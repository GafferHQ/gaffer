//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferArnold/ArnoldColorManager.h"

#include "GafferArnold/ArnoldShader.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferArnold;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( ArnoldColorManager );

size_t ArnoldColorManager::g_firstPlugIndex = 0;

ArnoldColorManager::ArnoldColorManager( const std::string &name )
	:	GlobalsProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new Plug( "parameters" ) );
	addChild( new ShaderPlug( "__shaderIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );
	addChild( new ArnoldShader( "__shader" ) );

	shaderNode()->parametersPlug()->setFlags( Plug::AcceptsInputs, true );
	shaderNode()->parametersPlug()->setInput( parametersPlug() );
}

ArnoldColorManager::~ArnoldColorManager()
{
}

Gaffer::Plug *ArnoldColorManager::parametersPlug()
{
	return getChild<Plug>( g_firstPlugIndex );
}

const Gaffer::Plug *ArnoldColorManager::parametersPlug() const
{
	return getChild<Plug>( g_firstPlugIndex );
}

GafferScene::ShaderPlug *ArnoldColorManager::shaderInPlug()
{
	return getChild<ShaderPlug>( g_firstPlugIndex + 1 );
}

const GafferScene::ShaderPlug *ArnoldColorManager::shaderInPlug() const
{
	return getChild<ShaderPlug>( g_firstPlugIndex + 1 );
}

ArnoldShader *ArnoldColorManager::shaderNode()
{
	return getChild<ArnoldShader>( g_firstPlugIndex + 2 );
}

const ArnoldShader *ArnoldColorManager::shaderNode() const
{
	return getChild<ArnoldShader>( g_firstPlugIndex + 2 );
}

void ArnoldColorManager::loadColorManager( const std::string &name, bool keepExistingValues )
{
	shaderNode()->loadShader( name, keepExistingValues );
	shaderInPlug()->setInput( shaderNode()->outPlug() );
}

void ArnoldColorManager::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	GlobalsProcessor::affects( input, outputs );

	if( input == shaderInPlug() )
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void ArnoldColorManager::hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h.append( shaderInPlug()->attributesHash() );
}

IECore::ConstCompoundObjectPtr ArnoldColorManager::computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const
{
	ConstCompoundObjectPtr attributes = shaderInPlug()->attributes();
	if( attributes->members().empty() )
	{
		return inputGlobals;
	}

	if( attributes->members().size() > 1 )
	{
		throw IECore::Exception( "Unexpected number of attributes" );
	}

	CompoundObjectPtr result = new CompoundObject;
	result->members() = inputGlobals->members();
	result->members()["option:ai:color_manager"] = attributes->members().begin()->second;

	return result;
}
