//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "boost/tokenizer.hpp"

#include "IECore/Exception.h"
#include "IECore/NullObject.h"

#include "Gaffer/Context.h"

#include "GafferScene/ScenePlug.h"

using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( ScenePlug );

const IECore::InternedString ScenePlug::scenePathContextName( "scene:path" );

ScenePlug::ScenePlug( const std::string &name, Direction direction, unsigned flags )
	:	CompoundPlug( name, direction, flags )
{
	// we don't want the children to be serialised in any way - we always create
	// them ourselves in this constructor so they aren't Dynamic, and we don't ever
	// want to store their values because they are meaningless without an input
	// connection, so they aren't Serialisable either.
	unsigned childFlags = flags & ~(Dynamic | Serialisable);

	addChild(
		new AtomicBox3fPlug(
			"bound",
			direction,
			Imath::Box3f(),
			childFlags
		)
	);
	
	addChild(
		new M44fPlug(
			"transform",
			direction,
			Imath::M44f(),
			childFlags
		)
	);
	
	addChild(
		new CompoundObjectPlug(
			"attributes",
			direction,
			new IECore::CompoundObject(),
			childFlags
		)
	);
	
	addChild(
		new ObjectPlug(
			"object",
			direction,
			new IECore::NullObject(),
			childFlags
		)
	);
	
	addChild(
		new InternedStringVectorDataPlug(
			"childNames",
			direction,
			new IECore::InternedStringVectorData(),
			childFlags
		)
	);
	
	addChild(
		new CompoundObjectPlug(
			"globals",	
			direction,
			new IECore::CompoundObject(),
			childFlags
		)
	);
	
}

ScenePlug::~ScenePlug()
{
}

bool ScenePlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	return children().size() != 6;
}

Gaffer::PlugPtr ScenePlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new ScenePlug( name, direction, getFlags() );
}

bool ScenePlug::acceptsInput( const Gaffer::Plug *input ) const
{
	if( !CompoundPlug::acceptsInput( input ) )
	{
		return false;
	}
	if( input )
	{
		return input->isInstanceOf( staticTypeId() );
	}
	return true;
}

Gaffer::AtomicBox3fPlug *ScenePlug::boundPlug()
{
	return getChild<AtomicBox3fPlug>( 0 );
}

const Gaffer::AtomicBox3fPlug *ScenePlug::boundPlug() const
{
	return getChild<AtomicBox3fPlug>( 0 );
}

Gaffer::M44fPlug *ScenePlug::transformPlug()
{
	return getChild<M44fPlug>( 1 );
}

const Gaffer::M44fPlug *ScenePlug::transformPlug() const
{
	return getChild<M44fPlug>( 1 );
}

Gaffer::CompoundObjectPlug *ScenePlug::attributesPlug()
{
	return getChild<CompoundObjectPlug>( 2 );
}

const Gaffer::CompoundObjectPlug *ScenePlug::attributesPlug() const
{
	return getChild<CompoundObjectPlug>( 2 );
}

Gaffer::ObjectPlug *ScenePlug::objectPlug()
{
	return getChild<ObjectPlug>( 3 );
}

const Gaffer::ObjectPlug *ScenePlug::objectPlug() const
{
	return getChild<ObjectPlug>( 3 );
}

Gaffer::InternedStringVectorDataPlug *ScenePlug::childNamesPlug()
{
	return getChild<InternedStringVectorDataPlug>( 4 );
}

const Gaffer::InternedStringVectorDataPlug *ScenePlug::childNamesPlug() const
{
	return getChild<InternedStringVectorDataPlug>( 4 );
}

Gaffer::CompoundObjectPlug *ScenePlug::globalsPlug()
{
	return getChild<CompoundObjectPlug>( 5 );
}

const Gaffer::CompoundObjectPlug *ScenePlug::globalsPlug() const
{
	return getChild<CompoundObjectPlug>( 5 );
}

Imath::Box3f ScenePlug::bound( const ScenePath &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );	
	return boundPlug()->getValue();
}

Imath::M44f ScenePlug::transform( const ScenePath &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );
	return transformPlug()->getValue();
}

Imath::M44f ScenePlug::fullTransform( const ScenePath &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	Context::Scope scopedContext( tmpContext );
	
	Imath::M44f result;
	ScenePath path( scenePath );
	while( path.size() )
	{
		tmpContext->set( scenePathContextName, path );
		result = result * transformPlug()->getValue();
		path.pop_back();
	}
	
	return result;
}

IECore::ConstCompoundObjectPtr ScenePlug::attributes( const ScenePath &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );
	return attributesPlug()->getValue();
}

IECore::CompoundObjectPtr ScenePlug::fullAttributes( const ScenePath &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	Context::Scope scopedContext( tmpContext );

	IECore::CompoundObjectPtr result = new IECore::CompoundObject;
	IECore::CompoundObject::ObjectMap &resultMembers = result->members();
	ScenePath path( scenePath );
	while( path.size() )
	{
		tmpContext->set( scenePathContextName, path );
		IECore::ConstCompoundObjectPtr a = attributesPlug()->getValue();
		const IECore::CompoundObject::ObjectMap &aMembers = a->members();
		for( IECore::CompoundObject::ObjectMap::const_iterator it = aMembers.begin(), eIt = aMembers.end(); it != eIt; it++ )
		{
			if( resultMembers.find( it->first ) == resultMembers.end() )
			{
				resultMembers.insert( *it );
			}
		}		
		path.pop_back();
	}
	
	return result;
}

IECore::ConstObjectPtr ScenePlug::object( const ScenePath &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );
	return objectPlug()->getValue();
}

IECore::ConstInternedStringVectorDataPtr ScenePlug::childNames( const ScenePath &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );
	return childNamesPlug()->getValue();
}

IECore::MurmurHash ScenePlug::boundHash( const ScenePath &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );
	return boundPlug()->hash();
}

IECore::MurmurHash ScenePlug::transformHash( const ScenePath &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );
	return transformPlug()->hash();
}

IECore::MurmurHash ScenePlug::fullTransformHash( const ScenePath &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	Context::Scope scopedContext( tmpContext );
	
	IECore::MurmurHash result;
	ScenePath path( scenePath );
	while( path.size() )
	{
		tmpContext->set( scenePathContextName, path );
		transformPlug()->hash( result );
		path.pop_back();
	}
	
	return result;
}

IECore::MurmurHash ScenePlug::attributesHash( const ScenePath &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );
	return attributesPlug()->hash();
}

IECore::MurmurHash ScenePlug::fullAttributesHash( const ScenePath &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	Context::Scope scopedContext( tmpContext );
	
	IECore::MurmurHash result;
	ScenePath path( scenePath );
	while( path.size() )
	{
		tmpContext->set( scenePathContextName, path );
		attributesPlug()->hash( result );
		path.pop_back();
	}
	
	return result;
}

IECore::MurmurHash ScenePlug::objectHash( const ScenePath &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );
	return objectPlug()->hash();

}

IECore::MurmurHash ScenePlug::childNamesHash( const ScenePath &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );
	return childNamesPlug()->hash();
}

void ScenePlug::stringToPath( const std::string &s, ScenePlug::ScenePath &path )
{
	typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;
	Tokenizer tokenizer( s, boost::char_separator<char>( "/" ) );	
	for( Tokenizer::const_iterator it = tokenizer.begin(), eIt = tokenizer.end(); it != eIt; it++ )
	{
		path.push_back( *it );
	}
}

std::ostream &operator << ( std::ostream &o, const ScenePlug::ScenePath &path )
{
	for( ScenePlug::ScenePath::const_iterator it = path.begin(); it != path.end(); ++it )
	{
		o << "/" << *it;
	}
	return o;
}
