//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, John Haddon. All rights reserved.
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

#pragma once

#include "GafferSceneUI/Export.h"
#include "GafferScene/Private/IECoreGLPreview/LightVisualiser.h"

#include "IECoreGL/Group.h"

#include "IECore/SimpleTypedData.h"


namespace GafferSceneUI
{

/// Class for performing standard visualisations of lights,
/// by mapping shader parameters to features of the visualisation.
/// This also provides several protected utility methods for
/// making standard visualisations, so is suitable for use as
/// a base class for custom light visualisers.
class GAFFERSCENEUI_API StandardLightVisualiser : public IECoreGLPreview::LightVisualiser
{

	public :

		IE_CORE_DECLAREMEMBERPTR( StandardLightVisualiser )

		StandardLightVisualiser();
		~StandardLightVisualiser() override;

		IECoreGLPreview::Visualisations visualise( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *shaderNetwork, const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const override;

		static void spotlightParameters( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *shaderNetwork, float &innerAngle, float &outerAngle, float &radius, float &lensRadius );

		// Visualisers for specific renderers can register a function with
		// this signature to provide textures for area-based lights.
		//
		// It should return one of :
		//  - nullptr : No texture applicable
		//  - StringData : The file path of a texture.
		//  - CompoundData : An image representation of the texture data, as
		//      supported by IECoreGL::ToGLTextureConverter.

		using SurfaceTexture = std::function< IECore::DataPtr (
			const IECore::InternedString &attributeName,
			const IECoreScene::ShaderNetwork *shaderNetwork,
			const IECore::CompoundObject *attributes,
			int maxTextureResolution
		) >;

		// Registers a `SurfaceTexture` function to be used when visualising
		// lights. The first first non-nullptr value returned from a registered
		// function will be used as the texture. If no texture data is found,
		// `surfaceTexture` will look for a string parameter registered as the
		// "textureNameParameter" metadata value for the supplied shader
		// network's output shader.
		static void registerSurfaceTexture( SurfaceTexture texture );

		// Convenience class to allow static registration of surface texture functions.
		// e.g. `static SurfaceTextureRegistration g_texture( surfaceTextureFunction )`.
		struct SurfaceTextureRegistration
		{
			SurfaceTextureRegistration( SurfaceTexture texture )
			{
				registerSurfaceTexture( texture );
			}
		};

	private :

		IECore::DataPtr surfaceTexture( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *shaderNetwork, const IECore::CompoundObject *attributes, int maxTextureResolution ) const;

		static LightVisualiser::LightVisualiserDescription<StandardLightVisualiser> g_description;

};

IE_CORE_DECLAREPTR( StandardLightVisualiser )

} // namespace GafferSceneUI
