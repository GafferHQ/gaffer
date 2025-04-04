//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/LightFilter.h"

#include "GafferScene/SceneNode.h"
#include "GafferScene/ShaderPlug.h"

#include "Gaffer/PlugAlgo.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TransformPlug.h"

#include "IECoreScene/Shader.h"
#include "IECoreScene/ShaderNetwork.h"

#include "IECore/MessageHandler.h"
#include "IECore/NullObject.h"

using namespace Gaffer;
using namespace GafferScene;

static IECore::InternedString g_lightFiltersSetName( "__lightFilters" );
static IECore::InternedString g_filteredLightsAttributeName( "filteredLights" );

GAFFER_NODE_DEFINE_TYPE( LightFilter );

size_t LightFilter::g_firstPlugIndex = 0;

LightFilter::LightFilter( GafferScene::ShaderPtr shader, const std::string &name )
	:	ObjectSource( name, "lightFilter" )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	shader->setName( "__shader" );
	addChild( shader );
	addChild( new StringPlug( "filteredLights" ) );
	addChild( new Plug( "parameters" ) );
	addChild( new ShaderPlug( "__shaderIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	shaderNode()->parametersPlug()->setFlags( Plug::AcceptsInputs, true );
	shaderNode()->parametersPlug()->setInput( parametersPlug() );
}

LightFilter::~LightFilter()
{
}

void LightFilter::loadShader( const std::string &shaderName, bool keepExistingValues )
{
	shaderNode()->loadShader( shaderName, keepExistingValues );
	shaderPlug()->setInput( shaderNode()->outPlug() );
	/// \todo We don't really want an attribute suffix for _any_ light filters,
	/// but historically we had one, so for now we are preserving that behaviour
	/// for all but the new RenderManLightFilter. We should remove the suffix
	/// and update the Arnold backend to use `ai:lightFilter` attributes directly.
	/// We should also remove the fallback check for the "filter" suffix in
	/// `LightFilterUI.py`.
	if( strcmp( typeName(), "GafferRenderMan::RenderManLightFilter" ) )
	{
		shaderNode()->attributeSuffixPlug()->setValue( "filter" );
	}
}

GafferScene::Shader *LightFilter::shaderNode()
{
	return getChild<GafferScene::Shader>( g_firstPlugIndex );
}

const GafferScene::Shader *LightFilter::shaderNode() const
{
	return getChild<GafferScene::Shader>( g_firstPlugIndex );
}

StringPlug *LightFilter::filteredLightsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const StringPlug *LightFilter::filteredLightsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::Plug *LightFilter::parametersPlug()
{
	return getChild<Plug>( g_firstPlugIndex + 2 );
}

const Gaffer::Plug *LightFilter::parametersPlug() const
{
	return getChild<Plug>( g_firstPlugIndex + 2 );
}

ShaderPlug *LightFilter::shaderPlug()
{
	return getChild<ShaderPlug>( g_firstPlugIndex + 3 );
}

const ShaderPlug *LightFilter::shaderPlug() const
{
	return getChild<ShaderPlug>( g_firstPlugIndex + 3 );
}

void LightFilter::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ObjectSource::affects( input, outputs );

	if( input == shaderPlug() || input == filteredLightsPlug() )
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}
}

void LightFilter::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

IECore::ConstObjectPtr LightFilter::computeSource( const Context *context ) const
{
	// The light filter node creates a new location in the scene, but just assigns attributes to it,
	// and doesn't create an object here
	return IECore::NullObject::defaultNullObject();
}

void LightFilter::hashAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	// We must call the base class before appending to the hash, but our direct
	// base class (ObjectSource) is set up with a hardcoded hash suitable only
	// for outputting empty attributes. Call directly to our SceneNode ancestor instead.
	SceneNode::hashAttributes( path, context, parent, h );

	h.append( shaderPlug()->attributesHash() );
	filteredLightsPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr LightFilter::computeAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	IECore::CompoundObjectPtr result = new IECore::CompoundObject;

	result->members() = shaderPlug()->attributes()->members();

	const std::string &filteredLights = filteredLightsPlug()->getValue();
	if( !filteredLights.empty() )
	{
		result->members()[g_filteredLightsAttributeName] = new IECore::StringData( filteredLights );
	}

	return result;
}

void LightFilter::hashStandardSetNames( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	// nothing to do here.
}

IECore::ConstInternedStringVectorDataPtr LightFilter::computeStandardSetNames() const
{
	IECore::InternedStringVectorDataPtr result = new IECore::InternedStringVectorData();
	result->writable().push_back( g_lightFiltersSetName );

	return result;
}

void LightFilter::hashBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashBound( path, context, parent, h );

	if( path.size() == 0 )
	{
		transformPlug()->hash( h );
	}
}

Imath::Box3f LightFilter::computeBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	Imath::Box3f result = Imath::Box3f( Imath::V3f( -.5 ), Imath::V3f( .5 ) );

	if( path.size() == 0 )
	{
		result = Imath::transform( result, transformPlug()->matrix() );
	}

	return result;
}
