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

#include "GafferScene/SceneProcessor.h"

#include "Gaffer/ArrayPlug.h"

using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( SceneProcessor );

size_t SceneProcessor::g_firstPlugIndex = 0;

SceneProcessor::SceneProcessor( const std::string &name )
	:	SceneNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "in", Gaffer::Plug::In ) );
}

SceneProcessor::SceneProcessor( const std::string &name, size_t minInputs, size_t maxInputs )
	:	SceneNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild(
		new ArrayPlug( "in", Gaffer::Plug::In, new ScenePlug( "in0" ), minInputs, maxInputs )
	);
}

SceneProcessor::~SceneProcessor()
{
}

ScenePlug *SceneProcessor::inPlug()
{
	GraphComponent *p = getChild( g_firstPlugIndex );
	if( ScenePlug *s = IECore::runTimeCast<ScenePlug>( p ) )
	{
		return s;
	}
	else
	{
		return static_cast<ArrayPlug *>( p )->getChild<ScenePlug>( 0 );
	}
}

const ScenePlug *SceneProcessor::inPlug() const
{
	const GraphComponent *p = getChild( g_firstPlugIndex );
	if( const ScenePlug *s = IECore::runTimeCast<const ScenePlug>( p ) )
	{
		return s;
	}
	else
	{
		return static_cast<const ArrayPlug *>( p )->getChild<ScenePlug>( 0 );
	}
}

Gaffer::ArrayPlug *SceneProcessor::inPlugs()
{
	return getChild<Gaffer::ArrayPlug>( g_firstPlugIndex );
}

const Gaffer::ArrayPlug *SceneProcessor::inPlugs() const
{
	return getChild<Gaffer::ArrayPlug>( g_firstPlugIndex );
}

Plug *SceneProcessor::correspondingInput( const Plug *output )
{
	if ( output == outPlug() )
	{
		return inPlug();
	}

	return SceneNode::correspondingInput( output );
}

const Plug *SceneProcessor::correspondingInput( const Plug *output ) const
{
	if ( output == outPlug() )
	{
		return inPlug();
	}

	return SceneNode::correspondingInput( output );
}

void SceneProcessor::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const ScenePlug *scenePlug = output->parent<ScenePlug>();
	if( scenePlug && !enabledPlug()->getValue() )
	{
		// if we're hashing the output scene, and we're disabled, we need to
		// pass through the hash from the inPlug().
		h = inPlug()->getChild<ValuePlug>( output->getName() )->hash();
	}
	else
	{
		// if not, we can let the base class take care of everything.
		SceneNode::hash( output, context, h );
	}
}

void SceneProcessor::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	const ScenePlug *scenePlug = output->parent<ScenePlug>();
	if( scenePlug && !enabledPlug()->getValue() )
	{
		// if we're computing the output scene, and we're disabled, we need to
		// pass through the scene from inPlug().
		output->setFrom( inPlug()->getChild<ValuePlug>( output->getName() ) );
	}
	else
	{
		// otherwise, we can let the base class take care of everything.
		SceneNode::compute( output, context );
	}
}
