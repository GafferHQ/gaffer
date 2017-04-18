//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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
#include "Gaffer/StringPlug.h"

#include "GafferScene/ScenePlug.h"
#include "GafferScene/PathMatcherData.h"
#include "GafferScene/SetFilter.h"
#include "GafferScene/SetAlgo.h"

using namespace GafferScene;
using namespace Gaffer;
using namespace IECore;
using namespace std;

IE_CORE_DEFINERUNTIMETYPED( SetFilter );

size_t SetFilter::g_firstPlugIndex = 0;

SetFilter::SetFilter( const std::string &name )
	:	Filter( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "set" ) );
	addChild( new PathMatcherDataPlug( "__expressionResult", Gaffer::Plug::Out, new PathMatcherData ) );
}

SetFilter::~SetFilter()
{
}

Gaffer::StringPlug *SetFilter::setPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *SetFilter::setPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

PathMatcherDataPlug *SetFilter::expressionResultPlug()
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 1 );
}

const PathMatcherDataPlug *SetFilter::expressionResultPlug() const
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 1 );
}

void SetFilter::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	Filter::affects( input, outputs );

	if( input == setPlug() )
	{
		outputs.push_back( expressionResultPlug() );
	}

	if( input == expressionResultPlug() )
	{
		outputs.push_back( outPlug() );
	}

}

bool SetFilter::sceneAffectsMatch( const ScenePlug *scene, const Gaffer::ValuePlug *child ) const
{
	if( Filter::sceneAffectsMatch( scene, child ) )
	{
		return true;
	}

	return child == scene->setPlug();
}

void SetFilter::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Filter::hash( output, context, h );

	if( output == expressionResultPlug() )
	{
		SetAlgo::setExpressionHash( setPlug()->getValue(), getInputScene( context ), h );
	}

}

void SetFilter::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	Filter::compute( output, context );

	if( output == expressionResultPlug() )
	{
		PathMatcherDataPtr data = new PathMatcherData( SetAlgo::evaluateSetExpression( setPlug()->getValue(), getInputScene( context ) ) );
		static_cast<PathMatcherDataPlug *>( output )->setValue( data );
	}
}

void SetFilter::hashMatch( const ScenePlug *scene, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( !scene )
	{
		return;
	}

	/// \todo It would be preferable to throw an exception if the scene path isn't
	/// available, as we really do require it for computing a match. Currently we
	/// can't do that because the Isolate and Prune must include the filter hash when
	/// hashing their sets, because they will use the filter to remap the sets as
	/// a global operation. In this case, we're lucky that the hash (minus the scene path)
	/// of the SetFilter is sufficient to uniquely identify the remapping that will occur - filters
	/// which access scene data using the path would not have a valid hash in this scenario,
	/// which is the reason we don't yet have AttributeFilter etc. If we had a hierarchyHash for
	/// the scene then we would be able to use that in these situations and have a broader range
	/// of filters. If we manage that, then we should go back to throwing an exception here if
	/// the context doesn't contain a path. We should then do the same in the PathFilter.
	typedef IECore::TypedData<ScenePlug::ScenePath> ScenePathData;
	const ScenePathData *pathData = context->get<ScenePathData>( ScenePlug::scenePathContextName, 0 );
	if( pathData )
	{
		const ScenePlug::ScenePath &path = pathData->readable();
		h.append( &(path[0]), path.size() );
	}

	Gaffer::Context::EditableScope expressionResultScope( context );
	expressionResultScope.remove( ScenePlug::scenePathContextName );

	expressionResultPlug()->hash( h );
}

unsigned SetFilter::computeMatch( const ScenePlug *scene, const Gaffer::Context *context ) const
{
	if( !scene )
	{
		return NoMatch;
	}

	const ScenePlug::ScenePath &path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );

	Gaffer::Context::EditableScope expressionResultScope( context );
	expressionResultScope.remove( ScenePlug::scenePathContextName );

	ConstPathMatcherDataPtr set = expressionResultPlug()->getValue();

	return set->readable().match( path );
}
