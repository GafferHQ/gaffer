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

/// Returns an OpenGL renderable solid point
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr pointSurface( float radius, const Imath::Color3f &color );

/// Returns an OpenGL renderable wireframe rectangle with rounded corners and color according to the `mute` state.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr roundedQuadWireframe( const Imath::V2f &size, const Imath::V2f &radii, float lineWidthScale, bool muted = false );

/// Returns an OpenGL renderable solid rectangle with optional rounded corners and texture map. If `textureData`
/// is `nullptr`, a solid color of `fallbackColor` will be used. `tint`, is applied to both the texture map and
/// fallback color. `saturation` and `gamma` are only applied to the texture map, if present. The texture
/// coordinates of the quad are transformed by `uvOrientation`.
/// `textureData` should be as per return type of `StandardLightVisualiser::surfaceTexture()`.

/// \todo Remove shading related parameters like `tint` and `saturation` and return only a solid renderable
/// primitive. Display of texture maps, especially modifications such as color adjustments, could easily be
/// renderer-specific, so it should be the job of the visualiser implementations to decide how to shade lights.
/// This applies to the other `*Surface` methods as well.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr roundedQuadSurface(
	const Imath::V2f &size, const Imath::V2f &radii, IECore::ConstDataPtr textureData, const Imath::Color3f &tint, const float saturation,
	const Imath::Color3f &gamma, int textureMaxResolution, const Imath::Color3f &fallbackColor, const Imath::M33f &uvOrientation
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
/// will be used. `tint`, is applied to both the texture map and fallback color. `saturation` and
/// `gamma` are only applied to the texture map, if present.
/// `textureData` should be as per return type of `StandardLightVisualiser::surfaceTexture()`.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr environmentSphereSurface(
	IECore::ConstDataPtr textureData, const Imath::Color3f &tint, const float saturation,
	const Imath::Color3f &gamma, const int maxTextureResolution, const Imath::Color3f &fallbackColor
);

/// Returns an OpenGL renderable circle wireframe.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr diskWireframe( float radius, float lineWidthScale, bool muted );

/// Returns an OpenGL renderable solid circle. If `textureData` is `nullptr`, a solid
/// color of `fallbackColor` will be used. `tint`, is applied to both the texture map and fallback
/// color. `saturation` and `gamma` are only applied to the texture map, if present.
/// `textureData` should be as per return type of `StandardLightVisualiser::surfaceTexture()`.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr diskSurface(
	float radius, IECore::ConstDataPtr textureData, const Imath::Color3f &tint, const float saturation,
	const Imath::Color3f &gamma, int maxTextureResolution, const Imath::Color3f &fallbackColor
);

/// Returns an OpenGL renderable set of wireframe arrows pointing away from the center
/// of the cylinder.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr cylinderRays( float radius, bool muted );

/// Returns an OpenGL renderable wireframe cylinder.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr cylinderWireframe( float radius, float length, float lineWidthScale, bool muted );

/// Returns an OpenGL renderable solid cylinder, with end caps.
GAFFERSCENEUI_API IECoreGL::ConstRenderablePtr cylinderSurface( float radius, float length, const Imath::Color3f &color );

/// Adds a wireframe arrow to the given point vectors.
GAFFERSCENEUI_API void addRay( const Imath::V3f &start, const Imath::V3f &end, std::vector<int> &vertsPerCurve, std::vector<Imath::V3f> &p, float arrowScale = 0.05f );

/// Adds wireframe arrows diverging by 45 degrees as spread approaches 1.
GAFFERSCENEUI_API void addAreaSpread( float spread, std::vector<int> &vertsPerCurve, std::vector<Imath::V3f> &p );

/// Returns the color to use for wireframe lights for a given `muted` state.
GAFFERSCENEUI_API Imath::Color3f lightWireframeColor( const bool muted );
GAFFERSCENEUI_API Imath::Color4f lightWireframeColor4( const bool muted );

/// Adds the necessary OpenGL state to `group` to draw its contents as a wireframe.
GAFFERSCENEUI_API void addWireframeCurveState( IECoreGL::Group *group, const float lineWidthScale = 1.0f );

/// Adds a constant color OpenGL shader to `group`. `aimType` can be one of :
/// -1 : The default vertex shader is used.
/// 0 : A vertex shader is bound to align points such that the object-space Z
/// coordinates are not changed and the X an Y axes are facing the camera.
/// 1 : A vertex shader is bound to align the points in camera-space.

/// \todo Should this be up to the individual implementations to manage, as we want to do with the
/// `*Surface` methods? The `aimType` functionality is nice to have shared, but could possibly be
/// made into a function that can be called by implementation shaders.
GAFFERSCENEUI_API void addConstantShader( IECoreGL::Group *group, const Imath::Color3f &tint, int aimType = -1 );

}  // namespace GafferSceneUI::Private::LightVisualiserAlgo
