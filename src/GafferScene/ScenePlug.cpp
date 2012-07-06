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

#include "Gaffer/Context.h"

#include "GafferScene/ScenePlug.h"

using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( ScenePlug );

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
		new ObjectPlug(
			"object",
			direction,
			0,
			flags
		)
	);
	
	addChild(
		new StringVectorDataPlug(
			"childNames",
			direction,
			0,
			flags
		)
	);
	
	addChild(
		new ObjectVectorPlug(
			"globals",	
			direction,
			0,
			flags
		)
	);
	
}

ScenePlug::~ScenePlug()
{
}

bool ScenePlug::acceptsChild( ConstGraphComponentPtr potentialChild ) const
{
	return children().size() != 5;
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
	return getChild<AtomicBox3fPlug>( "bound" );
}

const Gaffer::AtomicBox3fPlug *ScenePlug::boundPlug() const
{
	return getChild<AtomicBox3fPlug>( "bound" );
}

Gaffer::M44fPlug *ScenePlug::transformPlug()
{
	return getChild<M44fPlug>( "transform" );
}

const Gaffer::M44fPlug *ScenePlug::transformPlug() const
{
	return getChild<M44fPlug>( "transform" );
}

Gaffer::ObjectPlug *ScenePlug::objectPlug()
{
	return getChild<ObjectPlug>( "object" );
}

const Gaffer::ObjectPlug *ScenePlug::objectPlug() const
{
	return getChild<ObjectPlug>( "object" );
}

Gaffer::StringVectorDataPlug *ScenePlug::childNamesPlug()
{
	return getChild<StringVectorDataPlug>( "childNames" );
}

const Gaffer::StringVectorDataPlug *ScenePlug::childNamesPlug() const
{
	return getChild<StringVectorDataPlug>( "childNames" );
}

Gaffer::ObjectVectorPlug *ScenePlug::globalsPlug()
{
	return getChild<ObjectVectorPlug>( "globals" );
}

const Gaffer::ObjectVectorPlug *ScenePlug::globalsPlug() const
{
	return getChild<ObjectVectorPlug>( "globals" );
}

Imath::Box3f ScenePlug::bound( const std::string &scenePath ) const
{
	if( direction()==In && !getInput<Plug>() )
	{
		throw IECore::Exception( "ScenePlug::bound called on unconnected input plug" );
	}
	ContextPtr tmpContext = new Context( *Context::current() );
	tmpContext->set( "scene:path", scenePath );
	Context::Scope scopedContext( tmpContext );
	return boundPlug()->getValue();
}

Imath::M44f ScenePlug::transform( const std::string &scenePath ) const
{
	if( direction()==In && !getInput<Plug>() )
	{
		throw IECore::Exception( "ScenePlug::transform called on unconnected input plug" );
	}
	ContextPtr tmpContext = new Context( *Context::current() );
	tmpContext->set( "scene:path", scenePath );
	Context::Scope scopedContext( tmpContext );
	return transformPlug()->getValue();
}

IECore::ConstObjectPtr ScenePlug::object( const std::string &scenePath ) const
{
	if( direction()==In && !getInput<Plug>() )
	{
		throw IECore::Exception( "ScenePlug::object called on unconnected input plug" );
	}
	ContextPtr tmpContext = new Context( *Context::current() );
	tmpContext->set( "scene:path", scenePath );
	Context::Scope scopedContext( tmpContext );
	return objectPlug()->getValue();
}

IECore::ConstStringVectorDataPtr ScenePlug::childNames( const std::string &scenePath ) const
{
	if( direction()==In && !getInput<Plug>() )
	{
		throw IECore::Exception( "ScenePlug::childNames called on unconnected input plug" );
	}
	ContextPtr tmpContext = new Context( *Context::current() );
	tmpContext->set( "scene:path", scenePath );
	Context::Scope scopedContext( tmpContext );
	return childNamesPlug()->getValue();
}
