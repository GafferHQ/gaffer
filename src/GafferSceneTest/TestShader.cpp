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

#include "GafferSceneTest/TestShader.h"

#include "GafferScene/ShaderTweakProxy.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/OptionalValuePlug.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/SplinePlug.h"

#include "IECore/Spline.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferSceneTest;

namespace
{

template<typename PlugType>
Plug *setupTypedPlug(
	const InternedString &parameterName,
	GraphComponent *plugParent,
	const typename PlugType::ValueType &defaultValue
)
{
	PlugType *existingPlug = plugParent->getChild<PlugType>( parameterName );
	if( existingPlug && existingPlug->defaultValue() == defaultValue )
	{
		return existingPlug;
	}

	typename PlugType::Ptr plug = new PlugType( parameterName, Plug::Direction::In, defaultValue );
	PlugAlgo::replacePlug( plugParent, plug );

	return plug.get();
}

template<typename ValuePlugType>
Plug *setupOptionalValuePlug(
	const InternedString &parameterName,
	GraphComponent *plugParent,
	const ValuePlugPtr &valuePlug
)
{
	OptionalValuePlug *existingPlug = plugParent->getChild<OptionalValuePlug>( parameterName );

	if( existingPlug && valuePlug->typeId() == ValuePlugType::staticTypeId() )
	{
		auto existingValuePlug = runTimeCast<ValuePlugType>( existingPlug->valuePlug() );
		auto typedPlug = runTimeCast<ValuePlugType>( valuePlug );
		if( existingValuePlug->defaultValue() == typedPlug->defaultValue() )
		{
			return existingPlug;
		}
	}

	OptionalValuePlugPtr plug = new OptionalValuePlug( parameterName, valuePlug );
	PlugAlgo::replacePlug( plugParent, plug );

	return plug.get();
}

GafferScene::ShaderTweakProxy::ShaderLoaderDescription<TestShader> g_testShaderTweakProxyLoaderRegistration( "test" );
} // namespace

GAFFER_NODE_DEFINE_TYPE( TestShader )

TestShader::TestShader( const std::string &name )
	:	Shader( name )
{
	// The base class expects `loadShader()` to set `type`, but
	// we don't want to make assumptions for the purposes of testing.
	// Turn serialisation back on to preserve the user-specified type.
	typePlug()->setFlags( Plug::Serialisable, true );

	addChild( new Color3fPlug( "out", Plug::Out ) );

	loadShader( "simpleShader" );
}

TestShader::~TestShader()
{
}

void TestShader::loadShader( const std::string &shaderName, bool keepExistingValues )
{
	Plug *parametersPlug = this->parametersPlug()->source<Plug>();

	if( !keepExistingValues )
	{
		parametersPlug->clearChildren();
	}

	namePlug()->source<StringPlug>()->setValue( shaderName );

	if( shaderName == "simpleLight" )
	{
		setupTypedPlug<Color3fPlug>( "intensity", parametersPlug, Imath::Color3f( 0.f ) );
		setupTypedPlug<FloatPlug>( "exposure", parametersPlug, 0.f );
		setupTypedPlug<BoolPlug>( "__areaLight", parametersPlug, false );
	}
	else if( shaderName == "simpleShader" )
	{
		setupTypedPlug<IntPlug>( "i", parametersPlug, 0 );
		setupTypedPlug<Color3fPlug>( "c", parametersPlug, Imath::Color3f( 0.f ) );
		setupTypedPlug<SplinefColor3fPlug>( "spline", parametersPlug, SplineDefinitionfColor3f() );
		setupOptionalValuePlug<StringPlug>( "optionalString", parametersPlug, new StringPlug() );
	}
}
