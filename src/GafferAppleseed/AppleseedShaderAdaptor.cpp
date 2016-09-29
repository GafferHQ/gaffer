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

#include "tbb/concurrent_hash_map.h"

#include "OSL/oslquery.h"

#include "IECore/Shader.h"

#include "Gaffer/Context.h"

#include "GafferScene/SceneProcessor.h"
#include "GafferScene/RendererAlgo.h"

#include "GafferAppleseed/AppleseedShaderAdaptor.h"

using namespace std;
using namespace OSL;
using namespace IECore;
using namespace GafferScene;
using namespace GafferAppleseed;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

IECore::InternedString g_oslShaderAttributeName( "osl:shader" );
IECore::InternedString g_oslSurfaceAttributeName( "osl:surface" );
IECore::InternedString g_handleParameterName( "__handle" );
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

	const ObjectVector *shaderNetwork = inputAttributes->member<const ObjectVector>( g_oslShaderAttributeName );
	if( !shaderNetwork || shaderNetwork->members().empty() )
	{
		return inputAttributes;
	}

	const Shader *rootShader = runTimeCast<const Shader>( shaderNetwork->members().back().get() );
	if( !rootShader )
	{
		return inputAttributes;
	}

	OSLQuery::Parameter *firstOutput = firstOutputParameter( rootShader->getName() );

	// Build an adapter network if we can.

	bool prependInputNetwork = true;
	vector<ShaderPtr> adapters;
	if( firstOutput && firstOutput->isclosure )
	{
		ShaderPtr material = new Shader( "material/as_material_builder", "osl:surface" );
		material->parameters()[g_bsdfParameterName] = new StringData( "link:adapterInputHandle." + firstOutput->name.string() );
		adapters.push_back( material );
	}
	else if( firstOutput && firstOutput->type == TypeDesc::TypeColor )
	{
		ShaderPtr emission = new Shader( "surface/as_emission_surface", "osl:shader" );
		emission->parameters()["Color"] = new StringData( "link:adapterInputHandle." + firstOutput->name.string() );
		emission->parameters()[g_handleParameterName] = new StringData( "adapterEmissionHandle" );

		ShaderPtr material = new Shader( "material/as_material_builder", "osl:surface" );
		material->parameters()[g_bsdfParameterName] = new StringData( "link:adapterEmissionHandle.BSDF" );

		adapters.push_back( emission );
		adapters.push_back( material );
	}
	else if( firstOutput && ( firstOutput->type == TypeDesc::TypeFloat || firstOutput->type == TypeDesc::TypeInt ) )
	{
		ShaderPtr colorBuild = new Shader( "color/as_color_build", "osl:shader" );
		StringDataPtr colorLink = new StringData( "link:adapterInputHandle." + firstOutput->name.string() );
		colorBuild->parameters()["R"] = colorLink;
		colorBuild->parameters()["G"] = colorLink;
		colorBuild->parameters()["B"] = colorLink;
		colorBuild->parameters()[g_handleParameterName] = new StringData( "adapterColorBuildHandle" );

		ShaderPtr emission = new Shader( "surface/as_emission_surface", "osl:shader" );
		emission->parameters()["Color"] = new StringData( "link:adapterColorBuildHandle.ColorOut" );
		emission->parameters()[g_handleParameterName] = new StringData( "adapterEmissionHandle" );

		ShaderPtr material = new Shader( "material/as_material_builder", "osl:surface" );
		material->parameters()[g_bsdfParameterName] = new StringData( "link:adapterEmissionHandle.BSDF" );

		adapters.push_back( colorBuild );
		adapters.push_back( emission );
		adapters.push_back( material );
	}
	else if( firstOutput && firstOutput->type == TypeDesc::TypeVector )
	{
		ShaderPtr vectorSplit = new Shader( "vector/as_vector_split", "osl:shader" );
		vectorSplit->parameters()["Vector"] = new StringData( "link:adapterInputHandle." + firstOutput->name.string() );
		vectorSplit->parameters()[g_handleParameterName] = new StringData( "adapterVectorSplit" );

		ShaderPtr colorBuild = new Shader( "color/as_color_build", "osl:shader" );
		colorBuild->parameters()["R"] = new StringData( "link:adapterVectorSplit.X" );
		colorBuild->parameters()["G"] = new StringData( "link:adapterVectorSplit.Y" );
		colorBuild->parameters()["B"] = new StringData( "link:adapterVectorSplit.Z" );
		colorBuild->parameters()[g_handleParameterName] = new StringData( "adapterColorBuildHandle" );

		ShaderPtr emission = new Shader( "surface/as_emission_surface", "osl:shader" );
		emission->parameters()["Color"] = new StringData( "link:adapterColorBuildHandle.ColorOut" );
		emission->parameters()[g_handleParameterName] = new StringData( "adapterEmissionHandle" );

		ShaderPtr material = new Shader( "material/as_material_builder", "osl:surface" );
		material->parameters()[g_bsdfParameterName] = new StringData( "link:adapterEmissionHandle.BSDF" );

		adapters.push_back( vectorSplit );
		adapters.push_back( colorBuild );
		adapters.push_back( emission );
		adapters.push_back( material );
	}
	else
	{
		// Shader has no output, or an output we can't map sensibly.
		// Make an "error" shader.
		ShaderPtr emission = new Shader( "surface/as_emission_surface", "osl:shader" );
		emission->parameters()["Color"] = new Color3fData( Imath::Color3f( 1, 0, 0 ) );
		emission->parameters()[g_handleParameterName] = new StringData( "adapterEmissionHandle" );

		ShaderPtr material = new Shader( "material/as_material_builder", "osl:surface" );
		material->parameters()[g_bsdfParameterName] = new StringData( "link:adapterEmissionHandle.BSDF" );

		adapters.push_back( emission );
		adapters.push_back( material );

		prependInputNetwork = false; // We don't need the original shaders at all
	}

	// Make a new network with the adapter network
	// appended onto the input network

	ObjectVectorPtr adaptedNetwork = new ObjectVector();

	if( prependInputNetwork )
	{
		adaptedNetwork->members() = shaderNetwork->members(); // Shallow copy for speed - do not modify in place!

		ShaderPtr rootShaderCopy = rootShader->copy();
		rootShaderCopy->parameters()[g_handleParameterName] = new StringData( "adapterInputHandle" );;
		adaptedNetwork->members().back() = rootShaderCopy;
	}

	std::copy( adapters.begin(), adapters.end(), back_inserter( adaptedNetwork->members() ) );

	// Place the new network into the "osl:surface" attribute
	// and remove the "osl:shader" attribute.

	CompoundObjectPtr outputAttributes = new CompoundObject;
	outputAttributes->members() = inputAttributes->members(); // Shallow copy for speed - do not modify in place!
	outputAttributes->members()[g_oslSurfaceAttributeName] = adaptedNetwork;
	outputAttributes->members().erase( g_oslShaderAttributeName );

	return outputAttributes;
}
