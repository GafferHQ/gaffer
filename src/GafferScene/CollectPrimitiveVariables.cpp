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

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////
// CollectPrimitiveVariables
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( CollectPrimitiveVariables );

size_t CollectPrimitiveVariables::g_firstPlugIndex = 0;

CollectPrimitiveVariables::CollectPrimitiveVariables( const std::string &name )
	:	SceneElementProcessor( name, IECore::PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringVectorDataPlug( "suffixes", Plug::In, new StringVectorData() ) );
	addChild( new StringPlug( "suffixContextVariable", Plug::In, "collect:primitiveVariableSuffix" ) );
	addChild( new StringPlug( "targetVariables", Plug::In, "P" ) );
	addChild( new BoolPlug( "requiresVariation", Plug::In, false ) );

	// Fast pass-throughs for things we don't modify
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
}

CollectPrimitiveVariables::~CollectPrimitiveVariables()
{
}

Gaffer::StringVectorDataPlug *CollectPrimitiveVariables::suffixesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 0 );
}

const Gaffer::StringVectorDataPlug *CollectPrimitiveVariables::suffixesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 0 );
}

Gaffer::StringPlug *CollectPrimitiveVariables::suffixContextVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *CollectPrimitiveVariables::suffixContextVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *CollectPrimitiveVariables::targetVariablesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *CollectPrimitiveVariables::targetVariablesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::BoolPlug *CollectPrimitiveVariables::requiresVariationPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::BoolPlug *CollectPrimitiveVariables::requiresVariationPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

void CollectPrimitiveVariables::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if(
		input == inPlug()->objectPlug() ||
		input == suffixesPlug() ||
		input == suffixContextVariablePlug() ||
		input == targetVariablesPlug() ||
		input == requiresVariationPlug()
	)
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

void CollectPrimitiveVariables::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	IECore::MurmurHash inputHash = inPlug()->objectPlug()->hash();

	h.append( targetVariablesPlug()->hash() );
	h.append( suffixesPlug()->hash() );

	IECore::MurmurHash requiresVariationHash = requiresVariationPlug()->hash();
	bool requiresVariation = requiresVariationPlug()->getValue( &requiresVariationHash );

	// In this method, we only check whether the hashes of the input objects match, not the value of the input objects.
	// So the value of the requireVariation plug might still matter in the case where we don't just pass the input object hash.
	h.append( requiresVariationHash );

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

	if( requiresVariation && !hasVariation )
	{
		h = inputHash;
	}
}

bool CollectPrimitiveVariables::processesObject() const
{
	return true;
}

IECore::ConstObjectPtr CollectPrimitiveVariables::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	const IECoreScene::Primitive* inPrimitive = runTimeCast<const IECoreScene::Primitive>( inputObject.get() );
	if( !inPrimitive )
	{
		return inputObject;
	}

	IECoreScene::PrimitivePtr result = inPrimitive->copy();

	std::string targetVariables = targetVariablesPlug()->getValue();

	ConstStringVectorDataPtr suffixesData = suffixesPlug()->getValue();
	const vector<string>& suffixes = suffixesData->readable();

	IECore::MurmurHash inputHash = inPlug()->objectPlug()->hash();

	bool requiresVariation = requiresVariationPlug()->getValue();

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

	if( requiresVariation )
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

	for( unsigned int i = 0; i < suffixes.size(); i++ )
	{
		const IECoreScene::Primitive* collectPrimitive = runTimeCast<const IECoreScene::Primitive>( collectedObjects[i].get() );

		if( !collectPrimitive )
		{
			continue;
		}

		for( const auto &sourceVar : collectPrimitive->variables )
		{
			if( StringAlgo::matchMultiple( sourceVar.first, targetVariables ) )
			{
				result->variables[ sourceVar.first + suffixes[i] ] = sourceVar.second;
			}
		}
	}


	return result;
}


