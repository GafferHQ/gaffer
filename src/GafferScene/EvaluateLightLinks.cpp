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

#include <cstdio>

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( EvaluateLightLinks );

IECore::InternedString m_lightLinkAttrName = "linkedLights";
IECore::InternedString m_shadowGroupAttrName = "ai:visibility:shadow_group";

namespace{

IECore::StringVectorDataPtr expressionToLightNames( const std::string &expression, const ScenePlug *in, const PathMatcher &allLights )
{
	IECore::StringVectorDataPtr lightNames = new IECore::StringVectorData();
	std::vector<std::string> &lightNamesWritable = lightNames->writable();

	PathMatcher linkedIlluminationSet = SetAlgo::evaluateSetExpression( expression, in );
	linkedIlluminationSet = linkedIlluminationSet.intersection( allLights );
	linkedIlluminationSet.paths( lightNamesWritable );

	return lightNames;
}

} // namespace


EvaluateLightLinks::EvaluateLightLinks( const std::string &name )
	:	SceneProcessor( name )
{
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

void EvaluateLightLinks::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	const MurmurHash inputHash = inPlug()->attributesPlug()->hash();
	ConstCompoundObjectPtr attributes = inPlug()->attributesPlug()->getValue( & inputHash );

	ConstStringDataPtr illuminationExpressionData = attributes->member<StringData>( m_lightLinkAttrName );
	ConstStringDataPtr shadowExpressionData = attributes->member<StringData>( m_shadowGroupAttrName );

	if( !illuminationExpressionData && !shadowExpressionData )
	{
		// Pass through.
		h = inputHash;
		return;
	}

	SceneProcessor::hashAttributes( path, context, parent, h );
	h.append( inputHash );
	if( illuminationExpressionData )
	{
		h.append( SetAlgo::setExpressionHash( illuminationExpressionData->readable(), inPlug() ) );
	}

	if( shadowExpressionData )
	{
		h.append( SetAlgo::setExpressionHash( shadowExpressionData->readable(), inPlug() ) );
	}
}

IECore::ConstCompoundObjectPtr EvaluateLightLinks::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	IECore::ConstCompoundObjectPtr inputAttributes = inPlug()->attributesPlug()->getValue();

	ConstStringDataPtr illuminationExpressionData = inputAttributes->member<StringData>( m_lightLinkAttrName );
	ConstStringDataPtr shadowExpressionData = inputAttributes->member<StringData>( m_shadowGroupAttrName );

	if( !illuminationExpressionData && !shadowExpressionData )
	{
		// Pass through
		return inputAttributes;
	}

	CompoundObjectPtr result = new CompoundObject;
	result->members() = inputAttributes->members();

	ConstPathMatcherDataPtr lightsSetData = inPlug()->set( "__lights" );
	const PathMatcher &lightsSet = lightsSetData->readable();

	if( illuminationExpressionData )
	{
		result->members()[ m_lightLinkAttrName ] = expressionToLightNames( illuminationExpressionData->readable(), inPlug(), lightsSet );
	}

	if( shadowExpressionData )
	{
		result->members()[ m_shadowGroupAttrName ] = expressionToLightNames( shadowExpressionData->readable(), inPlug(), lightsSet );
	}

	return result;
}
