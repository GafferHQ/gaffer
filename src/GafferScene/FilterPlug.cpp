//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/FilterPlug.h"

#include "GafferScene/Filter.h"
#include "GafferScene/ScenePlug.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/ContextAlgo.h"
#include "Gaffer/Dot.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/SubGraph.h"
#include "Gaffer/Switch.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_PLUG_DEFINE_TYPE( FilterPlug );

const IECore::InternedString FilterPlug::inputSceneContextName( "scene:filter:inputScene" );

static ContextAlgo::GlobalScope::Registration g_globalScopeRegistration(
	ScenePlug::staticTypeId(),
	{ FilterPlug::inputSceneContextName }
);

FilterPlug::FilterPlug( const std::string &name, Direction direction, unsigned flags )
	:	IntPlug( name, direction, IECore::PathMatcher::NoMatch, IECore::PathMatcher::NoMatch, IECore::PathMatcher::EveryMatch, flags )
{
}

FilterPlug::FilterPlug( const std::string &name, Direction direction, int defaultValue, int minValue, int maxValue, unsigned flags )
	:	IntPlug( name, direction, defaultValue, minValue, maxValue, flags )
{
}

FilterPlug::~FilterPlug()
{
}

bool FilterPlug::acceptsInput( const Gaffer::Plug *input ) const
{
	if( !IntPlug::acceptsInput( input ) )
	{
		return false;
	}

	if( !input )
	{
		return true;
	}

	if( input->isInstanceOf( staticTypeId() ) )
	{
		return true;
	}

	// Really we want to return false here, but we must provide backwards
	// compatibility for a time when FilterPlug didn't exist and IntPlugs
	// were used instead. Those old plugs may have been promoted onto Boxes
	// routed via Dots, or used within ArrayPlugs. In each case, dynamic
	// IntPlugs will have been created and serialised into the script, so
	// we must accept them.
	const ScriptNode *script = ancestor<ScriptNode>();
	if( !script || !script->isExecuting() )
	{
		return false;
	}

	if( runTimeCast<const IntPlug>( input ) )
	{
		const Plug *p = input->source();
		const Node *n = p->node();
		if( runTimeCast<const FilterPlug>( p ) || runTimeCast<const SubGraph>( n ) || runTimeCast<const Dot>( n ) )
		{
			return true;
		}
		if( const ArrayPlug *arrayPlug = input->parent<ArrayPlug>() )
		{
			if( arrayPlug && arrayPlug->getChild<FilterPlug>( 0 ) )
			{
				return true;
			}
		}
	}

	return false;
}

Gaffer::PlugPtr FilterPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new FilterPlug( name, direction, defaultValue(), minValue(), maxValue(), getFlags() );
}

void FilterPlug::sceneAffects( const Gaffer::Plug *scenePlugChild, Gaffer::DependencyNode::AffectedPlugsContainer &outputs ) const
{
	const Plug *source = this->source();
	if( source == this )
	{
		// No input
		return;
	}

	const Node *sourceNode = source->node();
	if( const Filter *filter = runTimeCast<const Filter>( sourceNode ) )
	{
		filter->affects( scenePlugChild, outputs );
	}
	else if( const Switch *switchNode = runTimeCast<const Switch>( sourceNode ) )
	{
		if( source == switchNode->outPlug() )
		{
			// Switch with context-varying input. Any input branch could be
			// relevant.
			for( InputFilterPlugIterator it( switchNode->inPlugs() ); !it.done(); ++it )
			{
				(*it)->sceneAffects( scenePlugChild, outputs );
			}
		}
	}
}

FilterPlug::SceneScope::SceneScope( const Gaffer::Context *context, const ScenePlug *scenePlug )
	:	EditableScope( context )
{
	set( inputSceneContextName, (uint64_t)scenePlug );
}
