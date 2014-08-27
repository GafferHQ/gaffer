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

#include "Gaffer/Context.h"

#include "GafferScene/Filter.h"

using namespace GafferScene;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( Filter );

const IECore::InternedString Filter::g_inputSceneContextName( "scene:filter:inputScene" );
size_t Filter::g_firstPlugIndex = 0;

Filter::Filter( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "match", Gaffer::Plug::Out, NoMatch, NoMatch, EveryMatch ) );
}

Filter::~Filter()
{
}

Gaffer::IntPlug *Filter::matchPlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *Filter::matchPlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex );
}

bool Filter::sceneAffectsMatch( const ScenePlug *scene, const Gaffer::ValuePlug *child ) const
{
	return false;
}

void Filter::setInputScene( Gaffer::Context *context, const ScenePlug *scenePlug )
{
	context->set( g_inputSceneContextName, (uint64_t)scenePlug );
}

const ScenePlug *Filter::getInputScene( const Gaffer::Context *context )
{
	return (const ScenePlug *)( context->get<uint64_t>( g_inputSceneContextName, 0 ) );
}

void Filter::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );
	if( output == matchPlug() )
	{
		hashMatch( getInputScene( context ), context, h );
	}
}

void Filter::compute( ValuePlug *output, const Context *context ) const
{
	if( output == matchPlug() )
	{
		static_cast<IntPlug *>( output )->setValue( computeMatch( getInputScene( context ), context ) );
	}
}
