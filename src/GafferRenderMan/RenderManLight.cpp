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

#include "Gaffer/Context.h"
#include "Gaffer/CompoundDataPlug.h"

#include "GafferRenderMan/RenderManLight.h"
#include "GafferRenderMan/RenderManShader.h"

using namespace Gaffer;
using namespace GafferRenderMan;

IE_CORE_DEFINERUNTIMETYPED( RenderManLight );

size_t RenderManLight::g_firstPlugIndex = 0;

RenderManLight::RenderManLight( const std::string &name )
	:	GafferScene::Light( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "__shaderName" ) );
}

RenderManLight::~RenderManLight()
{
}

void RenderManLight::loadShader( const std::string &shaderName )
{
	IECore::ConstShaderPtr shader = IECore::runTimeCast<const IECore::Shader>( RenderManShader::shaderLoader()->read( shaderName + ".sdl" ) );
	RenderManShader::loadShaderParameters( shader.get(), parametersPlug() );
	getChild<StringPlug>( "__shaderName" )->setValue( shaderName );
}

void RenderManLight::hashLight( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	parametersPlug()->hash( h );
	getChild<StringPlug>( "__shaderName" )->hash( h );
}

IECore::LightPtr RenderManLight::computeLight( const Gaffer::Context *context ) const
{
	IECore::LightPtr result = new IECore::Light( getChild<StringPlug>( "__shaderName" )->getValue() );
	for( InputValuePlugIterator it( parametersPlug() ); it!=it.end(); it++ )
	{
		result->parameters()[(*it)->getName()] = CompoundDataPlug::extractDataFromPlug( it->get() );
	}
	return result;
}
