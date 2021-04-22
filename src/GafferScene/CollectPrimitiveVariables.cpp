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

#include "GafferScene/CollectPrimitiveVariables.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( CollectPrimitiveVariables );

size_t CollectPrimitiveVariables::g_firstPlugIndex = 0;

CollectPrimitiveVariables::CollectPrimitiveVariables( const std::string &name )
	:	ObjectProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "primitiveVariables", Plug::In, "P" ) );
	addChild( new StringVectorDataPlug( "suffixes", Plug::In, new StringVectorData() ) );
	addChild( new StringPlug( "suffixContextVariable", Plug::In, "collect:primitiveVariableSuffix" ) );
	addChild( new BoolPlug( "requireVariation", Plug::In, false ) );
}

CollectPrimitiveVariables::~CollectPrimitiveVariables()
{
}

Gaffer::StringPlug *CollectPrimitiveVariables::primitiveVariablesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 0 );
}

const Gaffer::StringPlug *CollectPrimitiveVariables::primitiveVariablesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 0 );
}

Gaffer::StringVectorDataPlug *CollectPrimitiveVariables::suffixesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringVectorDataPlug *CollectPrimitiveVariables::suffixesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *CollectPrimitiveVariables::suffixContextVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *CollectPrimitiveVariables::suffixContextVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::BoolPlug *CollectPrimitiveVariables::requireVariationPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::BoolPlug *CollectPrimitiveVariables::requireVariationPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

bool CollectPrimitiveVariables::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		ObjectProcessor::affectsProcessedObject( input ) ||
		input == suffixesPlug() ||
		input == suffixContextVariablePlug() ||
		input == primitiveVariablesPlug() ||
		input == requireVariationPlug()
	;
}

void CollectPrimitiveVariables::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ObjectProcessor::hashProcessedObject( path, context, h );

	IECore::MurmurHash inputHash = inPlug()->objectPlug()->hash();

	h.append( primitiveVariablesPlug()->hash() );
	h.append( suffixesPlug()->hash() );

	IECore::MurmurHash requireVariationHash = requireVariationPlug()->hash();
	bool requireVariation = requireVariationPlug()->getValue( &requireVariationHash );

	// In this method, we only check whether the hashes of the input objects match, not the value of the input objects.
	// So the value of the requireVariation plug might still matter in the case where we don't just pass the input object hash.
	h.append( requireVariationHash );

	Context::EditableScope scope( context );
	ConstStringVectorDataPtr suffixesData = suffixesPlug()->getValue();

	bool hasVariation = false;
	InternedString suffixContextVariableName( suffixContextVariablePlug()->getValue() );
	for( const std::string & suffix : suffixesData->readable() )
	{
		scope.set( suffixContextVariableName, suffix );
		IECore::MurmurHash curHash = inPlug()->objectPlug()->hash();
		if( curHash != inputHash )
		{
			hasVariation = true;
		}
		h.append( curHash );
	}

	if( requireVariation && !hasVariation )
	{
		h = inputHash;
	}
}

IECore::ConstObjectPtr CollectPrimitiveVariables::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const IECoreScene::Primitive* inPrimitive = runTimeCast<const IECoreScene::Primitive>( inputObject );
	if( !inPrimitive )
	{
		return inputObject;
	}

	std::string primitiveVariables = primitiveVariablesPlug()->getValue();

	ConstStringVectorDataPtr suffixesData = suffixesPlug()->getValue();
	const vector<string>& suffixes = suffixesData->readable();

	IECore::MurmurHash inputHash = inPlug()->objectPlug()->hash();

	bool requireVariation = requireVariationPlug()->getValue();

	Context::EditableScope scope( context );

	std::vector<IECore::ConstObjectPtr> collectedObjects( suffixes.size() );

	InternedString suffixContextVariableName( suffixContextVariablePlug()->getValue() );
	for( unsigned int i = 0; i < suffixes.size(); i++ )
	{
		scope.set( suffixContextVariableName, suffixes[i] );
		IECore::MurmurHash collectObjectHash = inPlug()->objectPlug()->hash();
		if( collectObjectHash == inputHash )
		{
			collectedObjects[i] = inputObject;
		}
		else
		{
			collectedObjects[i] = inPlug()->objectPlug()->getValue( &collectObjectHash );
		}
	}

	if( requireVariation )
	{
		bool variation = false;
		for( ConstObjectPtr &collectObject : collectedObjects )
		{
			if( collectObject != inputObject )
			{
				if( *collectObject != *inputObject )
				{
					variation = true;
					break;
				}
			}
		}
		if( !variation )
		{
			return inputObject;
		}
	}

	IECoreScene::PrimitivePtr result = inPrimitive->copy();
	for( unsigned int i = 0; i < suffixes.size(); i++ )
	{
		const IECoreScene::Primitive* collectPrimitive = runTimeCast<const IECoreScene::Primitive>( collectedObjects[i].get() );

		if( !collectPrimitive )
		{
			continue;
		}

		for( const auto &sourceVar : collectPrimitive->variables )
		{
			if( StringAlgo::matchMultiple( sourceVar.first, primitiveVariables ) )
			{
				result->variables[ sourceVar.first + suffixes[i] ] = sourceVar.second;
			}
		}
	}

	return result;
}
