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

#include "Gaffer/SubGraph.h"
#include "Gaffer/Dot.h"

#include "Gaffer/Context.h"

#include "GafferScene/FilteredSceneProcessor.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( FilteredSceneProcessor );

size_t FilteredSceneProcessor::g_firstPlugIndex = 0;

FilteredSceneProcessor::FilteredSceneProcessor( const std::string &name, Filter::Result filterDefault )
	:	SceneProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "filter", Plug::In, filterDefault, Filter::NoMatch, Filter::EveryMatch ) );
}

FilteredSceneProcessor::~FilteredSceneProcessor()
{
}

Gaffer::IntPlug *FilteredSceneProcessor::filterPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *FilteredSceneProcessor::filterPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

void FilteredSceneProcessor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );

	const ScenePlug *scenePlug = input->parent<ScenePlug>();
	if( scenePlug && scenePlug == inPlug() )
	{
		const Filter *filter = runTimeCast<const Filter>( filterPlug()->source<Plug>()->node() );
		if( filter && filter->sceneAffectsMatch( scenePlug, static_cast<const ValuePlug *>( input ) ) )
		{
			outputs.push_back( filterPlug() );
		}
	}
}

bool FilteredSceneProcessor::acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const
{
	if( !SceneProcessor::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}

	if( !inputPlug )
	{
		return true;
	}

	if( plug == filterPlug() )
	{
		// We only really want to accept inputs from Filter nodes.
		const Plug *source = inputPlug->source<Plug>();
		const Node *n = source->node();
		if( const Filter *filter = runTimeCast<const Filter>( n ) )
		{
			if( source == filter->outPlug() )
			{
				return true;
			}
		}
		// But we can also trust connections from FilteredSceneProcessor::filterPlug()
		// because it will have these exact same checks applied when it gets an input.
		// This is particularly necessary for derived classes which may wish to wire
		// up an internal network with connections to the external filter plug.
		if( const FilteredSceneProcessor *f = runTimeCast<const FilteredSceneProcessor>( n ) )
		{
			if( source == f->filterPlug() )
			{
				return true;
			}
		}
		// And we must also accept certain intermediate plugs speculatively in case they
		// provide a filter connection in the future. We can do this because we are
		// safe in the knowledge that this check will be called when the intermediate
		// plug is having its input set.
		return runTimeCast<const SubGraph>( n ) || runTimeCast<const Dot>( n );
	}
	return true;
}

Gaffer::ContextPtr FilteredSceneProcessor::filterContext( const Gaffer::Context *context ) const
{
	Context *result = new Context( *context, Context::Borrowed );
	Filter::setInputScene( result, inPlug() );
	return result;
}

void FilteredSceneProcessor::filterHash( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ContextPtr c = filterContext( context );
	Context::Scope s( c.get() );
	filterPlug()->hash( h );
}

Filter::Result FilteredSceneProcessor::filterValue( const Gaffer::Context *context ) const
{
	ContextPtr c = filterContext( context );
	Context::Scope s( c.get() );
	return (Filter::Result)filterPlug()->getValue();
}
