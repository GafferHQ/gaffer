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

#include "GafferSceneTest/TestLight.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/PlugAlgo.h"

#include "IECoreScene/Shader.h"

using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneTest;

GAFFER_NODE_DEFINE_TYPE( TestLight )

size_t TestLight::g_firstPlugIndex = 0;

TestLight::TestLight( const std::string &name )
	:	Light( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new TestShader( "__shader" ) );
	addChild( new ShaderPlug( "__shaderIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	/// \todo Remove this when merging to `main` after changing `TestShader` to not load a
	/// default shader. We need it for now to remove the child plugs resulting from loading
	/// `simpleShader` in the `TestShader` constructor.
	shaderNode()->parametersPlug()->clearChildren();

	shaderNode()->typePlug()->setValue( "light" );
	shaderNode()->parametersPlug()->setFlags( Plug::AcceptsInputs, true );
	shaderNode()->parametersPlug()->setInput( parametersPlug() );

	shaderInPlug()->setInput( shaderNode()->outPlug() );

	shaderNode()->loadShader( "simpleLight" );
}

TestLight::~TestLight()
{
}

TestShader *TestLight::shaderNode()
{
	return getChild<TestShader>( g_firstPlugIndex );
}

const TestShader *TestLight::shaderNode() const
{
	return getChild<TestShader>( g_firstPlugIndex );
}

ShaderPlug *TestLight::shaderInPlug()
{
	return getChild<ShaderPlug>( g_firstPlugIndex + 1 );
}

const ShaderPlug *TestLight::shaderInPlug() const
{
	return getChild<ShaderPlug>( g_firstPlugIndex + 1 );
}

void TestLight::loadShader( const std::string &shaderName )
{
	shaderNode()->loadShader( shaderName );
	shaderNode()->typePlug()->setValue( "light" );
	shaderInPlug()->setInput( shaderNode()->outPlug() );
}

void TestLight::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	Light::affects( input, outputs );

	if( input == shaderInPlug() )
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}
}

void TestLight::hashLight( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h.append( shaderInPlug()->attributesHash() );
}

IECoreScene::ConstShaderNetworkPtr TestLight::computeLight( const Gaffer::Context *context ) const
{
	IECore::ConstCompoundObjectPtr shaderAttributes = shaderInPlug()->attributes();
	return shaderAttributes->member<const IECoreScene::ShaderNetwork>( "light" );
}
