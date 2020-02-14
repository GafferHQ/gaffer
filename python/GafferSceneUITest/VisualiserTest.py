##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Cinesite VFX Ltd. nor the names of
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

import IECore
import IECoreScene

import GafferUITest
import GafferScene

# Needs to be imported to register the visualisers
import GafferSceneUI

class VisualiserTest( GafferUITest.TestCase ) :

	def testCameraVisualiserFramingBound( self )  :

		# Certain visualisations should be able to opt-out of affecting
		# a locations bounds (generally to prevent 'large' visualisations
		# from breaking 'f' to fit to the viewer).

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"OpenGL",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)

		camera = IECoreScene.Camera()
		camera.setProjection( "perspective" )

		# The expected bound is the size of the green camera body visualisation.
		# We want to make sure the renderer bound it doesn't contain the frustum
		# visualisation which extends to the far clipping plane.
		expectedBodyBound = imath.Box3f( imath.V3f( -0.85, -0.85, -0.75 ), imath.V3f( 0.85, 0.85, 1.8 ) )

		# Make sure the far plane is bigger than the camera body visualisation
		clippingPlanes = camera.getClippingPlanes()
		self.assertTrue( clippingPlanes[1] > abs(expectedBodyBound.min()[2]) )

		_ =	renderer.object(
			"/camera",
			camera,
			renderer.attributes( IECore.CompoundObject() )
		)
		cameraBound = renderer.command( "gl:queryBound", {} )

		self.assertEqual( cameraBound, expectedBodyBound )

if __name__ == "__main__":
	unittest.main()
