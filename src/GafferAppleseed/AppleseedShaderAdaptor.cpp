//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "GafferAppleseed/AppleseedShaderAdaptor.h"

#include "GafferScene/RendererAlgo.h"
#include "GafferScene/SceneProcessor.h"

#include "Gaffer/Context.h"

#include "IECoreScene/Shader.h"
#include "IECoreScene/ShaderNetwork.h"

#include "OSL/oslquery.h"

#include "tbb/concurrent_hash_map.h"

using namespace std;
using namespace OSL;
using namespace IECore;
using namespace IECoreScene;
using namespace GafferScene;
using namespace GafferAppleseed;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

IECore::InternedString g_oslShaderAttributeName( "osl:shader" );
IECore::InternedString g_oslSurfaceAttributeName( "osl:surface" );
IECore::InternedString g_bsdfParameterName( "BSDF" );
IECore::InternedString g_rendererContextName( "scene:renderer" );

typedef tbb::concurrent_hash_map<std::string, OSLQuery::Parameter *> ParameterMap;

ParameterMap &parameterMap()
{
	static ParameterMap m;
	return m;
}

OSLQuery::Parameter *firstOutputParameter( const std::string &shaderName )
{
	ParameterMap &m = parameterMap();
	ParameterMap::accessor accessor;
	if( m.insert( accessor, shaderName ) )
	{
		const char *searchPath = getenv( "OSL_SHADER_PATHS" );
		OSLQuery query;
		if( query.open( shaderName, searchPath ? searchPath : "" ) )
		{
			for( size_t i = 0, e = query.nparams(); i < e; ++i )
			{
				const OSLQuery::Parameter *parameter = query.getparam( i );
				if( parameter->isoutput )
				{
					accessor->second = new OSLQuery::Parameter( *parameter );
					break;
				}
			}
		}
	}

	return accessor->second;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// AppleseedShaderAdaptor
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( AppleseedShaderAdaptor );

AppleseedShaderAdaptor::AppleseedShaderAdaptor( const std::string &name )
	:	SceneProcessor( name )
{
	// Pass through stuff we'll never modify.
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->objectPlug()->setInput( inPlug()->objectPlug() );
	outPlug()->childNamesPlug()->setInput( inPlug()->childNamesPlug() );
	outPlug()->globalsPlug()->setInput( inPlug()->globalsPlug() );
	outPlug()->setNamesPlug()->setInput( inPlug()->setNamesPlug() );
	outPlug()->setPlug()->setInput( inPlug()->setPlug() );
}

void AppleseedShaderAdaptor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );

	if( input == inPlug()->attributesPlug() )
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}
}

void AppleseedShaderAdaptor::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashAttributes( path, context, parent, h );
	inPlug()->attributesPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr AppleseedShaderAdaptor::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	ConstCompoundObjectPtr inputAttributes = inPlug()->attributesPlug()->getValue();

	const ShaderNetwork *shaderNetwork = inputAttributes->member<const ShaderNetwork>( g_oslShaderAttributeName );
	if( !shaderNetwork )
	{
		return inputAttributes;
	}

	const Shader *outputShader = shaderNetwork->outputShader();
	if( !outputShader )
	{
		return inputAttributes;
	}

	OSLQuery::Parameter *firstOutput = firstOutputParameter( outputShader->getName() );

	// Build an adaptor network

	ShaderNetworkPtr adaptedNetwork;
	if( firstOutput && firstOutput->isclosure )
	{
		adaptedNetwork = shaderNetwork->copy();
		ShaderPtr material = new Shader( "material/as_material_builder", "osl:surface" );
		InternedString materialHandle = adaptedNetwork->addShader( "material", std::move( material ) );
		adaptedNetwork->addConnection(
			{ { adaptedNetwork->getOutput().shader, firstOutput->name.string() }, { materialHandle, g_bsdfParameterName } }
		);
		adaptedNetwork->setOutput( materialHandle );

	}
	else if( firstOutput && firstOutput->type == TypeDesc::TypeColor )
	{
		adaptedNetwork = shaderNetwork->copy();
		ShaderPtr emission = new Shader( "surface/as_emission_surface", "osl:shader" );
		InternedString emissionHandle = adaptedNetwork->addShader( "emission", std::move( emission ) );
		adaptedNetwork->addConnection(
			{ { adaptedNetwork->getOutput().shader, firstOutput->name.string() }, { emissionHandle, "Color" } }
		);

		ShaderPtr material = new Shader( "material/as_material_builder", "osl:surface" );
		InternedString materialHandle = adaptedNetwork->addShader( "material", std::move( material ) );
		adaptedNetwork->addConnection(
			{ { emissionHandle, "BSDF" }, { materialHandle, "BSDF" } }
		);

		adaptedNetwork->setOutput( materialHandle );
	}
	else if( firstOutput && ( firstOutput->type == TypeDesc::TypeFloat || firstOutput->type == TypeDesc::TypeInt ) )
	{
		adaptedNetwork = shaderNetwork->copy();
		ShaderPtr colorBuild = new Shader( "color/as_color_build", "osl:shader" );
		InternedString colorBuildHandle = adaptedNetwork->addShader( "colorBuild", std::move( colorBuild ) );
		for( const auto &channel : { "R", "G", "B" } )
		{
			adaptedNetwork->addConnection(
				{ { adaptedNetwork->getOutput().shader, firstOutput->name.string() }, { colorBuildHandle, channel } }
			);
		}

		ShaderPtr emission = new Shader( "surface/as_emission_surface", "osl:shader" );
		InternedString emissionHandle = adaptedNetwork->addShader( "emission", std::move( emission ) );
		adaptedNetwork->addConnection(
			{ { colorBuildHandle, "ColorOut" }, { emissionHandle, "Color" } }
		);

		ShaderPtr material = new Shader( "material/as_material_builder", "osl:surface" );
		InternedString materialHandle = adaptedNetwork->addShader( "material", std::move( material ) );
		adaptedNetwork->addConnection(
			{ { emissionHandle, "BSDF" }, { materialHandle, "BSDF" } }
		);
		adaptedNetwork->setOutput( materialHandle );
	}
	else if( firstOutput && firstOutput->type == TypeDesc::TypeVector )
	{
		adaptedNetwork = shaderNetwork->copy();
		ShaderPtr vectorSplit = new Shader( "vector/as_vector_split", "osl:shader" );
		InternedString vectorSplitHandle = adaptedNetwork->addShader( "vectorSplit", std::move( vectorSplit ) );
		adaptedNetwork->addConnection(
			{ { adaptedNetwork->getOutput().shader, firstOutput->name.string() }, { vectorSplitHandle, "Vector" } }
		);

		ShaderPtr colorBuild = new Shader( "color/as_color_build", "osl:shader" );
		InternedString colorBuildHandle = adaptedNetwork->addShader( "colorBuild", std::move( colorBuild ) );
		for( const auto &c : { make_pair( "X", "R" ), make_pair( "Y", "G" ), make_pair( "Z", "B" ) } )
		{
			adaptedNetwork->addConnection(
				{ { vectorSplitHandle, c.first }, { colorBuildHandle, c.second } }
			);
		}

		ShaderPtr emission = new Shader( "surface/as_emission_surface", "osl:shader" );
		InternedString emissionHandle = adaptedNetwork->addShader( "emission", std::move( emission ) );
		adaptedNetwork->addConnection(
			{ { colorBuildHandle, "ColorOut" }, { emissionHandle, "Color" } }
		);

		ShaderPtr material = new Shader( "material/as_material_builder", "osl:surface" );
		InternedString materialHandle = adaptedNetwork->addShader( "material", std::move( material ) );
		adaptedNetwork->addConnection(
			{ { emissionHandle, "BSDF" }, { materialHandle, "BSDF" } }
		);
		adaptedNetwork->setOutput( materialHandle );
	}
	else
	{
		// Shader has no output, or an output we can't map sensibly.
		// Make an "error" shader.
		adaptedNetwork = new ShaderNetwork;
		ShaderPtr emission = new Shader( "surface/as_emission_surface", "osl:shader" );
		emission->parameters()["Color"] = new Color3fData( Imath::Color3f( 1, 0, 0 ) );
		InternedString emissionHandle = adaptedNetwork->addShader( "emission", std::move( emission ) );

		ShaderPtr material = new Shader( "material/as_material_builder", "osl:surface" );
		InternedString materialHandle = adaptedNetwork->addShader( "material", std::move( material ) );
		adaptedNetwork->addConnection(
			{ { emissionHandle, "BSDF" }, { materialHandle, "BSDF" } }
		);
		adaptedNetwork->setOutput( materialHandle );
	}

	// Place the new network into the "osl:surface" attribute
	// and remove the "osl:shader" attribute.

	CompoundObjectPtr outputAttributes = new CompoundObject;
	outputAttributes->members() = inputAttributes->members(); // Shallow copy for speed - do not modify in place!
	outputAttributes->members()[g_oslSurfaceAttributeName] = adaptedNetwork;
	outputAttributes->members().erase( g_oslShaderAttributeName );

	return outputAttributes;
}
