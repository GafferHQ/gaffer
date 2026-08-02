//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Lucien Fostier. All rights reserved.
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
//     * Neither the name of Image Engine Design nor the names of any
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
//  NONINFRINGEMENT) OR OTHERWISE ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

#pragma once

#include "GafferOFX/Export.h"
#include "GafferOFX/EffectImageInstance.h"

#include "ofxPixels.h"

#include "HostSupport/ofxhClip.h"

#include "IECore/BoxOps.h"
#include "ImathBox.h"

#include <map>
#include <mutex>

namespace GafferOFX
{
	class ClipInstance;

	class Image : public OFX::Host::ImageEffect::Image
	{
		protected :

			// Raw float buffer: RGBA-interleaved (4 floats/pixel) for
			// chromatic clips, single-channel for Alpha (mask) clips.
			std::unique_ptr<float[]> m_data;
			int m_components = 4;

		public :

			explicit Image( ClipInstance &clip, OfxTime t, int view = 0, const OfxRectI *bounds = nullptr );
			OfxRGBAColourF* pixel( int x, int y ) const;
			~Image();
	};

	class ClipInstance : public OFX::Host::ImageEffect::ClipInstance
	{
		protected :

			GafferOFX::EffectImageInstance*	m_effect;
			std::string	m_name;
			std::string m_plugName;

			// GL output texture ID for OpenGL rendering
			unsigned int m_outputTexture = 0;

			// Cached source input texture for GL rendering (avoids glGenTextures per render)
			unsigned int m_inputTexture = 0;
			int m_inputTexW = 0;
			int m_inputTexH = 0;
			/// GLContextManager generation at last upload; stale after a context rebuild.
			int m_inputTextureGeneration = 0;

		public :

			ClipInstance(
				GafferOFX::EffectImageInstance* effect,
				OFX::Host::ImageEffect::ClipDescriptor* desc
			);

			 ~ClipInstance();
			Image* getOutputImage();

			void setPlugName( const std::string &name ) { m_plugName = name; }
			const std::string &plugName() const { return m_plugName; }

			///    - kOfxBitDepthFloat
			const std::string &getUnmappedBitDepth() const override;

			/// Get the Raw Unmapped Components from the host
			///
			/// \returns
			///     - kOfxImageComponentNone (implying a clip is unconnected, not valid for an image)
			///     - kOfxImageComponentRGBA
			///     - kOfxImageComponentAlpha
			 const std::string &getUnmappedComponents() const override;

			//  kOfxImagePreMultiplied - the image is premultiplied by it's alpha
			 const std::string &getPremult() const override;

			// Pixel Aspect Ratio -
			//
			//  The pixel aspect ratio of a clip or image.
			 double getAspectRatio() const override;

			// Frame Rate -
			//
			//  The frame rate of a clip or instance's project.
			 double getFrameRate() const override;

			// Frame Range (startFrame, endFrame) -
			//
			//  The frame range over which a clip has images.
			 void getFrameRange(double &startFrame, double &endFrame) const override;

			///  - kOfxImageFieldNone - the clip material is unfielded
			 const std::string &getFieldOrder() const override;

			// Connected -
			//
			//  Says whether the clip is actually connected at the moment.
			 bool getConnected() const override;

			// Unmapped Frame Rate -
			//
			//  The unmaped frame range over which an output clip has images.
			 double getUnmappedFrameRate() const override;

			// Unmapped Frame Range -
			//
			//  The unmaped frame range over which an output clip has images.
			 void getUnmappedFrameRange(double &unmappedStartFrame, double &unmappedEndFrame) const override;

			// Continuous Samples -
			//
			//  0 if the images can only be sampled at discreet times (eg: the clip is a sequence of frames),
			//  1 if the images can only be sampled continuously (eg: the clip is infact an animating roto spline and can be rendered anywhen).
			 bool getContinuousSamples() const override;

			/// override this to fill in the image at the given time.
			/// The bounds of the image on the image plane should be
			/// 'appropriate', typically the value returned in getRegionsOfInterest
			/// on the effect instance. Outside a render call, the optionalBounds should
			/// be 'appropriate' for the.
			/// If bounds is not null, fetch the indicated section of the canonical image plane.
			 OFX::Host::ImageEffect::Image* getImage(OfxTime time, const OfxRectD *optionalBounds) override;

			/// override this to return the rod on the clip
			 OfxRectD getRegionOfDefinition(OfxTime time) const override;

#ifdef OFX_SUPPORTS_OPENGLRENDER
			/// load a texture from the given clip, for OpenGL-based rendering.
			 OFX::Host::ImageEffect::Texture* loadTexture(OfxTime time, const char *format, const OfxRectD *optionalBounds) override;
#endif

			/// Set an output OpenGL texture that the plugin will render into.
			void setOutputTexture( 			unsigned int textureId ) { m_outputTexture = textureId; }
			unsigned int outputTexture() const { return m_outputTexture; }

	};

	/// A texture subclass that deletes the GL texture on destruction.
	class GafferTexture : public OFX::Host::ImageEffect::Texture
	{
		public :
			GafferTexture(
				ClipInstance& instance,
				double renderScaleX,
				double renderScaleY,
				unsigned int index,
				unsigned int target,
				const OfxRectI &bounds,
				const OfxRectI &rod,
				int rowBytes,
				const std::string &field,
				const std::string &uniqueIdentifier
			);

			~GafferTexture() override;

		private :
			unsigned int m_textureId;
	};

}
