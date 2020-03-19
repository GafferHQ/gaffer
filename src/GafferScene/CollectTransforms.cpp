//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#include "IECoreScene/Primitive.h"

#include "GafferScene/Transform.h"

#include "GafferScene/CollectTransforms.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace {

const IECore::ConstCompoundObjectPtr g_emptyCompound = new IECore::CompoundObject();
const IECore::MurmurHash g_emptyCompoundHash = g_emptyCompound->Object::hash();
const ScenePlug::ScenePath g_emptyScenePath;

}

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( CollectTransforms );

size_t CollectTransforms::g_firstPlugIndex = 0;

CollectTransforms::CollectTransforms( const std::string &name )
	:	AttributeProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringVectorDataPlug( "attributes", Plug::In, new StringVectorData() ) );
	addChild( new StringPlug( "attributeContextVariable", Plug::In, "collect:transformName" ) );
	addChild( new IntPlug( "space", Plug::In, GafferScene::Transform::Local, GafferScene::Transform::Local, GafferScene::Transform::World ) );
	addChild( new BoolPlug( "requireVariation", Plug::In, false ) );

	addChild( new CompoundObjectPlug( "transforms", Plug::Out, new CompoundObject() ) );
}

CollectTransforms::~CollectTransforms()
{
}

Gaffer::StringVectorDataPlug *CollectTransforms::attributesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 0 );
}

const Gaffer::StringVectorDataPlug *CollectTransforms::attributesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 0 );
}

Gaffer::StringPlug *CollectTransforms::attributeContextVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *CollectTransforms::attributeContextVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *CollectTransforms::spacePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *CollectTransforms::spacePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

Gaffer::BoolPlug *CollectTransforms::requireVariationPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::BoolPlug *CollectTransforms::requireVariationPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

Gaffer::CompoundObjectPlug *CollectTransforms::transformsPlug()
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::CompoundObjectPlug *CollectTransforms::transformsPlug() const
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 4 );
}

void CollectTransforms::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	AttributeProcessor::affects( input, outputs );

	if(
		input == inPlug()->transformPlug() ||
		input == attributesPlug() ||
		input == attributeContextVariablePlug() ||
		input == spacePlug() ||
		input == requireVariationPlug()
	)
	{
		outputs.push_back( transformsPlug() );
	}
}

void CollectTransforms::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	AttributeProcessor::hash( output, context, h );
	if( output == transformsPlug() )
	{
		bool worldMatrix = spacePlug()->getValue() == GafferScene::Transform::World;
		const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName, g_emptyScenePath );
		if( scenePath.size() == 0 )
		{
			h = g_emptyCompoundHash;
			return;
		}

		IECore::MurmurHash inHash;
		if( worldMatrix )
		{
			inHash = inPlug()->fullTransformHash( scenePath );
		}
		else
		{
			inHash = inPlug()->transformPlug()->hash();
		}

		// We use this plug to drive the output attributes name, even if the inputs
		// aren't varying, so we need to hash it in
		h.append( attributesPlug()->hash() );
		h.append( requireVariationPlug()->hash() );

		ConstStringVectorDataPtr namesData = attributesPlug()->getValue();
		const vector<string>& names = namesData->readable();

		bool requireVariation = requireVariationPlug()->getValue();
		bool hasVariation = false;

		Context::EditableScope scope( context );

		InternedString attributeContextVariableName( attributeContextVariablePlug()->getValue() );
		for( const std::string &name : names )
		{
			scope.set( attributeContextVariableName, name );
			IECore::MurmurHash collectedHash;
			if( worldMatrix )
			{
				collectedHash = inPlug()->fullTransformHash( scenePath );
			}
			else
			{
				collectedHash = inPlug()->transformPlug()->hash();
			}

			if( collectedHash != inHash )
			{
				hasVariation = true;
			}
			h.append( collectedHash );
		}

		if( requireVariation && !hasVariation )
		{
			h = g_emptyCompoundHash;
			return;
		}

		if( requireVariation )
		{
			h.append( inHash );
		}

	}

}

void CollectTransforms::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == transformsPlug() )
	{
		bool worldMatrix = spacePlug()->getValue() == GafferScene::Transform::World;
		const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName, g_emptyScenePath );
		if( scenePath.size() == 0 )
		{
			static_cast<CompoundObjectPlug *>( output )->setValue( g_emptyCompound );
			return;
		}

		IECore::MurmurHash inHash = inPlug()->transformPlug()->hash();
		M44f inTransform = inPlug()->transformPlug()->getValue( &inHash );

		if( worldMatrix )
		{
			inHash = inPlug()->fullTransformHash( scenePath );
			inTransform = inPlug()->fullTransform( scenePath );
		}
		else
		{
			inHash = inPlug()->transformPlug()->hash();
			inTransform = inPlug()->transformPlug()->getValue( &inHash );
		}

		IECore::CompoundObjectPtr result = new IECore::CompoundObject();

		ConstStringVectorDataPtr namesData = attributesPlug()->getValue();
		const vector<string>& names = namesData->readable();

		bool requireVariation = requireVariationPlug()->getValue();

		Context::EditableScope scope( context );

		InternedString attributeContextVariableName( attributeContextVariablePlug()->getValue() );
		for( const std::string &name : names )
		{
			scope.set( attributeContextVariableName, name );
			if( worldMatrix )
			{
				IECore::MurmurHash collectedTransformHash = inPlug()->fullTransformHash( scenePath );
				if( collectedTransformHash != inHash )
				{
					M44f collectedTransform = inPlug()->fullTransform( scenePath );
					if( collectedTransform != inTransform )
					{
						result->members()[ name ] = new M44fData( collectedTransform );
					}
				}
			}
			else
			{
				IECore::MurmurHash collectedTransformHash = inPlug()->transformPlug()->hash();
				if( collectedTransformHash != inHash )
				{
					M44f collectedTransform = inPlug()->transformPlug()->getValue( &collectedTransformHash );
					if( collectedTransform != inTransform )
					{
						result->members()[ name ] = new M44fData( collectedTransform );
					}
				}
			}

		}

		if( requireVariation && result->members().size() == 0 )
		{
			static_cast<CompoundObjectPlug *>( output )->setValue( g_emptyCompound );
			return;
		}

		// We aren't returning empty, so we should fill in any spots in
		// the result that were left empty because they matched the input
		for( const std::string &name : names )
		{
			result->members().insert(
				std::pair<IECore::InternedString,IECore::ObjectPtr>( name, new M44fData( inTransform ) )
			);
		}

		static_cast<CompoundObjectPlug *>( output )->setValue( result );
		return;
	}

	AttributeProcessor::compute( output, context );
}


bool CollectTransforms::affectsProcessedAttributes( const Gaffer::Plug *input ) const
{
	return AttributeProcessor::affectsProcessedAttributes( input ) || input == transformsPlug();
}

void CollectTransforms::hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	IECore::MurmurHash transformsHash = transformsPlug()->hash();
	if( transformsHash == g_emptyCompoundHash )
	{
		h = inPlug()->attributesPlug()->hash();
	}
	else
	{
		AttributeProcessor::hashProcessedAttributes( path, context, h );
		h.append( transformsHash );
	}
}


IECore::ConstCompoundObjectPtr CollectTransforms::computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, const IECore::CompoundObject *inputAttributes ) const
{
	IECore::ConstCompoundObjectPtr collectedTransforms = transformsPlug()->getValue();
	if( collectedTransforms->members().size() == 0 )
	{
		return inputAttributes;
	}

	IECore::CompoundObjectPtr result = new CompoundObject();

	// Since we're not going to modify any existing members (only add new ones),
	// and our result becomes const on returning it, we can directly reference
	// the input members in our result without copying. Be careful not to modify
	// them though!
	result->members() = inputAttributes->members();

	for( auto nameTransform : collectedTransforms->members() )
	{
		result->members()[ nameTransform.first ] = nameTransform.second;
	}

	return result;
}


