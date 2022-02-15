//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferArnold/ArnoldImager.h"

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
const InternedString g_imagerAttributeName( "ai:imager" );
const InternedString g_imagerOptionName( "option:ai:imager" );

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

GAFFER_NODE_DEFINE_TYPE( ArnoldImager );

size_t ArnoldImager::g_firstPlugIndex = 0;

ArnoldImager::ArnoldImager( const std::string &name )
	:	GlobalsProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ShaderPlug( "imager" ) );
	addChild( new IntPlug( "mode", Plug::In, (int)Mode::Replace, (int)Mode::Replace, (int)Mode::InsertLast ) );
}

ArnoldImager::~ArnoldImager()
{
}

GafferScene::ShaderPlug *ArnoldImager::imagerPlug()
{
	return getChild<ShaderPlug>( g_firstPlugIndex );
}

const GafferScene::ShaderPlug *ArnoldImager::imagerPlug() const
{
	return getChild<ShaderPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *ArnoldImager::modePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *ArnoldImager::modePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

bool ArnoldImager::acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const
{
	if( !GlobalsProcessor::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}

	if( plug != imagerPlug() )
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

	return sourceShader->typePlug()->getValue() == "ai:imager";
}

void ArnoldImager::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	GlobalsProcessor::affects( input, outputs );

	if( input == imagerPlug() || input == modePlug() )
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void ArnoldImager::hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h.append( imagerPlug()->attributesHash() );
	modePlug()->hash( h );
}

IECore::ConstCompoundObjectPtr ArnoldImager::computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const
{
	ConstCompoundObjectPtr attributes = imagerPlug()->attributes();
	if( attributes->members().empty() )
	{
		return inputGlobals;
	}

	const IECoreScene::ShaderNetwork *imager = attributes->member<IECoreScene::ShaderNetwork>( g_imagerAttributeName );
	if( !imager )
	{
		throw IECore::Exception( "Imager not found" );
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
		const ShaderNetwork *inputImager = inputGlobals->member<ShaderNetwork>( g_imagerOptionName );
		if( !inputImager || !inputImager->size() )
		{
			result->members()[g_imagerOptionName] = const_cast<ShaderNetwork *>( imager );
		}
		else
		{
			ShaderNetworkPtr mergedImager = inputImager->copy();
			ShaderNetwork::Parameter insertedOut = ShaderNetworkAlgo::addShaders( mergedImager.get(), imager );
			if( mode == Mode::InsertLast )
			{
				mergedImager->addConnection( {
					mergedImager->getOutput(),
					firstInput( mergedImager.get(), insertedOut.shader )
				} );
				mergedImager->setOutput( insertedOut );
			}
			else
			{
				assert( mode == Mode::InsertFirst );
				mergedImager->addConnection( {
					insertedOut,
					firstInput( mergedImager.get(), mergedImager->getOutput().shader )
				} );
			}
			result->members()[g_imagerOptionName] = mergedImager;
		}
	}
	else
	{
		assert( mode == Mode::Replace );
		result->members()[g_imagerOptionName] = const_cast<ShaderNetwork *>( imager );
	}

	return result;
}
