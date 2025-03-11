//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, John Haddon. All rights reserved.
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

#include "GafferRenderMan/RenderManLight.h"

#include "GafferRenderMan/RenderManShader.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferRenderMan;

IE_CORE_DEFINERUNTIMETYPED( RenderManLight );

size_t RenderManLight::g_firstPlugIndex = 0;

RenderManLight::RenderManLight( const std::string &name )
	:	GafferScene::Light( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new RenderManShader( "__shader" ) );
	addChild( new ShaderPlug( "__shaderIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	shaderNode()->parametersPlug()->setFlags( Plug::AcceptsInputs, true );
	shaderNode()->parametersPlug()->setInput( parametersPlug() );

	shaderInPlug()->setInput( shaderNode()->outPlug() );
}

RenderManLight::~RenderManLight()
{
}

Shader *RenderManLight::shaderNode()
{
	return getChild<Shader>( g_firstPlugIndex );
}

const Shader *RenderManLight::shaderNode() const
{
	return getChild<Shader>( g_firstPlugIndex );
}

GafferScene::ShaderPlug *RenderManLight::shaderInPlug()
{
	return getChild<ShaderPlug>( g_firstPlugIndex + 1 );
}

const GafferScene::ShaderPlug *RenderManLight::shaderInPlug() const
{
	return getChild<ShaderPlug>( g_firstPlugIndex + 1 );
}

void RenderManLight::loadShader( const std::string &shaderName )
{
	shaderNode()->loadShader( shaderName );
}

void RenderManLight::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	Light::affects( input, outputs );

	if(
		input == shaderInPlug()
	)
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}
}

void RenderManLight::hashLight( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h.append( shaderInPlug()->attributesHash() );
}

IECoreScene::ConstShaderNetworkPtr RenderManLight::computeLight( const Gaffer::Context *context ) const
{
	IECore::ConstCompoundObjectPtr shaderAttributes = shaderInPlug()->attributes();
	return shaderAttributes->member<const IECoreScene::ShaderNetwork>( "ri:light" );
}
