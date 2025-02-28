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

#include "GafferRenderMan/RenderManIntegrator.h"

#include "GafferScene/Shader.h"
#include "GafferScene/ShaderPlug.h"

#include "Gaffer/StringPlug.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferRenderMan;

IE_CORE_DEFINERUNTIMETYPED( RenderManIntegrator );

RenderManIntegrator::RenderManIntegrator( const std::string &name )
	:	GlobalShader( name )
{
}

RenderManIntegrator::~RenderManIntegrator()
{
}

bool RenderManIntegrator::acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const
{
	if( !GlobalShader::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}

	if( plug != shaderPlug() )
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

	return sourceShader->typePlug()->getValue() == "ri:integrator";
}

bool RenderManIntegrator::affectsOptionName( const Gaffer::Plug *input ) const
{
	return false;
}

void RenderManIntegrator::hashOptionName( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	// No need to hash anything, because our option name is constant
}

std::string RenderManIntegrator::computeOptionName( const Gaffer::Context *context ) const
{
	return "ri:integrator";
}
