//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferRenderMan/RenderManMeshLight.h"

#include "GafferRenderMan/RenderManAttributes.h"
#include "GafferRenderMan/RenderManShader.h"

#include "GafferScene/Set.h"
#include "GafferScene/ShaderAssignment.h"

#include "Gaffer/StringPlug.h"
#include "Gaffer/Switch.h"

using namespace Gaffer;
using namespace GafferScene;
using namespace GafferRenderMan;

GAFFER_NODE_DEFINE_TYPE( RenderManMeshLight );

RenderManMeshLight::RenderManMeshLight( const std::string &name )
	:	GafferScene::FilteredSceneProcessor( name, IECore::PathMatcher::NoMatch )
{

	// RenderManAttributes node. We use this to hide the objects to everything
	// except camera rays, since that seems a reasonable default behaviour for
	// a mesh light. The user can turn this back on with a RenderManAttributes
	// node, in which case the surface shader is used for ray hits.

	RenderManAttributesPtr attributes = new RenderManAttributes( "__attributes" );
	attributes->inPlug()->setInput( inPlug() );
	attributes->filterPlug()->setInput( filterPlug() );
	for( const auto &attributeName : { "ri:visibility:indirect", "ri:visibility:transmission" } )
	{
		auto plug = attributes->attributesPlug()->getChild<NameValuePlug>( attributeName );
		plug->enabledPlug()->setValue( true );
		plug->valuePlug<IntPlug>()->setValue( 0 );
	}

	addChild( attributes );

	// Promote the camera visibility plug, since that is more likely to be used
	// than the others.

	Plug *internalCameraVisibilityPlug = attributes->attributesPlug()->getChild<Plug>( "ri:visibility:camera" );
	PlugPtr cameraVisibilityPlug = internalCameraVisibilityPlug->createCounterpart( "cameraVisibility", Plug::In );
	addChild( cameraVisibilityPlug );
	internalCameraVisibilityPlug->setInput( cameraVisibilityPlug );

	// Shader node. This loads the PxrMeshLight shader.

	RenderManShaderPtr shader = new RenderManShader( "__shader" );
	shader->loadShader( "PxrMeshLight" );
	addChild( shader );

	PlugPtr parametersPlug = shader->parametersPlug()->createCounterpart( "parameters", Plug::In );
	addChild( parametersPlug );
	for( Plug::Iterator srcIt( parametersPlug.get() ), dstIt( shader->parametersPlug() ); !srcIt.done(); ++srcIt, ++dstIt )
	{
		(*dstIt)->setInput( *srcIt );
	}

	// ShaderAssignment node. This assigns the PxrMeshLight shader
	// to the objects chosen by the filter.

	ShaderAssignmentPtr shaderAssignment = new ShaderAssignment( "__shaderAssignment" );
	shaderAssignment->inPlug()->setInput( attributes->outPlug() );
	shaderAssignment->filterPlug()->setInput( filterPlug() );
	shaderAssignment->shaderPlug()->setInput( shader->outPlug() );
	addChild( shaderAssignment );

	// Set node. This adds the objects into the __lights set,
	// so they will be output correctly to the renderer.

	SetPtr set = new Set( "__set" );
	set->inPlug()->setInput( shaderAssignment->outPlug() );
	set->filterPlug()->setInput( filterPlug() );
	set->namePlug()->setValue( "__lights" );
	set->modePlug()->setValue( Set::Add );
	addChild( set );

	// Default lights Set node.

	BoolPlugPtr defaultLightPlug = new BoolPlug( "defaultLight", Plug::In, true );
	addChild( defaultLightPlug );

	SetPtr defaultLightsSet = new Set( "__defaultLightsSet" );
	defaultLightsSet->inPlug()->setInput( set->outPlug() );
	defaultLightsSet->filterPlug()->setInput( filterPlug() );
	defaultLightsSet->enabledPlug()->setInput( defaultLightPlug.get() );
	defaultLightsSet->namePlug()->setValue( "defaultLights" );
	defaultLightsSet->modePlug()->setValue( Set::Add );
	addChild( defaultLightsSet );

	// Switch for enabling/disabling

	SwitchPtr enabledSwitch = new Switch( "__switch" );
	enabledSwitch->setup( inPlug() );
	enabledSwitch->inPlugs()->getChild<ScenePlug>( 0 )->setInput( inPlug() );
	enabledSwitch->inPlugs()->getChild<ScenePlug>( 1 )->setInput( defaultLightsSet->outPlug() );
	enabledSwitch->indexPlug()->setValue( 1 );
	enabledSwitch->enabledPlug()->setInput( enabledPlug() );
	addChild( enabledSwitch );

	outPlug()->setInput( enabledSwitch->outPlug() );
	// We don't need to serialise the connection because we make
	// it upon construction.
	/// \todo Can we just do this in the SceneProcessor base class?
	outPlug()->setFlags( Plug::Serialisable, false );
}

RenderManMeshLight::~RenderManMeshLight()
{
}
