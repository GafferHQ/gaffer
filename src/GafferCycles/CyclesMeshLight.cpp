//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Alex Fuller. All rights reserved.
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

#include "GafferCycles/CyclesMeshLight.h"

#include "GafferCycles/CyclesAttributes.h"
#include "GafferCycles/CyclesShader.h"

#include "GafferScene/Set.h"
#include "GafferScene/ShaderAssignment.h"

#include "Gaffer/StringPlug.h"
#include "Gaffer/Switch.h"

#include "boost/algorithm/string/predicate.hpp"

using namespace Gaffer;
using namespace GafferScene;
using namespace GafferCycles;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( CyclesMeshLight );

CyclesMeshLight::CyclesMeshLight( const std::string &name )
	:	GafferScene::FilteredSceneProcessor( name, IECore::PathMatcher::NoMatch )
{

	CyclesAttributesPtr attributes = new CyclesAttributes( "__attributes" );
	attributes->inPlug()->setInput( inPlug() );
	attributes->filterPlug()->setInput( filterPlug() );
	addChild( attributes );

	// Visibility flags

	for( NameValuePlug::Iterator it( attributes->attributesPlug() ); !it.done(); ++it )
	{
		if( boost::ends_with( (*it)->getName().string(), "Visibility" ) )
		{
			PlugPtr plug = (*it)->createCounterpart( (*it)->getName(), Plug::In );
			addChild( plug );
			(*it)->setInput( plug );
		}
	}

	// MIS

	Plug *internalMisPlug = attributes->attributesPlug()->getChild<Plug>( "useMis" );
	PlugPtr misPlug = internalMisPlug->createCounterpart( "useMis", Plug::In );
	addChild( misPlug );
	internalMisPlug->setInput( misPlug );

	// Light-Group

	Plug *internalLightGroupPlug = attributes->attributesPlug()->getChild<Plug>( "lightGroup" );
	PlugPtr lightGroupPlug = internalLightGroupPlug->createCounterpart( "lightGroup", Plug::In );
	addChild( lightGroupPlug );
	internalLightGroupPlug->setInput( lightGroupPlug );

	// Shader node. This loads the Cycles emission shader.

	CyclesShaderPtr shader = new CyclesShader( "__shader" );
	shader->loadShader( "emission" );
	addChild( shader );

	PlugPtr parametersPlug = shader->parametersPlug()->createCounterpart( "parameters", Plug::In );
	addChild( parametersPlug );
	for( Plug::Iterator srcIt( parametersPlug.get() ), dstIt( shader->parametersPlug() ); !srcIt.done(); ++srcIt, ++dstIt )
	{
		(*dstIt)->setInput( *srcIt );
		// We don't need the parameters to be dynamic, because we create the
		// plugs in our constructor when calling `loadShader()`.
		(*srcIt)->setFlags( Plug::Dynamic, false );
	}

	// ShaderAssignment node. This assigns the mesh_light shader
	// to the objects chosen by the filter.

	ShaderAssignmentPtr shaderAssignment = new ShaderAssignment( "__shaderAssignment" );
	shaderAssignment->inPlug()->setInput( attributes->outPlug() );
	shaderAssignment->filterPlug()->setInput( filterPlug() );
	shaderAssignment->shaderPlug()->setInput( shader->outPlug() );
	addChild( shaderAssignment );

	// Default lights Set node.

	BoolPlugPtr defaultLightPlug = new BoolPlug( "defaultLight", Plug::In, true );
	addChild( defaultLightPlug );

	SetPtr defaultLightsSet = new Set( "__defaultLightsSet" );
	defaultLightsSet->inPlug()->setInput( shaderAssignment->outPlug() );
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

CyclesMeshLight::~CyclesMeshLight()
{
}
