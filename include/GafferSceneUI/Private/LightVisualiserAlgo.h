//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Cinesite VFX Ltd. nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#pragma once

#include "GafferSceneUI/Export.h"

#include "IECoreGL/Group.h"

#include "IECore/SimpleTypedData.h"

namespace GafferSceneUI::Private::LightVisualiserAlgo
{

/// Returns an OpenGL renderable wireframe ray of unit length.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr ray( bool muted = false );

/// Returns an OpenGL renderable set of wireframe rays radiating from a center point.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr pointRays( float radius = 0, bool muted = false );

/// Returns an OpenGL renderable set of parallel wireframe rays.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr distantRays( bool muted = false );

/// Returns an OpenGL renderable pair of wireframe frustums.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr spotlightCone( float innerAngle, float outerAngle, float lensRadius, float length = 1.0f, float lineWidthScale = 1.0f, bool muted = false );

/// Returns an OpenGL renderable wireframe point.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr pointShape( float radius, bool muted = false );

/// Returns an OpenGL renderable wireframe rectangle with color according to the `mute` state.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr quadWireframe( const Imath::V2f &size, bool muted = false );

/// Returns an OpenGL renderable solid rectangle with optional texture map. If `textureData` is `nullptr`,
/// a solid color of `fallbackColor` will be used. `tint`, `saturation` and `gamma` are only applied to
/// the texture map, if present. The texture coordinates of the quad are transformed by `uvOrientation`.
/// `textureData` should be as per return type of `StandardLightVisualiser::surfaceTexture()`.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr quadSurface(
	const Imath::V2f &size, IECore::ConstDataPtr textureData, const Imath::Color3f &tint,
	int textureMaxResolution, const Imath::Color3f &fallbackColor, const Imath::M33f &uvOrientation
);

/// Returns an OpenGL renderable wireframe rectangle with outer hatching.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr quadPortal( const Imath::V2f &size, float hatchingScale = 1.0f, bool muted = false );

/// Returns an OpenGL renderable set of wireframe circles, one per axis for `true` values of `axisRings`.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr sphereWireframe(
	float radius, const Imath::Vec3<bool> &axisRings, float lineWidthScale, const Imath::V3f &center, bool muted
);

/// Returns an OpenGL renderable simple solid color visualisation.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr colorIndicator( const Imath::Color3f &color );

/// Returns an OpenGL renderable single-sided solid sphere with normals pointing inward so the far
/// side of the sphere is visible. If `textureData` is `nullptr`, a solid color of `fallbackColor`
/// will be used. `tint`, `saturation` and `gamma` are only applied to the texture map, if present.
/// `textureData` should be as per return type of `StandardLightVisualiser::surfaceTexture()`.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr environmentSphereSurface(
	IECore::ConstDataPtr textureData, const Imath::Color3f &tint,
	const int maxTextureResolution, const Imath::Color3f &fallbackColor
);

/// Returns an OpenGL renderable circle wireframe.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr diskWireframe( float radius, bool muted );

/// Returns an OpenGL renderable solid circle. If `textureData` is `nullptr`, a solid
/// color of `fallbackColor` will be used. `tint`, `saturation` and `gamma` are only
/// applied to the texture map, if present. `textureData` should be as per return type
/// of `StandardLightVisualiser::surfaceTexture()`.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr diskSurface(
	float radius, IECore::ConstDataPtr textureData, const Imath::Color3f &tint,
	int maxTextureResolution, const Imath::Color3f &fallbackColor
);

/// Returns an OpenGL renderable set of wireframe arrows pointing away from the center
/// of the cylinder.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr cylinderRays( float radius, bool muted );

/// Returns an OpenGL renderable wireframe cylinder.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr cylinderWireframe( float radius, float length, bool muted );

/// Returns an OpenGL renderable solid cylinder, with end caps.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr cylinderSurface( float radius, float length, const Imath::Color3f &color );

/// Adds a wireframe arrow to the given point vectors.
GAFFERSCENEUI_API void addRay( const Imath::V3f &start, const Imath::V3f &end, std::vector<int> &vertsPerCurve, std::vector<Imath::V3f> &p, float arrowScale = 0.05f );

/// Adds wireframe arrows diverging by 45 degrees as spread approaches 1.
GAFFERSCENEUI_API void addAreaSpread( float spread, std::vector<int> &vertsPerCurve, std::vector<Imath::V3f> &p );

/// Returns the color to use for wireframe lights for a given `muted` state.
GAFFERSCENEUI_API Imath::Color3f lightWireframeColor( const bool muted );
GAFFERSCENEUI_API Imath::Color4f lightWireframeColor4( const bool muted );

}  // namespace GafferSceneUI::Private::LightVisualiserAlgo
