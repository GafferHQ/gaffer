//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller. All rights reserved.
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

#include "GafferCycles/CyclesShader.h"

#include "GafferCycles/SocketHandler.h"

#include "GafferScene/ShaderTweakProxy.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"

#include "GafferOSL/OSLShader.h"

#include "IECore/LRUCache.h"
#include "IECore/MessageHandler.h"

#include "IECoreScene/ShaderNetwork.h"

#include "boost/algorithm/string.hpp"

// Cycles
#include "graph/node.h"

using namespace std;
using namespace boost;
using namespace Imath;
using namespace IECore;
using namespace GafferScene;
using namespace GafferCycles;
using namespace Gaffer;
using namespace GafferOSL;

namespace
{

// This is to allow Cycles Shaders to be connected to OSL Shaders
bool g_oslRegistrationSurface = OSLShader::registerCompatibleShader( "cycles:surface" );
bool g_oslRegistrationVolume = OSLShader::registerCompatibleShader( "cycles:volume" );
bool g_oslRegistrationDisplacement = OSLShader::registerCompatibleShader( "cycles:displacement" );

ShaderTweakProxy::ShaderLoaderDescription<CyclesShader> g_cyclesShaderTweakProxyLoaderRegistration( "cycles" );


} // namespace

IE_CORE_DEFINERUNTIMETYPED( CyclesShader );

CyclesShader::CyclesShader( const std::string &name )
	:	GafferScene::Shader( name )
{
	addChild( new Plug( "out", Gaffer::Plug::Out ) );
}

CyclesShader::~CyclesShader()
{
}

void CyclesShader::loadShader( const std::string &shaderName, bool keepExistingValues )
{

	// First populate all the Gaffer plugs for shaders
	auto cShaderName = ccl::ustring( shaderName.c_str() );
	const ccl::NodeType *shaderNodeType = ccl::NodeType::find( cShaderName );

	if( !shaderNodeType )
	{
		throw Exception( fmt::format( "Shader \"{}\" not found", shaderName ) );
	}

	const bool outPlugWasEmpty = outPlug()->children().empty();
	if( !keepExistingValues )
	{
		parametersPlug()->clearChildren();
		outPlug()->clearChildren();
	}

	namePlug()->setValue( shaderName );

	if( boost::ends_with( shaderName, "volume" ) )
	{
		typePlug()->setValue( "cycles:volume" );
	}
	else if( boost::ends_with( shaderName, "displacement" ) )
	{
		typePlug()->setValue( "cycles:displacement" );
	}
	else if( shaderName == "aov_output" )
	{
		typePlug()->setValue( "cycles:aov:" );
	}
	else
	{
		typePlug()->setValue( "cycles:surface" );
	}

	SocketHandler::setupPlugs( shaderNodeType, parametersPlug() );
	SocketHandler::setupPlugs( shaderNodeType, outPlug(), Gaffer::Plug::Out );

	if( outPlug()->children().empty() != outPlugWasEmpty )
	{
		// CyclesShaderUI registers a dynamic metadata entry which depends on whether or
		// not the plug has children, so we must notify the world that the value will
		// have changed.
		Metadata::plugValueChangedSignal()( staticTypeId(), "out", "nodule:type", outPlug() );
	}

}

IECore::ConstCompoundObjectPtr CyclesShader::attributes( const Gaffer::Plug *output ) const
{
	ConstCompoundObjectPtr original = Shader::attributes( output );
	const IECoreScene::ShaderNetwork *network = original->member<const IECoreScene::ShaderNetwork>( "cycles:aov:" );
	if( !network || !network->size() )
	{
		return original;
	}

	std::string aovName;
	for( const auto &namedParameter : network->outputShader()->parameters() )
	{
		if( namedParameter.first.string() == "name" )
		{
			const IECore::StringData *stringData = runTimeCast<const IECore::StringData>( namedParameter.second.get() );
			aovName = stringData->readable();
			break;
		}
	}
	const std::string aovTypeName = "cycles:aov:" + aovName;
	CompoundObjectPtr result = original->copy();

	result->member<IECoreScene::ShaderNetwork>( aovTypeName, false, true );
	std::swap( result->members()[aovTypeName], result->members()["cycles:aov:"] );
	result->members().erase( "cycles:aov:" );

	return result;
}
