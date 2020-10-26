//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "GafferOSL/OSLLight.h"

#include "GafferOSL/OSLShader.h"

#include "GafferScene/Private/IECoreScenePreview/Geometry.h"
#include "GafferScene/Shader.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/DiskPrimitive.h"
#include "IECoreScene/SpherePrimitive.h"

#include "IECore/NullObject.h"

using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferOSL;

GAFFER_NODE_DEFINE_TYPE( OSLLight );

size_t OSLLight::g_firstPlugIndex = 0;

OSLLight::OSLLight( const std::string &name )
	:	GafferScene::Light( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	// \todo - now that shaderName is not serialized, it seems questionable whether it even needs to exist, or
	// whether we should just directly serialize shaderNode()->namePlug()  into the loadShader call.
	// For the moment, keeping shaderName around makes it easier to support deprecated scripts, which contain
	// a setValue on shaderName, and no loadShader
	addChild( new StringPlug( "shaderName", Plug::In, "", Plug::Default & ~Plug::Serialisable ) );
	addChild( new IntPlug( "shape", Plug::In, Disk, Disk, Geometry ) );
	addChild( new FloatPlug( "radius", Plug::In, 0.01, 0 ) );
	addChild( new StringPlug( "geometryType" ) );
	addChild( new Box3fPlug( "geometryBound", Plug::In, Box3f( V3f( -1 ), V3f( 1 ) ) ) );
	addChild( new CompoundDataPlug( "geometryParameters" ) );
	addChild( new CompoundDataPlug( "attributes" ) );

	addChild( new OSLShader( "__shader" ) );
	addChild( new ShaderPlug( "__shaderIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	/// \todo OSLShader could add this in it's constructor
	shaderNode()->addChild( new Plug( "out", Plug::Out ) );
	shaderNode()->namePlug()->setInput( shaderNamePlug() );
	shaderNode()->typePlug()->setValue( "osl:light" );
	shaderNode()->parametersPlug()->setFlags( Plug::AcceptsInputs, true );
	shaderNode()->parametersPlug()->setInput( parametersPlug() );

	shaderInPlug()->setInput( shaderNode()->outPlug() );
}

OSLLight::~OSLLight()
{
}

Gaffer::StringPlug *OSLLight::shaderNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *OSLLight::shaderNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *OSLLight::shapePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *OSLLight::shapePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::FloatPlug *OSLLight::radiusPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::FloatPlug *OSLLight::radiusPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *OSLLight::geometryTypePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *OSLLight::geometryTypePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::Box3fPlug *OSLLight::geometryBoundPlug()
{
	return getChild<Box3fPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::Box3fPlug *OSLLight::geometryBoundPlug() const
{
	return getChild<Box3fPlug>( g_firstPlugIndex + 4 );
}

Gaffer::CompoundDataPlug *OSLLight::geometryParametersPlug()
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::CompoundDataPlug *OSLLight::geometryParametersPlug() const
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex + 5 );
}

Gaffer::CompoundDataPlug *OSLLight::attributesPlug()
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::CompoundDataPlug *OSLLight::attributesPlug() const
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex + 6 );
}

OSLShader *OSLLight::shaderNode()
{
	return getChild<OSLShader>( g_firstPlugIndex + 7 );
}

const OSLShader *OSLLight::shaderNode() const
{
	return getChild<OSLShader>( g_firstPlugIndex + 7 );
}

GafferScene::ShaderPlug *OSLLight::shaderInPlug()
{
	return getChild<ShaderPlug>( g_firstPlugIndex + 8 );
}

const GafferScene::ShaderPlug *OSLLight::shaderInPlug() const
{
	return getChild<ShaderPlug>( g_firstPlugIndex + 8 );
}

void OSLLight::loadShader( const std::string &shaderName )
{
	shaderNode()->loadShader( shaderName );
	shaderNode()->typePlug()->setValue( "osl:light" );
}

void OSLLight::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	Light::affects( input, outputs );

	if(
		input == shapePlug() ||
		input == radiusPlug() ||
		input == geometryTypePlug() ||
		geometryBoundPlug()->isAncestorOf( input ) ||
		geometryParametersPlug()->isAncestorOf( input )
	)
	{
		outputs.push_back( sourcePlug() );
	}

	if(
		input == shaderInPlug() ||
		attributesPlug()->isAncestorOf( input )
	)
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}
}

void OSLLight::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	shapePlug()->hash( h );
	radiusPlug()->hash( h );
	geometryTypePlug()->hash( h );
	geometryBoundPlug()->hash( h );
	geometryParametersPlug()->hash( h );
}

IECore::ConstObjectPtr OSLLight::computeSource( const Gaffer::Context *context ) const
{
	switch( shapePlug()->getValue() )
	{
		case Disk :
			return new DiskPrimitive( radiusPlug()->getValue() );
		case Sphere :
			return new SpherePrimitive( radiusPlug()->getValue() );
		case Geometry :
		{
			CompoundDataPtr parameters = new CompoundData;
			geometryParametersPlug()->fillCompoundData( parameters->writable() );
			return new IECoreScenePreview::Geometry(
				geometryTypePlug()->getValue(),
				geometryBoundPlug()->getValue(),
				parameters
			);
		}
	}
	return NullObject::defaultNullObject();
}

void OSLLight::hashAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	Light::hashAttributes( path, context, parent, h );
	attributesPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr OSLLight::computeAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	IECore::CompoundObjectPtr result = new IECore::CompoundObject;
	result->members() = Light::computeAttributes( path, context, parent )->members();
	attributesPlug()->fillCompoundObject( result->members() );
	return result;
}

void OSLLight::hashLight( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h.append( shaderInPlug()->attributesHash() );
}

IECoreScene::ConstShaderNetworkPtr OSLLight::computeLight( const Gaffer::Context *context ) const
{
	IECore::ConstCompoundObjectPtr shaderAttributes = shaderInPlug()->attributes();
	return shaderAttributes->member<const IECoreScene::ShaderNetwork>( "osl:light" );
}

