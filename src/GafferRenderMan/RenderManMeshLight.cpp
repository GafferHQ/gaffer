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

#include "GafferRenderMan/RenderManShader.h"

#include "GafferScene/CustomAttributes.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferRenderMan;

namespace
{

const ConstCompoundObjectPtr g_hiddenVisibilityAttributes = [] {

	const CompoundObjectPtr result = new CompoundObject;
	result->members()["ri:visibility:indirect"] = new BoolData( false );
	result->members()["ri:visibility:transmission"] = new BoolData( false );
	return result;

} ();

} // namespace

GAFFER_NODE_DEFINE_TYPE( RenderManMeshLight );

RenderManMeshLight::RenderManMeshLight( const std::string &name )
	:	GafferScene::MeshLight(
			name,
			[] { RenderManShaderPtr shader = new RenderManShader; shader->loadShader( "PxrMeshLight" ); return shader; } ()
		)
{

	// Hide the objects to everything except camera rays, since that seems a
	// reasonable default behaviour for a mesh light. The user can turn this
	// back on with a RenderManAttributes node, in which case the surface shader
	// is used for ray hits.

	customAttributes()->extraAttributesPlug()->setValue( g_hiddenVisibilityAttributes );

	// Promote a camera visibility plug, since that is more likely to be used
	// than the others.
	/// \todo We could promote as OptionalValuePlug to avoid exposing the
	/// `name` plug unnecessarily.

	NameValuePlugPtr internalCameraVisibilityPlug = new NameValuePlug(
		"ri:visibility:camera", new BoolPlug( "value", Plug::In, true ), false, "cameraVisibility"
	);
	customAttributes()->attributesPlug()->addChild( internalCameraVisibilityPlug );
	PlugPtr cameraVisibilityPlug = internalCameraVisibilityPlug->createCounterpart( "cameraVisibility", Plug::In );
	addChild( cameraVisibilityPlug );
	internalCameraVisibilityPlug->setInput( cameraVisibilityPlug );
}

RenderManMeshLight::~RenderManMeshLight()
{
}
