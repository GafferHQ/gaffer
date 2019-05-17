//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/EvaluateLightLinks.h"

#include "GafferScene/SetAlgo.h"

#include "IECore/CompoundData.h"
#include "IECore/NullObject.h"

#include <cstdio>

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( EvaluateLightLinks );

size_t EvaluateLightLinks::g_firstPlugIndex = 0;

IECore::InternedString m_lightLinkAttrName = "linkedLights";
IECore::InternedString m_shadowGroupAttrName = "ai:visibility:shadow_group";
IECore::InternedString m_filteredLightsAttrName = "filteredLights";

IECore::InternedString g_lightsSetName( "__lights" );
IECore::InternedString g_defaultLightsSetName( "defaultLights" );

IECore::InternedString g_expressionContextEntryName( "__evaluateLightLinks:setExpression" );

namespace{

IECore::ObjectPtr setToValidLightNames( const PathMatcher &linkedLights, const PathMatcher &allLights )
{
	IECore::StringVectorDataPtr lightNamesData = new IECore::StringVectorData();
	std::vector<std::string> &lightNames = lightNamesData->writable();

	const PathMatcher &intersected = linkedLights.intersection( allLights );
	intersected.paths( lightNames );

	return lightNamesData;
}

} // namespace


EvaluateLightLinks::EvaluateLightLinks( const std::string &name )
	:	SceneProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	// Private plug used only to cache computation results.
	addChild( new Gaffer::ObjectPlug( "__lightNames", Gaffer::Plug::Out, NullObject::defaultNullObject() ) );

	// Fast pass-throughs for the things we don't alter.
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->setNamesPlug()->setInput( inPlug()->setNamesPlug() );
	outPlug()->setPlug()->setInput( inPlug()->setPlug() );
	outPlug()->objectPlug()->setInput( inPlug()->objectPlug() );
	outPlug()->childNamesPlug()->setInput( inPlug()->childNamesPlug() );
	outPlug()->globalsPlug()->setInput( inPlug()->globalsPlug() );
}

EvaluateLightLinks::~EvaluateLightLinks()
{
}

void EvaluateLightLinks::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );

	if( input == inPlug()->attributesPlug() )
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}

	if( input->parent<ScenePlug>() == inPlug() && SetAlgo::affectsSetExpression( input ) )
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}
}

void EvaluateLightLinks::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneProcessor::hash( output, context, h );

	if( output == lightNamesPlug() )
	{
		const StringData *expressionData = context->get<StringData>( g_expressionContextEntryName, nullptr );

		if( expressionData )
		{
			h.append( SetAlgo::setExpressionHash( expressionData->readable(), inPlug() ) );
			h.append( inPlug()->setHash( g_lightsSetName ) );
		}
		else
		{
			ScenePlug::SetScope scope( context, g_lightsSetName );

			h.append( inPlug()->setPlug()->hash() );
			scope.setSetName( g_defaultLightsSetName );
			h.append( inPlug()->setPlug()->hash() );
		}

		return;
	}
}

void EvaluateLightLinks::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == lightNamesPlug() )
	{
		const StringData *expressionData = context->get<StringData>( g_expressionContextEntryName, nullptr );

		ObjectPtr result = NullObject::defaultNullObject();
		if( expressionData )
		{
			PathMatcher linkedSet = SetAlgo::evaluateSetExpression( expressionData->readable(), inPlug() );
			ConstPathMatcherDataPtr lightsSet = inPlug()->set( g_lightsSetName );
			result = setToValidLightNames( linkedSet, lightsSet->readable() );
		}
		else
		{
			ScenePlug::SetScope scope( context, g_lightsSetName );

			IECore::MurmurHash lightsSetHash = inPlug()->setPlug()->hash();
			scope.setSetName( g_defaultLightsSetName );
			IECore::MurmurHash defaultLightsSetHash = inPlug()->setPlug()->hash();

			if( defaultLightsSetHash != lightsSetHash )
			{
				ConstPathMatcherDataPtr defaultLightsSetData = inPlug()->setPlug()->getValue( &defaultLightsSetHash );
				const PathMatcher &defaultLightsSet = defaultLightsSetData->readable();

				scope.setSetName( g_lightsSetName );
				ConstPathMatcherDataPtr lightsSetData = inPlug()->setPlug()->getValue( &lightsSetHash );
				const PathMatcher &lightsSet = lightsSetData->readable();

				if( lightsSet != defaultLightsSet )
				{
					result = setToValidLightNames( defaultLightsSet, lightsSet );
				}
			}
		}

		static_cast<Gaffer::ObjectPlug *>( output )->setValue( result );
	}

	return SceneProcessor::compute( output, context );
}

void EvaluateLightLinks::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	const MurmurHash inputHash = inPlug()->attributesPlug()->hash();
	ConstCompoundObjectPtr inputAttributes = inPlug()->attributesPlug()->getValue( &inputHash );

	ConstStringDataPtr illuminationExpressionData = inputAttributes->member<StringData>( m_lightLinkAttrName );
	ConstStringDataPtr shadowExpressionData = inputAttributes->member<StringData>( m_shadowGroupAttrName );
	ConstStringDataPtr filteredLightsExpressionData = inputAttributes->member<StringData>( m_filteredLightsAttrName );

	if( !illuminationExpressionData && !shadowExpressionData && path.size() != 1 && !filteredLightsExpressionData )
	{
		// Pass through.
		h = inputHash;
		return;
	}

	SceneProcessor::hashAttributes( path, context, parent, h );
	h.append( inputHash );

	Context::EditableScope scope( context );

	if( illuminationExpressionData || path.size() == 1 )
	{
		if( illuminationExpressionData )
		{
			scope.set<std::string>( g_expressionContextEntryName, illuminationExpressionData->readable() );
		}

		h.append( lightNamesPlug()->hash() );
	}

	if( shadowExpressionData || path.size() == 1 )
	{
		if( shadowExpressionData )
		{
			scope.set<std::string>( g_expressionContextEntryName, shadowExpressionData->readable() );
		}
		else
		{
			scope.remove( g_expressionContextEntryName );
		}

		h.append( lightNamesPlug()->hash() );
	}

	if( filteredLightsExpressionData )
	{
		scope.set<std::string>( g_expressionContextEntryName, filteredLightsExpressionData->readable() );
		h.append( lightNamesPlug()->hash() );
	}
}

IECore::ConstCompoundObjectPtr EvaluateLightLinks::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	IECore::ConstCompoundObjectPtr inputAttributes = inPlug()->attributesPlug()->getValue();

	ConstStringDataPtr illuminationExpressionData = inputAttributes->member<StringData>( m_lightLinkAttrName );
	ConstStringDataPtr shadowExpressionData = inputAttributes->member<StringData>( m_shadowGroupAttrName );
	ConstStringDataPtr filteredLightsExpressionData = inputAttributes->member<StringData>( m_filteredLightsAttrName );

	// In addition to locations that have SetExpressions assigned that need
	// evaluating, locations at the root level of the hierarchy need to consider
	// the set containing default lights. As an optimization, we don't provide
	// linking data based on this set unless lights exist that don't illuminate
	// geometry by default. Renderers consider all lights to be linked unless told
	// otherwise anyway. The resulting linking is propagated through the hierarchy
	// via inheritance.

	if( !illuminationExpressionData && !shadowExpressionData && path.size() != 1 && !filteredLightsExpressionData )
	{
		// Pass through
		return inputAttributes;
	}

	CompoundObjectPtr result = new CompoundObject;
	result->members() = inputAttributes->members();

	Context::EditableScope scope( context );

	if( illuminationExpressionData || path.size() == 1 )
	{
		if( illuminationExpressionData )
		{
			scope.set<std::string>( g_expressionContextEntryName, illuminationExpressionData->readable() );
		}

		ConstObjectPtr object = lightNamesPlug()->getValue();
		if( object != NullObject::defaultNullObject() )
		{
			const StringVectorData *tmp = static_cast<const StringVectorData *>( object.get() );
			result->members()[ m_lightLinkAttrName ] = const_cast<StringVectorData *>( tmp );
		}
	}

	if( shadowExpressionData || path.size() == 1 )
	{
		if( shadowExpressionData )
		{
			scope.set<std::string>( g_expressionContextEntryName, shadowExpressionData->readable() );
		}
		else
		{
			scope.remove( g_expressionContextEntryName );
		}

		ConstObjectPtr object = lightNamesPlug()->getValue();
		if( object != NullObject::defaultNullObject() )
		{
			const StringVectorData *tmp = static_cast<const StringVectorData *>( object.get() );
			result->members()[ m_shadowGroupAttrName ] = const_cast<StringVectorData *>( tmp );
		}
	}

	if( filteredLightsExpressionData )
	{
		scope.set<std::string>( g_expressionContextEntryName, filteredLightsExpressionData->readable() );
		ConstObjectPtr object = lightNamesPlug()->getValue();

		const StringVectorData *tmp = static_cast<const StringVectorData *>( object.get() );
		result->members()[ m_filteredLightsAttrName ] = const_cast<StringVectorData *>( tmp );
	}

	return result;
}

Gaffer::ObjectPlug *EvaluateLightLinks::lightNamesPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex );
}

const Gaffer::ObjectPlug *EvaluateLightLinks::lightNamesPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex );
}
