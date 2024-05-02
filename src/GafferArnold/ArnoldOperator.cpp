//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferArnold/ArnoldOperator.h"

#include "GafferScene/Shader.h"
#include "GafferScene/ShaderPlug.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/ShaderNetwork.h"
#include "IECoreScene/ShaderNetworkAlgo.h"

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferArnold;

namespace
{

const InternedString g_inputParameterName( "input" );
const InternedString g_operatorAttributeName( "ai:operator" );
const InternedString g_operatorOptionName( "option:ai:operator" );

ShaderNetwork::Parameter firstInput( const ShaderNetwork *network, const InternedString &shader )
{
	ShaderNetwork::Parameter result( shader, g_inputParameterName );
	while( true )
	{
		if( auto input = network->input( result ) )
		{
			result.shader = input.shader;
		}
		else
		{
			return result;
		}
	}
}

} // namespace

GAFFER_NODE_DEFINE_TYPE( ArnoldOperator );

size_t ArnoldOperator::g_firstPlugIndex = 0;

ArnoldOperator::ArnoldOperator( const std::string &name )
	:	GlobalsProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ShaderPlug( "operator" ) );
	addChild( new IntPlug( "mode", Plug::In, (int)Mode::Replace, (int)Mode::Replace, (int)Mode::InsertLast ) );
}

ArnoldOperator::~ArnoldOperator()
{
}

GafferScene::ShaderPlug *ArnoldOperator::operatorPlug()
{
	return getChild<ShaderPlug>( g_firstPlugIndex );
}

const GafferScene::ShaderPlug *ArnoldOperator::operatorPlug() const
{
	return getChild<ShaderPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *ArnoldOperator::modePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *ArnoldOperator::modePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

bool ArnoldOperator::acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const
{
	if( !GlobalsProcessor::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}

	if( plug != operatorPlug() )
	{
		return true;
	}

	if( !inputPlug )
	{
		return true;
	}

	const Plug *sourcePlug = inputPlug->source();
	auto *sourceShader = runTimeCast<const GafferScene::Shader>( sourcePlug->node() );
	if( !sourceShader )
	{
		return true;
	}

	const Plug *sourceShaderOutPlug = sourceShader->outPlug();
	if( !sourceShaderOutPlug )
	{
		return true;
	}

	if( sourcePlug != sourceShaderOutPlug && !sourceShaderOutPlug->isAncestorOf( sourcePlug ) )
	{
		return true;
	}

	return sourceShader->typePlug()->getValue() == "ai:operator";
}

void ArnoldOperator::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	GlobalsProcessor::affects( input, outputs );

	if( input == operatorPlug() || input == modePlug() )
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void ArnoldOperator::hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h.append( operatorPlug()->attributesHash() );
	modePlug()->hash( h );
}

IECore::ConstCompoundObjectPtr ArnoldOperator::computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const
{
	ConstCompoundObjectPtr attributes = operatorPlug()->attributes();
	if( attributes->members().empty() )
	{
		return inputGlobals;
	}

	const IECoreScene::ShaderNetwork *aiOperator = attributes->member<IECoreScene::ShaderNetwork>( g_operatorAttributeName );
	if( !aiOperator )
	{
		throw IECore::Exception( "Operator not found" );
	}

	CompoundObjectPtr result = new CompoundObject;
	// Since we're not going to modify any existing members (only add new ones),
	// and our result becomes const on returning it, we can directly reference
	// the input members in our result without copying. Be careful not to modify
	// them though!
	result->members() = inputGlobals->members();

	const Mode mode = (Mode)modePlug()->getValue();
	if( mode == Mode::InsertFirst || mode == Mode::InsertLast )
	{
		const ShaderNetwork *inputOperator = inputGlobals->member<ShaderNetwork>( g_operatorOptionName );
		if( !inputOperator || !inputOperator->size() )
		{
			result->members()[g_operatorOptionName] = const_cast<ShaderNetwork *>( aiOperator );
		}
		else
		{
			ShaderNetworkPtr mergedOperator = inputOperator->copy();
			ShaderNetwork::Parameter insertedOut = ShaderNetworkAlgo::addShaders( mergedOperator.get(), aiOperator );
			if( mode == Mode::InsertLast )
			{
				mergedOperator->addConnection( {
					mergedOperator->getOutput(),
					firstInput( mergedOperator.get(), insertedOut.shader )
				} );
				mergedOperator->setOutput( insertedOut );
			}
			else
			{
				assert( mode == Mode::InsertFirst );
				mergedOperator->addConnection( {
					insertedOut,
					firstInput( mergedOperator.get(), mergedOperator->getOutput().shader )
				} );
			}
			result->members()[g_operatorOptionName] = mergedOperator;
		}
	}
	else
	{
		assert( mode == Mode::Replace );
		result->members()[g_operatorOptionName] = const_cast<ShaderNetwork *>( aiOperator );
	}

	return result;
}
