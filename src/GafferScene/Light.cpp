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

#include "GafferScene/Light.h"

#include "GafferScene/SceneNode.h"

#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TransformPlug.h"

#include "IECoreScene/Shader.h"

#include "IECore/MessageHandler.h"
#include "IECore/NullObject.h"

using namespace Gaffer;
using namespace GafferScene;

static IECore::InternedString g_lightsSetName( "__lights" );
static IECore::InternedString g_defaultLightsSetName( "defaultLights" );

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Light );

size_t Light::g_firstPlugIndex = 0;

Light::Light( const std::string &name )
	:	ObjectSource( name, "light" )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new Plug( "parameters" ) );
	addChild( new BoolPlug( "defaultLight", Gaffer::Plug::Direction::In, true ) );

	Gaffer::CompoundDataPlug *visualiserAttr = new CompoundDataPlug( "visualiserAttributes" );

	FloatPlugPtr scaleValuePlug = new FloatPlug( "value", Gaffer::Plug::Direction::In, 1.0f, 0.01f );
	visualiserAttr->addChild( new Gaffer::NameValuePlug( "gl:visualiser:scale", scaleValuePlug, false, "scale" ) );

	IntPlugPtr maxResValuePlug = new IntPlug( "value", Gaffer::Plug::Direction::In, 512, 2, 2048 );
	visualiserAttr->addChild( new Gaffer::NameValuePlug( "gl:visualiser:maxTextureResolution", maxResValuePlug, false, "maxTextureResolution" ) );

	visualiserAttr->addChild( new Gaffer::NameValuePlug( "gl:visualiser:frustum", new IECore::StringData( "whenSelected" ), false, "frustum" ) );

	FloatPlugPtr frustumScaleValuePlug = new FloatPlug( "value", Gaffer::Plug::Direction::In, 1.0f, 0.01f );
	visualiserAttr->addChild( new Gaffer::NameValuePlug( "gl:light:frustumScale", frustumScaleValuePlug, false, "lightFrustumScale" ) );

	visualiserAttr->addChild( new Gaffer::NameValuePlug( "gl:light:drawingMode", new IECore::StringData( "texture" ), false, "lightDrawingMode" ) );

	addChild( visualiserAttr  );
}

Light::~Light()
{
}

Gaffer::Plug *Light::parametersPlug()
{
	return getChild<Plug>( g_firstPlugIndex );
}

const Gaffer::Plug *Light::parametersPlug() const
{
	return getChild<Plug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *Light::defaultLightPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *Light::defaultLightPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

Gaffer::CompoundDataPlug *Light::visualiserAttributesPlug()
{
	return getChild<Gaffer::CompoundDataPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::CompoundDataPlug *Light::visualiserAttributesPlug() const
{
	return getChild<Gaffer::CompoundDataPlug>( g_firstPlugIndex + 2 );
}

void Light::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ObjectSource::affects( input, outputs );

	if(
		parametersPlug()->isAncestorOf( input )
		|| visualiserAttributesPlug()->isAncestorOf( input )
	) {
		outputs.push_back( outPlug()->attributesPlug() );
	}

	if( input == defaultLightPlug() )
	{
		// \todo: Perhaps this is indicative of a hole in the ObjectSource API. In
		// theory the Light class has no responsibility towards the `setPlug()` since
		// that is meant to be dealt with in the ObjectSource base class. The
		// subclasses are meant to only worry about `hashStandardSetNames()` and
		// `computeStandardSetNames()`. We should maybe have a matching `virtual bool
		// affectsStandardSetNames( const Plug *input )` that subclasses implement
		// and is called in `ObjectSource::affects()`
		outputs.push_back( outPlug()->setNamesPlug() );
		outputs.push_back( outPlug()->setPlug() );
	}
}

void Light::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

IECore::ConstObjectPtr Light::computeSource( const Context *context ) const
{
	// The light node now creates a new location in the scene, but just assigns attributes to it,
	// and doesn't create an object here
	return IECore::NullObject::defaultNullObject();
}

void Light::hashAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	hashLight( context, h );
	visualiserAttributesPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr Light::computeAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	IECore::CompoundObjectPtr result = new IECore::CompoundObject;

	std::string lightAttribute = "light";

	IECoreScene::ConstShaderNetworkPtr lightShaders = computeLight( context );
	if( const IECoreScene::Shader *shader = lightShaders->outputShader() )
	{
		lightAttribute = shader->getType();
	}

	// As we output as const, then this just lets us get through the next few lines...
	result->members()[lightAttribute] = const_cast<IECoreScene::ShaderNetwork*>( lightShaders.get() );

	visualiserAttributesPlug()->fillCompoundObject( result->members() );

	return result;
}

void Light::hashStandardSetNames( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	defaultLightPlug()->hash( h );
}

IECore::ConstInternedStringVectorDataPtr Light::computeStandardSetNames() const
{
	IECore::InternedStringVectorDataPtr result = new IECore::InternedStringVectorData();
	result->writable().push_back( g_lightsSetName );

	if( defaultLightPlug()->getValue() )
	{
		result->writable().push_back( g_defaultLightsSetName );
	}

	return result;
}

void Light::hashBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashBound( path, context, parent, h );
	if( path.size() == 0 )
	{
		transformPlug()->hash( h );
	}
}

Imath::Box3f Light::computeBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	Imath::Box3f result = Imath::Box3f( Imath::V3f( -.5 ), Imath::V3f( .5 ) );
	if( path.size() == 0 )
	{
		result = Imath::transform( result, transformPlug()->matrix() );
	}
	return result;
}
