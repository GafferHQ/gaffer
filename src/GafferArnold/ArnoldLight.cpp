//////////////////////////////////////////////////////////////////////////
//
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

#include "GafferArnold/ArnoldLight.h"

#include "GafferArnold/ArnoldShader.h"
#include "GafferArnold/ParameterHandler.h"

#include "GafferScene/Shader.h"

#include "Gaffer/PlugAlgo.h"
#include "Gaffer/StringPlug.h"

#include "IECoreArnold/UniverseBlock.h"

#include "IECoreScene/ShaderNetworkAlgo.h"

#include "IECore/Exception.h"

#include "boost/format.hpp"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferArnold;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( ArnoldLight );

size_t ArnoldLight::g_firstPlugIndex = 0;

ArnoldLight::ArnoldLight( const std::string &name )
	:	GafferScene::Light( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ArnoldShader( "__shader" ) );
	addChild( new ShaderPlug( "__shaderIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	shaderNode()->addChild( new Plug( "out", Plug::Out ) );
	shaderNode()->typePlug()->setValue( "ai:light" );
	shaderNode()->parametersPlug()->setFlags( Plug::AcceptsInputs, true );
	shaderNode()->parametersPlug()->setInput( parametersPlug() );

	shaderInPlug()->setInput( shaderNode()->outPlug() );
}

ArnoldLight::~ArnoldLight()
{
}

ArnoldShader *ArnoldLight::shaderNode()
{
	return getChild<ArnoldShader>( g_firstPlugIndex );
}

const ArnoldShader *ArnoldLight::shaderNode() const
{
	return getChild<ArnoldShader>( g_firstPlugIndex );
}

GafferScene::ShaderPlug *ArnoldLight::shaderInPlug()
{
	return getChild<ShaderPlug>( g_firstPlugIndex + 1 );
}

const GafferScene::ShaderPlug *ArnoldLight::shaderInPlug() const
{
	return getChild<ShaderPlug>( g_firstPlugIndex + 1 );
}

void ArnoldLight::loadShader( const std::string &shaderName )
{
	shaderNode()->loadShader( shaderName );
	shaderNode()->typePlug()->setValue( "ai:light" );
	shaderInPlug()->setInput( shaderNode()->outPlug() );
}

void ArnoldLight::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	Light::affects( input, outputs );

	if( input == shaderInPlug() )
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}
}

void ArnoldLight::hashLight( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h.append( shaderInPlug()->attributesHash() );
}

IECoreScene::ConstShaderNetworkPtr ArnoldLight::computeLight( const Gaffer::Context *context ) const
{
	IECore::ConstCompoundObjectPtr shaderAttributes = shaderInPlug()->attributes();
	return shaderAttributes->member<const IECoreScene::ShaderNetwork>( "ai:light" );
}
