//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Lucien Fostier. All rights reserved.
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

#include "GafferOFX/Export.h"
#include "GafferOFX/EffectImageInstance.h"

#include "HostSupport/ofxhImageEffect.h"

namespace GafferOFX
{

/// Gaffer-specific implementation of an OFX overlay interact instance.
/// This wraps OFX::Host::ImageEffect::OverlayInteract and implements
/// the required hooks using Gaffer's viewport information.
class GAFFEROFX_API GafferOFXInteractInstance : public OFX::Host::ImageEffect::OverlayInteract
{

	public :

		GafferOFXInteractInstance(
			OFX::Host::ImageEffect::Instance &effectInstance,
			int bitDepthPerComponent = 8,
			bool hasAlpha = false
		);

		~GafferOFXInteractInstance() override;

		OfxStatus createInstance();
		void destroyInstance();

		/// Set the image display window origin (bottom-left pixel).
		void setDisplayWindowOrigin( double x, double y );

		/// Set viewport dimensions (pixel space). Must be called before drawAction.
		void setViewportSize( double width, double height );

		/// Set the current time (frame). Called by the Tool on mouse events.
		void setTime( OfxTime time );

		OfxTime getTime() const;

		/// Draw a debug test shape to verify GL rendering works.
		void debugDraw();

		/// Render the overlay in image-pixel coordinates.
		/// Sets up orthographic projection matching imagePixelWidth/Height,
		/// dispatches drawAction to the plugin, then restores GL state.
		void renderOverlay( double time, double renderScaleX, double renderScaleY, double pixelAspect, int imageWidth = 0, int imageHeight = 0 );

		/// Override callEntry to pass the effect instance handle instead of the
		/// interact instance handle. The plugin's dispatch maps overlay interact
		/// actions back to the image effect, and it only recognizes the effect handle.
		OfxStatus callEntry( const char *action, OFX::Host::Property::Set *inArgs ) override;

		/// After an interact action (penUp), notify the effect instance
		/// that the plugin may have changed parameters during the interact.
		/// This dispatches instanceChanged only to params that were
		/// actually modified since the last call.
		void notifyPluginEdited();

		/// Interact::Instance pure virtual implementations.
		void getViewportSize( double &width, double &height ) const override;
		void getPixelScale( double &xScale, double &yScale ) const override;
		void getBackgroundColour( double &r, double &g, double &b ) const override;
		bool getSuggestedColour( double &r, double &g, double &b ) const override;
		OfxStatus swapBuffers() override;
		OfxStatus redraw() override;

	private :

		bool m_created;
		double m_viewportWidth;
		double m_viewportHeight;
		double m_displayWindowMinX;
		double m_displayWindowMinY;
		OfxTime m_time;

};

} // namespace GafferOFX
