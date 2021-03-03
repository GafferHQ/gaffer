//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

#include "boost/python.hpp"

#include "GafferBindings/Serialisation.h"

#include "GafferBindings/GraphComponentBinding.h"
#include "GafferBindings/MetadataBinding.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/Plug.h"
#include "Gaffer/Spreadsheet.h"

#include "IECorePython/ScopedGILLock.h"

#include "IECore/MemoryIndexedIO.h"
#include "IECore/MessageHandler.h"

#include "boost/algorithm/string.hpp"
#include "boost/archive/iterators/base64_from_binary.hpp"
#include "boost/archive/iterators/binary_from_base64.hpp"
#include "boost/archive/iterators/transform_width.hpp"
#include "boost/format.hpp"
#include "boost/python/suite/indexing/container_utils.hpp"
#include "boost/tokenizer.hpp"

#include <unordered_map>

using namespace IECore;
using namespace Gaffer;
using namespace GafferBindings;
using namespace boost::python;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

// Where a parent has dynamically changing numbers of children,
// and no meaning is attached to their names, we want to
// access the children by index rather than name. This is faster
// and more readable, and opens the possibility of omitting the
// overhead of the names entirely one day.
/// \todo Consider an official way for GraphComponents to opt in
/// to this behaviour.
bool keyedByIndex( const GraphComponent *parent )
{
	return
		runTimeCast<const Spreadsheet::RowsPlug>( parent ) ||
		runTimeCast<const ArrayPlug>( parent )
	;
}

std::string modulePathInternal( const boost::python::object &o )
{
	if( !PyObject_HasAttrString( o.ptr(), "__module__" ) )
	{
		return "";
	}
	std::string modulePath = extract<std::string>( o.attr( "__module__" ) );
	std::string objectName;
	if( PyType_Check( o.ptr() ) )
	{
		objectName = extract<std::string>( o.attr( "__name__" ) );
	}
	else
	{
		objectName = extract<std::string>( o.attr( "__class__" ).attr( "__name__" ) );
	}

	using Tokenizer = boost::tokenizer<boost::char_separator<char> >;
	std::string sanitisedModulePath;
	Tokenizer tokens( modulePath, boost::char_separator<char>( "." ) );

	for( Tokenizer::iterator tIt=tokens.begin(); tIt!=tokens.end(); tIt++ )
	{
		if( tIt->compare( 0, 1, "_" )==0 )
		{
			// assume that module path components starting with _ are bogus, and are used only to bring
			// binary components into a namespace.
			continue;
		}
		Tokenizer::iterator next = tIt; next++;
		if( next==tokens.end() && *tIt == objectName )
		{
			// if the last module name is the same as the class name then assume this is just the file the
			// class has been implemented in.
			continue;
		}
		if( sanitisedModulePath.size() )
		{
			sanitisedModulePath += ".";
		}
		sanitisedModulePath += *tIt;
	}

	return sanitisedModulePath;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Serialisation
//////////////////////////////////////////////////////////////////////////

Serialisation::Serialisation( const Gaffer::GraphComponent *parent, const std::string &parentName, const Gaffer::Set *filter )
	:	m_parent( parent ), m_parentName( parentName ), m_filter( filter ),
		m_protectParentNamespace( Context::current()->get<bool>( "serialiser:protectParentNamespace", true ) )
{
	IECorePython::ScopedGILLock gilLock;
	walk( parent, parentName, acquireSerialiser( parent ), Context::current()->canceller() );

	if( Context::current()->get<bool>( "serialiser:includeParentMetadata", false ) )
	{
		if( const Node *node = runTimeCast<const Node>( parent ) )
		{
			m_postScript += metadataSerialisation( node, parentName, *this );
		}
		else if( const Plug *plug = runTimeCast<const Plug>( parent ) )
		{
			m_postScript += metadataSerialisation( plug, parentName, *this );
		}
	}
}

const Gaffer::GraphComponent *Serialisation::parent() const
{
	return m_parent;
}

std::string Serialisation::result() const
{
	std::string result;
	for( std::set<std::string>::const_iterator it=m_modules.begin(); it!=m_modules.end(); it++ )
	{
		result += "import " + *it + "\n";
	}

	if(
		runTimeCast<const Node>( m_parent ) &&
		Context::current()->get<bool>( "serialiser:includeVersionMetadata", true )
	)
	{
		boost::format formatter( "Gaffer.Metadata.registerValue( %s, \"%s\", %d, persistent=False )\n" );

		result += "\n";
		result += boost::str( formatter % m_parentName % "serialiser:milestoneVersion" % GAFFER_MILESTONE_VERSION );
		result += boost::str( formatter % m_parentName % "serialiser:majorVersion" % GAFFER_MAJOR_VERSION );
		result += boost::str( formatter % m_parentName % "serialiser:minorVersion" % GAFFER_MINOR_VERSION );
		result += boost::str( formatter % m_parentName % "serialiser:patchVersion" % GAFFER_PATCH_VERSION );
	}

	if( m_protectParentNamespace )
	{
		result += "\n__children = {}\n\n";
	}

	result += m_hierarchyScript;

	result += m_connectionScript;

	result += m_postScript;

	if( m_protectParentNamespace )
	{
		result += "\n\ndel __children\n\n";
	}

	return result;
}

std::string Serialisation::modulePath( const IECore::RefCounted *object )
{
	boost::python::object o( RefCountedPtr( const_cast<RefCounted *>( object ) ) ); // we can only push non-const objects to python so we need the cast
	return modulePath( o );
}

std::string Serialisation::modulePath( const boost::python::object &o )
{
	// Querying the module path is expensive and done frequently, so we cache
	// results. The cache is not thread-safe, but since we are dealing with
	// python objects, we know this thread must have the GIL, and therefore no
	// other thread can access the cache concurrently.
	static std::unordered_map<PyTypeObject *, std::string> g_cache;
	auto inserted = g_cache.insert( { o.ptr()->ob_type, std::string() } );
	if( inserted.second )
	{
		Py_INCREF( o.ptr()->ob_type );
		inserted.first->second = modulePathInternal( o );
	}
	return inserted.first->second;
}

std::string Serialisation::classPath( const IECore::RefCounted *object )
{
	boost::python::object o( RefCountedPtr( const_cast<RefCounted *>( object ) ) ); // we can only push non-const objects to python so we need the cast
	return classPath( o );
}

std::string Serialisation::classPath( const boost::python::object &object )
{
	std::string result = modulePath( object );
	if( result.size() )
	{
		result += ".";
	}

	boost::python::object cls;
	if( PyType_Check( object.ptr() ) )
	{
		cls = object;
	}
	else
	{
		cls = object.attr( "__class__" );
	}

	if( PyObject_HasAttrString( cls.ptr(), "__qualname__" ) )
	{
		// In Python 3, __qualname__ is automatically generated to give us
		// a qualified name for a nested class - see https://www.python.org/dev/peps/pep-3155.
		// In Python 2, it may be provided manually by bindings as necessary.
		std::string qualName = extract<std::string>( cls.attr( "__qualname__" ) );
		// The automatically generated name may contain a prefix made redundant
		// by our `from .Foo import Foo` convention for building modules. Strip it.
		const size_t dotPos = qualName.find( '.' );
		if( dotPos != std::string::npos )
		{
			if( boost::ends_with( result, "." + qualName.substr( 0, dotPos ) + "." ) )
			{
				qualName.erase( 0, dotPos + 1 );
			}
		}
		result += qualName;
	}
	else
	{
		result += extract<std::string>( cls.attr( "__name__" ) );
	}

	return result;
}

void Serialisation::walk( const Gaffer::GraphComponent *parent, const std::string &parentIdentifier, const Serialiser *parentSerialiser, const IECore::Canceller *canceller )
{
	for( GraphComponent::ChildIterator it = parent->children().begin(), eIt = parent->children().end(); it != eIt; it++ )
	{
		IECore::Canceller::check( canceller );

		const GraphComponent *child = it->get();
		if( parent == m_parent && m_filter && !m_filter->contains( child ) )
		{
			continue;
		}
		if( !parentSerialiser->childNeedsSerialisation( child, *this ) )
		{
			continue;
		}

		const Serialiser *childSerialiser = acquireSerialiser( child );
		childSerialiser->moduleDependencies( child, m_modules, *this );

		std::string childConstructor;
		if( parentSerialiser->childNeedsConstruction( child, *this ) )
		{
			childConstructor = childSerialiser->constructor( child, *this );
		}

		std::string childIdentifier;
		if( parent == m_parent && childConstructor.size() && m_protectParentNamespace )
		{
			childIdentifier = this->childIdentifier( "__children", it );
		}
		else
		{
			childIdentifier = this->childIdentifier( parentIdentifier, it );
		}

		if( childConstructor.size() )
		{
			if( parent == m_parent )
			{
				if( m_protectParentNamespace )
				{
					m_hierarchyScript += childIdentifier + " = " + childConstructor + "\n";
					m_hierarchyScript += parentIdentifier + ".addChild( " + childIdentifier + " )\n";
				}
				else
				{
					m_hierarchyScript += childIdentifier + " = " + childConstructor + "\n";
				}
			}
			else
			{
				m_hierarchyScript += parentIdentifier + ".addChild( " + childConstructor + " )\n";
			}
		}

		m_hierarchyScript += childSerialiser->postConstructor( child, childIdentifier, *this );
		m_connectionScript += childSerialiser->postHierarchy( child, childIdentifier, *this );
		m_postScript += childSerialiser->postScript( child, childIdentifier, *this );

		walk( child, childIdentifier, childSerialiser, canceller );
	}
}

std::string Serialisation::identifier( const Gaffer::GraphComponent *graphComponent ) const
{
	if( !graphComponent )
	{
		return "";
	}

	std::string parentIdentifier;
	const GraphComponent *parent = graphComponent->parent();
	if( parent == m_parent )
	{
		if( m_filter && !m_filter->contains( graphComponent ) )
		{
			return "";
		}
		const Serialiser *parentSerialiser = acquireSerialiser( parent );
		if( m_protectParentNamespace && parentSerialiser->childNeedsConstruction( graphComponent, *this ) )
		{
			parentIdentifier = "__children";
		}
		else
		{
			parentIdentifier = m_parentName;
		}
	}
	else
	{
		parentIdentifier = identifier( parent );
	}

	return childIdentifier( parentIdentifier, graphComponent );
}

std::string Serialisation::childIdentifier( const std::string &parentIdentifier, const Gaffer::GraphComponent *child ) const
{
	if( parentIdentifier.empty() )
	{
		return "";
	}

	const GraphComponent *parent = child->parent();
	std::string result = parentIdentifier;
	if( keyedByIndex( parent ) )
	{
		result += "[";
		result += boost::lexical_cast<std::string>(
			std::find( parent->children().begin(), parent->children().end(), child ) - parent->children().begin()
		);
		result += "]";
	}
	else
	{
		result += "[\"";
		result += child->getName().string();
		result += "\"]";
	}
	return result;
}

std::string Serialisation::childIdentifier( const std::string &parentIdentifier, Gaffer::GraphComponent::ChildIterator child ) const
{
	if( parentIdentifier.empty() )
	{
		return "";
	}

	const GraphComponent *parent = (*child)->parent();
	std::string result = parentIdentifier;
	if( keyedByIndex( parent ) )
	{
		result += "[";
		result += boost::lexical_cast<std::string>( child - parent->children().begin() );
		result += "]";
	}
	else
	{
		result += "[\"";
		result += (*child)->getName().string();
		result += "\"]";
	}
	return result;
}

void Serialisation::addModule( const std::string &moduleName )
{
	m_modules.insert( moduleName );
}

void Serialisation::registerSerialiser( IECore::TypeId targetType, SerialiserPtr serialiser )
{
	serialiserMap()[targetType] = serialiser;
}

const Serialisation::Serialiser *Serialisation::acquireSerialiser( const GraphComponent *graphComponent )
{
	const SerialiserMap &m = serialiserMap();
	IECore::TypeId t = graphComponent->typeId();
	while( t != IECore::InvalidTypeId )
	{
		SerialiserMap::const_iterator it = m.find( t );
		if( it != m.end() )
		{
			return it->second.get();
		}
		t = IECore::RunTimeTyped::baseTypeId( t );
	}

	assert( false );
	return nullptr;
}

Serialisation::SerialiserMap &Serialisation::serialiserMap()
{
	static SerialiserMap m;
	if( !m.size() )
	{
		m[GraphComponent::staticTypeId()] = new Serialiser();
	}
	return m;
}

std::string Serialisation::objectToBase64( const IECore::Object *object )
{
	// Serialise the object to a buffer in memory.

	IECore::MemoryIndexedIOPtr io = new IECore::MemoryIndexedIO( nullptr, {}, IECore::IndexedIO::Write );
	object->save( io, "o" );
	IECore::CharVectorDataPtr buffer = io->buffer();

	// Base64 encode that buffer. `boost::beast` has a nice simple version of
	// this that takes care of all the padding, but it is in a private namespace.
	// So we use the less useable version in `boost::archive`.

	// Pad buffer to multiple of 3, as required by `transform_width`.
	const int remainder = buffer->readable().size() % 3;
	const int padding = remainder ? 3 - remainder : 0;
	buffer->writable().resize( buffer->readable().size() + padding, 0 );

	// Encode to base64.
	using namespace boost::archive::iterators;
	using BufferIterator = std::vector<char>::const_iterator;
	using Base64Iterator = base64_from_binary<transform_width<BufferIterator, 6, 8>>;
	std::string result( Base64Iterator( buffer->readable().begin() ), Base64Iterator( buffer->readable().end() ) );

	// Replace the output padding with '=', so we can discard it
	// after decoding.
	std::fill( result.end() - padding, result.end(), '=' );

	return result;
}

IECore::ObjectPtr Serialisation::objectFromBase64( const std::string &base64 )
{
	// Decode to buffer

	IECore::CharVectorDataPtr buffer = new CharVectorData;
	using namespace boost::archive::iterators;
	using Base64Iterator = transform_width<binary_from_base64<std::string::const_iterator>, 8, 6>;
	buffer->writable().assign( Base64Iterator( base64.begin() ), Base64Iterator( base64.end() ) );

	// Remove padding

	if( base64.size() )
	{
		auto it = base64.rbegin();
		while( *it++ == '=' )
		{
			buffer->writable().pop_back();
		}
	}

	// Deserialise object from buffer.

	MemoryIndexedIOPtr io = new MemoryIndexedIO( buffer, {}, IECore::IndexedIO::Read );
	return Object::load( io, "o" );
}

//////////////////////////////////////////////////////////////////////////
// Serialisation::Serialiser
//////////////////////////////////////////////////////////////////////////

void Serialisation::Serialiser::moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules, const Serialisation &serialisation ) const
{
	const std::string module = Serialisation::modulePath( graphComponent );
	if( !module.empty() )
	{
		modules.insert( module );
	}
}

std::string Serialisation::Serialiser::constructor( const Gaffer::GraphComponent *graphComponent, Serialisation &serialisation ) const
{
	object o( GraphComponentPtr( const_cast<GraphComponent *>( graphComponent ) ) );
	std::string r = extract<std::string>( o.attr( "__repr__" )() );
	return r;
}

std::string Serialisation::Serialiser::postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const
{
	return "";
}

std::string Serialisation::Serialiser::postHierarchy( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const
{
	return "";
}

std::string Serialisation::Serialiser::postScript( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const
{
	return "";
}

bool Serialisation::Serialiser::childNeedsSerialisation( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const
{
	return true;
}

bool Serialisation::Serialiser::childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const
{
	return false;
}
