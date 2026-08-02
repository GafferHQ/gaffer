##########################################################################
#
#  Copyright (c) 2025, Lucien Fostier. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import imath

import Gaffer
import GafferUI

class OFXOverlayGadget( GafferUI.Gadget ) :

	def __init__( self, interact, viewportGadget, pixelAspect = 1.0, imageWidth = 0, imageHeight = 0, displayWindowMinX = 0, displayWindowMinY = 0 ) :

		GafferUI.Gadget.__init__( self )
		self.__interact = interact
		self.__viewportGadget = viewportGadget
		self.__pixelAspect = pixelAspect
		self.__imageWidth = imageWidth
		self.__imageHeight = imageHeight
		self.__interact.setDisplayWindowOrigin( float( displayWindowMinX ), float( displayWindowMinY ) )
		self.__lastViewportSize = ( -1, -1 )
		self.__gainedFocus = False

	def renderLayer( self, layer, style, renderReason ) :
		if not self.getVisible() :
			return

		if self.__interact is None :
			return

		if renderReason != GafferUI.Gadget.RenderReason.Draw :
			return

		if layer != GafferUI.Gadget.Layer.Front :
			return

		self.__updateViewportSize()

		renderScale = ( 1.0, 1.0 )
		time = self.__interact.getTime()

		# Gain focus once on first render
		if not self.__gainedFocus :
			self.__interact.gainFocusAction( time, renderScale )
			self.__gainedFocus = True

		# renderOverlay sets up GL state (projection, modelview),
		# dispatches drawAction to the plugin, then restores GL state.
		self.__interact.renderOverlay(
			time, 1.0, 1.0, self.__pixelAspect,
			self.__imageWidth, self.__imageHeight
		)

	def __updateViewportSize( self ) :

		vpSize = self.__viewportGadget.getViewport()
		vw, vh = int( vpSize.x ), int( vpSize.y )
		if ( vw, vh ) != self.__lastViewportSize :
			self.__interact.setViewportSize( float( vw ), float( vh ) )
			self.__lastViewportSize = ( vw, vh )

	def layerMask( self ) :

		# LayerMask is not exposed to Python - return the raw int.
		# 0x20 = OverlayFront, the topmost layer, correct for OFX overlays.
		# TODO use Layer::Front (might need to bind that to python)
		return 0x20

	def renderBound( self ) :

		return imath.Box3f( imath.V3f( -1e9 ), imath.V3f( 1e9 ) )
