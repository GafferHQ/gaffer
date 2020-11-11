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

#include "boost/python.hpp"

#include "PrimitivesBinding.h"

#include "Gaffer/StringPlug.h"

#include "GafferScene/Camera.h"
#include "GafferScene/ClippingPlane.h"
#include "GafferScene/CoordinateSystem.h"
#include "GafferScene/Cube.h"
#include "GafferScene/ExternalProcedural.h"
#include "GafferScene/Grid.h"
#include "GafferScene/Light.h"
#include "GafferScene/ObjectToScene.h"
#include "GafferScene/Plane.h"
#include "GafferScene/ShaderPlug.h"
#include "GafferScene/Sphere.h"
#include "GafferScene/Text.h"
#include "GafferScene/LightFilter.h"

#include "GafferBindings/DependencyNodeBinding.h"

using namespace std;
using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferScene;

namespace {

class LightSerialiser : public GafferBindings::NodeSerialiser
{

	std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, GafferBindings::Serialisation &serialisation ) const override
	{
		std::string defaultPC = GafferBindings::NodeSerialiser::postConstructor( graphComponent, identifier, serialisation );
		const GafferScene::Light *light = static_cast<const GafferScene::Light *>( graphComponent );

		// \todo - Remove this once old scripts have been converted
		// Before we start serialization, clean up any old scripts that might have dynamic parameters on lights
		// ( Now we create the parameters with a loadShader after the constructor, so they don't need to be dynamic )
		for( Plug::Iterator it( light->parametersPlug() ); !it.done(); ++it )
		{
			(*it)->setFlags( Gaffer::Plug::Dynamic, false );
		}

		// \todo - We should have a good way to access this on the base class - John is planning
		// refactor this setup so that lights contain a GafferScene::Shader, instead of implementing
		// loadShader themselves
		const StringPlug* shaderNamePlug = light->getChild<Gaffer::StringPlug>( "shaderName" );
		if( !shaderNamePlug )
		{
			shaderNamePlug = light->getChild<Gaffer::StringPlug>( "__shaderName" );
		}
		if( !shaderNamePlug )
		{
			shaderNamePlug = light->getChild<Gaffer::StringPlug>( "__model" );
		}
		if( !shaderNamePlug )
		{
			if( const GafferScene::Shader *shader = light->getChild<GafferScene::Shader>( "__shader" ) )
			{
				shaderNamePlug = shader->namePlug();
			}
		}

		const std::string shaderName = shaderNamePlug ? shaderNamePlug->getValue() : "";
		if( shaderName.size() )
		{
			return defaultPC + boost::str( boost::format( "%s.loadShader( \"%s\" )\n" ) % identifier % shaderName );
		}

		return defaultPC;
	}

};

} // namespace

namespace GafferSceneModule {

class LightFilterSerialiser : public GafferBindings::NodeSerialiser
{

	std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, GafferBindings::Serialisation &serialisation ) const override
	{
		std::string defaultPostConstructor = GafferBindings::NodeSerialiser::postConstructor( graphComponent, identifier, serialisation );

		const GafferScene::LightFilter *lightFilter = static_cast<const GafferScene::LightFilter *>( graphComponent );
		const std::string shaderName = lightFilter->shaderNode()->namePlug()->getValue();

		if( shaderName.size() )
		{
			return defaultPostConstructor + boost::str( boost::format( "%s.loadShader( \"%s\" )\n" ) % identifier % shaderName );
		}

		return defaultPostConstructor;
	}

};

} // namespace GafferSceneModule


void GafferSceneModule::bindPrimitives()
{

	GafferBindings::DependencyNodeClass<ObjectSource>();
	GafferBindings::DependencyNodeClass<Plane>();
	GafferBindings::DependencyNodeClass<Cube>();
	GafferBindings::DependencyNodeClass<Text>();
	GafferBindings::DependencyNodeClass<ObjectToScene>();

	{
		scope s = GafferBindings::DependencyNodeClass<Camera>();
		enum_<Camera::PerspectiveMode>( "PerspectiveMode" )
			.value( "FieldOfView", Camera::FieldOfView )
			.value( "ApertureFocalLength", Camera::ApertureFocalLength )
		;
	}

	GafferBindings::DependencyNodeClass<ClippingPlane>();
	GafferBindings::DependencyNodeClass<CoordinateSystem>();
	GafferBindings::DependencyNodeClass<ExternalProcedural>();
	GafferBindings::DependencyNodeClass<Grid>();
	GafferBindings::DependencyNodeClass<Light>();
	GafferBindings::Serialisation::registerSerialiser( Light::staticTypeId(), new LightSerialiser() );

	NodeClass<LightFilter>( nullptr, no_init )
		.def( "loadShader", &LightFilter::loadShader, ( boost::python::arg( "shaderName" ), boost::python::arg( "keepExistingValues" ) = false ) )
	;

	GafferBindings::Serialisation::registerSerialiser( LightFilter::staticTypeId(), new LightFilterSerialiser() );


	{
		scope s = GafferBindings::DependencyNodeClass<Sphere>();

		enum_<Sphere::Type>( "Type" )
			.value( "Primitive", Sphere::Primitive )
			.value( "Mesh", Sphere::Mesh )
		;
	}

}
