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
#include "boost/python/suite/indexing/container_utils.hpp"

#include "boost/tokenizer.hpp"
#include "boost/format.hpp"

#include "IECore/MessageHandler.h"

#include "IECorePython/ScopedGILLock.h"

#include "Gaffer/Context.h"
#include "Gaffer/Plug.h"

#include "GafferBindings/Serialisation.h"
#include "GafferBindings/GraphComponentBinding.h"
#include "GafferBindings/MetadataBinding.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferBindings;
using namespace boost::python;

//////////////////////////////////////////////////////////////////////////
// Serialisation
//////////////////////////////////////////////////////////////////////////

Serialisation::Serialisation( const Gaffer::GraphComponent *parent, const std::string &parentName, const Gaffer::Set *filter )
	:	m_parent( parent ), m_parentName( parentName ), m_filter( filter )
{
	IECorePython::ScopedGILLock gilLock;
	walk( parent, parentName, acquireSerialiser( parent ) );

	if( Context::current()->get<bool>( "serialiser:includeParentMetadata", false ) )
	{
		if( const Node *node = runTimeCast<const Node>( parent ) )
		{
			metadataModuleDependencies( node, m_modules );
			m_postScript += metadataSerialisation( node, parentName );
		}
		else if( const Plug *plug = runTimeCast<const Plug>( parent ) )
		{
			metadataModuleDependencies( plug, m_modules );
			m_postScript += metadataSerialisation( plug, parentName );
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
		Context::current()->get<bool>( "serialiser:includeVersionMetadata", false ) &&
		runTimeCast<const Node>( m_parent )
	)
	{
		boost::format formatter( "Gaffer.Metadata.registerNodeValue( %s, \"%s\", %d, persistent=False )\n" );

		result += "\n";
		result += boost::str( formatter % m_parentName % "serialiser:milestoneVersion" % GAFFER_MILESTONE_VERSION );
		result += boost::str( formatter % m_parentName % "serialiser:majorVersion" % GAFFER_MAJOR_VERSION );
		result += boost::str( formatter % m_parentName % "serialiser:minorVersion" % GAFFER_MINOR_VERSION );
		result += boost::str( formatter % m_parentName % "serialiser:patchVersion" % GAFFER_PATCH_VERSION );
	}

	result += "\n__children = {}\n\n";

	result += m_hierarchyScript;

	result += m_connectionScript;

	result += m_postScript;

	result += "\n\ndel __children\n\n";

	return result;
}

std::string Serialisation::modulePath( const IECore::RefCounted *object )
{
	boost::python::object o( RefCountedPtr( const_cast<RefCounted *>( object ) ) ); // we can only push non-const objects to python so we need the cast
	return modulePath( o );
}

std::string Serialisation::modulePath( boost::python::object &o )
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

	typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;
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

std::string Serialisation::classPath( const IECore::RefCounted *object )
{
	boost::python::object o( RefCountedPtr( const_cast<RefCounted *>( object ) ) ); // we can only push non-const objects to python so we need the cast
	return classPath( o );
}

std::string Serialisation::classPath( boost::python::object &object )
{
	std::string result = modulePath( object );
	if( result.size() )
	{
		result += ".";
	}

	if( PyType_Check( object.ptr() ) )
	{
		result += extract<std::string>( object.attr( "__name__" ) );
	}
	else
	{
		result += extract<std::string>( object.attr( "__class__" ).attr( "__name__" ) );
	}
	return result;
}

void Serialisation::walk( const Gaffer::GraphComponent *parent, const std::string &parentIdentifier, const Serialiser *parentSerialiser )
{
	for( GraphComponent::ChildIterator it = parent->children().begin(), eIt = parent->children().end(); it != eIt; it++ )
	{
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
		if( parent == m_parent && childConstructor.size() )
		{
			childIdentifier = "__children[\"" + child->getName().string() + "\"]";
		}
		else
		{
			childIdentifier = parentIdentifier + "[\"" + child->getName().string() + "\"]";
		}

		if( childConstructor.size() )
		{
			if( parent == m_parent)
			{
				m_hierarchyScript += childIdentifier + " = " + childConstructor + "\n";
				m_hierarchyScript += parentIdentifier + ".addChild( " + childIdentifier + " )\n";
			}
			else
			{
				m_hierarchyScript += parentIdentifier + ".addChild( " + childConstructor + " )\n";
			}
		}

		m_hierarchyScript += childSerialiser->postConstructor( child, childIdentifier, *this );
		m_connectionScript += childSerialiser->postHierarchy( child, childIdentifier, *this );
		m_postScript += childSerialiser->postScript( child, childIdentifier, *this );

		walk( child, childIdentifier, childSerialiser );
	}
}

std::string Serialisation::identifier( const Gaffer::GraphComponent *graphComponent ) const
{
	std::string result;
	while( graphComponent )
	{
		const GraphComponent *parent = graphComponent->parent<GraphComponent>();
		if( parent == m_parent )
		{
			if( m_filter && !m_filter->contains( graphComponent ) )
			{
				return "";
			}
			const Serialiser *parentSerialiser = acquireSerialiser( parent );
			if( parentSerialiser->childNeedsConstruction( graphComponent, *this ) )
			{
				return "__children[\"" + graphComponent->getName().string() + "\"]" + result;
			}
			else
			{
				return m_parentName + "[\"" + graphComponent->getName().string() + "\"]" + result;
			}
		}
		result = "[\"" + graphComponent->getName().string() + "\"]" + result;
		graphComponent = parent;
	}

	return "";
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
	return NULL;
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

//////////////////////////////////////////////////////////////////////////
// Serialisation::Serialiser
//////////////////////////////////////////////////////////////////////////

void Serialisation::Serialiser::moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules, const Serialisation &serialisation ) const
{
	modules.insert( Serialisation::modulePath( graphComponent ) );
}

std::string Serialisation::Serialiser::constructor( const Gaffer::GraphComponent *graphComponent, const Serialisation &serialisation ) const
{
	object o( GraphComponentPtr( const_cast<GraphComponent *>( graphComponent ) ) );
	std::string r = extract<std::string>( o.attr( "__repr__" )() );
	return r;
}

std::string Serialisation::Serialiser::postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
{
	return "";
}

std::string Serialisation::Serialiser::postHierarchy( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
{
	return "";
}

std::string Serialisation::Serialiser::postScript( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
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

//////////////////////////////////////////////////////////////////////////
// Python binding
//////////////////////////////////////////////////////////////////////////

namespace
{

class SerialiserWrapper : public IECorePython::RefCountedWrapper<Serialisation::Serialiser>
{

	public :

		SerialiserWrapper( PyObject *self )
			:	IECorePython::RefCountedWrapper<Serialisation::Serialiser>( self )
		{
		}

		virtual void moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules, const Serialisation &serialisation ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "moduleDependencies" );
				if( f )
				{
					object mo = f( GraphComponentPtr( const_cast<GraphComponent *>( graphComponent ) ), serialisation );
					std::vector<std::string> mv;
					container_utils::extend_container( mv, mo );
					modules.insert( mv.begin(), mv.end() );
					return;
				}
			}
			Serialiser::moduleDependencies( graphComponent, modules, serialisation );
		}

		virtual std::string constructor( const Gaffer::GraphComponent *graphComponent, const Serialisation &serialisation ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "constructor" );
				if( f )
				{
					return boost::python::extract<std::string>(
						f( GraphComponentPtr( const_cast<GraphComponent *>( graphComponent ) ), serialisation )
					);
				}
			}
			return Serialiser::constructor( graphComponent, serialisation );
		}

		virtual std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "postConstructor" );
				if( f )
				{
					return boost::python::extract<std::string>(
						f( GraphComponentPtr( const_cast<GraphComponent *>( graphComponent ) ), identifier, serialisation )
					);
				}
			}
			return Serialiser::postConstructor( graphComponent, identifier, serialisation );
		}

		virtual std::string postHierarchy( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "postHierarchy" );
				if( f )
				{
					return boost::python::extract<std::string>(
						f( GraphComponentPtr( const_cast<GraphComponent *>( graphComponent ) ), identifier, serialisation )
					);
				}
			}
			return Serialiser::postHierarchy( graphComponent, identifier, serialisation );
		}

		virtual std::string postScript( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "postScript" );
				if( f )
				{
					return boost::python::extract<std::string>(
						f( GraphComponentPtr( const_cast<GraphComponent *>( graphComponent ) ), identifier, serialisation )
					);
				}
			}
			return Serialiser::postScript( graphComponent, identifier, serialisation );
		}

		virtual bool childNeedsSerialisation( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "childNeedsSerialisation" );
				if( f )
				{
					return f( GraphComponentPtr( const_cast<GraphComponent *>( child ) ), serialisation );
				}
			}
			return Serialiser::childNeedsSerialisation( child, serialisation );
		}

		virtual bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "childNeedsConstruction" );
				if( f )
				{
					return f( GraphComponentPtr( const_cast<GraphComponent *>( child ) ), serialisation );
				}
			}
			return Serialiser::childNeedsConstruction( child, serialisation );
		}

};

GraphComponentPtr parent( const Serialisation &serialisation )
{
	return const_cast<GraphComponent *>( serialisation.parent() );
}

object moduleDependencies( Serialisation::Serialiser &serialiser, const Gaffer::GraphComponent *graphComponent, const Serialisation &serialisation )
{
	std::set<std::string> modules;
	serialiser.moduleDependencies( graphComponent, modules, serialisation );
	boost::python::list modulesList;
	for( std::set<std::string>::const_iterator it = modules.begin(); it != modules.end(); ++it )
	{
		modulesList.append( *it );
	}
	PyObject *modulesSet = PySet_New( modulesList.ptr() );
	return object( handle<>( modulesSet ) );
}

} // namespace

void GafferBindings::bindSerialisation()
{

	scope s = boost::python::class_<Serialisation>( "Serialisation", no_init )
		.def(
			init<const Gaffer::GraphComponent *, const std::string &, const Gaffer::Set *>
			(
				(
					arg( "parent" ),
					arg( "parentName" ) = "parent",
					arg( "filter" ) = object()
				)
			)
		)
		.def( "parent", &parent )
		.def( "identifier", &Serialisation::identifier )
		.def( "result", &Serialisation::result )
		.def( "modulePath", (std::string (*)( object & ))&Serialisation::modulePath )
		.staticmethod( "modulePath" )
		.def( "classPath", (std::string (*)( object & ))&Serialisation::classPath )
		.staticmethod( "classPath" )
		.def( "registerSerialiser", &Serialisation::registerSerialiser )
		.staticmethod( "registerSerialiser" )
		.def( "acquireSerialiser", &Serialisation::acquireSerialiser, return_value_policy<reference_existing_object>() )
		.staticmethod( "acquireSerialiser" )
	;

	IECorePython::RefCountedClass<Serialisation::Serialiser, IECore::RefCounted, SerialiserWrapper>( "Serialiser" )
		.def( init<>() )
		.def( "moduleDependencies", &moduleDependencies )
		.def( "constructor", &Serialisation::Serialiser::constructor )
		.def( "postConstructor", &Serialisation::Serialiser::postConstructor )
		.def( "postHierarchy", &Serialisation::Serialiser::postHierarchy )
		.def( "postScript", &Serialisation::Serialiser::postScript )
		.def( "childNeedsSerialisation", &Serialisation::Serialiser::postScript )
		.def( "childNeedsConstruction", &Serialisation::Serialiser::childNeedsConstruction )
	;

}
