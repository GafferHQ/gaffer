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

#include "GafferArnold/ArnoldMeshLight.h"

#include "GafferArnold/ArnoldShader.h"

#include "GafferScene/CustomAttributes.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferArnold;

namespace
{

const ConstCompoundObjectPtr g_hiddenVisibilityAttributes = [] {

	const std::vector<std::string> names = {
		"ai:visibility:shadow",
		"ai:visibility:diffuse_reflect", "ai:visibility:specular_reflect",
		"ai:visibility:diffuse_transmit", "ai:visibility:specular_transmit",
		"ai:visibility:volume", "ai:visibility:subsurface"
	};

	const CompoundObjectPtr result = new CompoundObject;
	for( const auto &name : names )
	{
		result->members()[name] = new BoolData( false );
	}
	return result;

} ();

} // namespace

GAFFER_NODE_DEFINE_TYPE( ArnoldMeshLight );

ArnoldMeshLight::ArnoldMeshLight( const std::string &name )
	:	GafferScene::MeshLight(
			name,
			[] { ArnoldShaderPtr shader = new ArnoldShader; shader->loadShader( "mesh_light" ); return shader; } ()
		)
{

	// Hide the object from the majority of ray types, since we don't want to
	// add the poor sampling of the object on top of the nice sampling of the
	// light.

	customAttributes()->extraAttributesPlug()->setValue( g_hiddenVisibilityAttributes );

	// The only visibility option we don't turn off is camera visibility
	// - instead we promote so the user can decide whether or not the mesh
	// should be visible in the render.
	/// \todo We could promote as OptionalValuePlug to avoid exposing the
	/// `name` plug unnecessarily.

	NameValuePlugPtr internalCameraVisibilityPlug = new NameValuePlug(
		"ai:visibility:camera", new BoolPlug( "value", Plug::In, true ), false, "cameraVisibility"
	);
	customAttributes()->attributesPlug()->addChild( internalCameraVisibilityPlug );
	PlugPtr cameraVisibilityPlug = internalCameraVisibilityPlug->createCounterpart( "cameraVisibility", Plug::In );
	addChild( cameraVisibilityPlug );
	internalCameraVisibilityPlug->setInput( cameraVisibilityPlug );
}

ArnoldMeshLight::~ArnoldMeshLight()
{
}
