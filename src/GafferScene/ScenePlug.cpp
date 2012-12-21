//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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
	
	addChild(
		new AtomicBox3fPlug(
			"bound",
			direction,
			Imath::Box3f(),
			flags
		)
	);
	
	addChild(
		new M44fPlug(
			"transform",
			direction,
			Imath::M44f(),
			flags
		)
	);
	
	addChild(
		new CompoundObjectPlug(
			"attributes",
			direction,
			new IECore::CompoundObject(),
			flags
		)
	);
	
	addChild(
		new ObjectPlug(
			"object",
			direction,
			new IECore::NullObject(),
			flags
		)
	);
	
	addChild(
		new StringVectorDataPlug(
			"childNames",
			direction,
			new IECore::StringVectorData(),
			flags
		)
	);
	
	addChild(
		new ObjectVectorPlug(
			"globals",	
			direction,
			new IECore::ObjectVector(),
			flags
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

Gaffer::StringVectorDataPlug *ScenePlug::childNamesPlug()
{
	return getChild<StringVectorDataPlug>( 4 );
}

const Gaffer::StringVectorDataPlug *ScenePlug::childNamesPlug() const
{
	return getChild<StringVectorDataPlug>( 4 );
}

Gaffer::ObjectVectorPlug *ScenePlug::globalsPlug()
{
	return getChild<ObjectVectorPlug>( 5 );
}

const Gaffer::ObjectVectorPlug *ScenePlug::globalsPlug() const
{
	return getChild<ObjectVectorPlug>( 5 );
}

Imath::Box3f ScenePlug::bound( const std::string &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current() );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );	
	return boundPlug()->getValue();
}

Imath::M44f ScenePlug::transform( const std::string &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current() );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );
	return transformPlug()->getValue();
}

Imath::M44f ScenePlug::fullTransform( const std::string &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current() );
	Context::Scope scopedContext( tmpContext );
	
	Imath::M44f result;
	size_t i = 0;
	do {
		i = scenePath.find( '/', i + 1 );
		tmpContext->set( scenePathContextName, scenePath.substr( 0, i ) );
		result = transformPlug()->getValue() * result;
	} while( i != std::string::npos );
	
	return result;
}

IECore::ConstCompoundObjectPtr ScenePlug::attributes( const std::string &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current() );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );
	return attributesPlug()->getValue();
}

IECore::ConstObjectPtr ScenePlug::object( const std::string &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current() );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );
	return objectPlug()->getValue();
}

IECore::ConstStringVectorDataPtr ScenePlug::childNames( const std::string &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current() );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );
	return childNamesPlug()->getValue();
}

IECore::MurmurHash ScenePlug::boundHash( const std::string &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current() );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );
	return boundPlug()->hash();
}

IECore::MurmurHash ScenePlug::transformHash( const std::string &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current() );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );
	return transformPlug()->hash();
}

IECore::MurmurHash ScenePlug::attributesHash( const std::string &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current() );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );
	return attributesPlug()->hash();
}

IECore::MurmurHash ScenePlug::objectHash( const std::string &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current() );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );
	return objectPlug()->hash();

}

IECore::MurmurHash ScenePlug::childNamesHash( const std::string &scenePath ) const
{
	ContextPtr tmpContext = new Context( *Context::current() );
	tmpContext->set( scenePathContextName, scenePath );
	Context::Scope scopedContext( tmpContext );
	return childNamesPlug()->hash();
}
