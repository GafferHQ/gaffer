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

#include "boost/tokenizer.hpp"
#include "boost/format.hpp"

#include "IECore/MessageHandler.h"
#include "IECorePython/ScopedGILLock.h"

#include "GafferBindings/Serialisation.h"
#include "GafferBindings/GraphComponentBinding.h"

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
	
	const Serialiser *parentSerialiser = serialiser( parent );
	for( GraphComponent::ChildIterator it = parent->children().begin(), eIt = parent->children().end(); it != eIt; it++ )
	{
		const GraphComponent *child = it->get();
		if( m_filter && !m_filter->contains( child ) )
		{
			continue;
		}
		if( !parentSerialiser->childNeedsSerialisation( child ) )
		{
			continue;
		}
		
		std::string childIdentifier;
		if( parentSerialiser->childNeedsConstruction( child ) )
		{
			const Serialiser *childSerialiser = serialiser( child );
			childIdentifier = "__children[\"" + child->getName().string() + "\"]";
			m_hierarchyScript += childIdentifier + " = " + childSerialiser->constructor( child ) + "\n";
			m_hierarchyScript += parentName + ".addChild( " + childIdentifier + " )\n";
		}
		else
		{
			childIdentifier = parentName + "[\"" + child->getName().string() + "\"]";
		}
		walk( child, childIdentifier );
	}
}

std::string Serialisation::result() const
{
	std::string result;
	for( std::set<std::string>::const_iterator it=m_modules.begin(); it!=m_modules.end(); it++ )
	{
		result += "import " + *it + "\n";
	}
	
	result += "\n__children = {}\n\n";
	
	result += m_hierarchyScript;
	
	result += m_connectionScript;
	
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
	std::string className = extract<std::string>( o.attr( "__class__" ).attr( "__name__" ) );

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
		if( next==tokens.end() && *tIt == className )
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
	result += extract<std::string>( object.attr( "__class__" ).attr( "__name__" ) );
	return result;
}

void Serialisation::walk( const Gaffer::GraphComponent *parent, const std::string &parentIdentifier )
{
	const Serialiser *parentSerialiser = serialiser( parent );
	
	parentSerialiser->moduleDependencies( parent, m_modules );
	m_hierarchyScript += parentSerialiser->postConstructor( parent, parentIdentifier, *this );
	m_connectionScript += parentSerialiser->postHierarchy( parent, parentIdentifier, *this );

	for( GraphComponent::ChildIterator it = parent->children().begin(), eIt = parent->children().end(); it != eIt; it++ )
	{
		const GraphComponent *child = it->get();
		if( !parentSerialiser->childNeedsSerialisation( child ) )
		{
			continue;
		}
		if( parentSerialiser->childNeedsConstruction( child ) )
		{
			const Serialiser *childSerialiser = serialiser( child );
			m_hierarchyScript += parentIdentifier + ".addChild( " + childSerialiser->constructor( child ) + " )\n";
		}
		std::string childIdentifier = parentIdentifier + "[\"" + child->getName().string() + "\"]";
		walk( child, childIdentifier );
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
			const Serialiser *parentSerialiser = serialiser( parent );
			if( parentSerialiser->childNeedsConstruction( graphComponent ) )
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

Serialisation::SerialiserMap &Serialisation::serialiserMap()
{
	static SerialiserMap m;
	if( !m.size() )
	{
		m[GraphComponent::staticTypeId()] = new Serialiser();
	}
	return m;
}

const Serialisation::Serialiser *Serialisation::serialiser( const GraphComponent *graphComponent )
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
	
	assert( 0 );
	return 0;
}

//////////////////////////////////////////////////////////////////////////
// Serialisation::Serialiser
//////////////////////////////////////////////////////////////////////////
		
void Serialisation::Serialiser::moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules ) const
{
	modules.insert( Serialisation::modulePath( graphComponent ) );
}

std::string Serialisation::Serialiser::constructor( const Gaffer::GraphComponent *graphComponent ) const
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

bool Serialisation::Serialiser::childNeedsSerialisation( const Gaffer::GraphComponent *child ) const
{
	return true;
}

bool Serialisation::Serialiser::childNeedsConstruction( const Gaffer::GraphComponent *child ) const
{
	return false;
}
