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

import IECoreGL

import GafferTest
import GafferScene

class VisualiserTest( GafferTest.TestCase ) :

	def testConstructor( self ) :

		g = IECoreGL.Group()

		v = GafferScene.IECoreScenePreview.Visualisation( g )
		self.assertEqual( v.scale, GafferScene.IECoreScenePreview.Visualisation.Scale.Local )
		self.assertEqual( v.category, GafferScene.IECoreScenePreview.Visualisation.Category.Generic )
		self.assertEqual( v.affectsFramingBound, True )

		v = GafferScene.IECoreScenePreview.Visualisation( g,
			GafferScene.IECoreScenePreview.Visualisation.Scale.None_,
			GafferScene.IECoreScenePreview.Visualisation.Category.Frustum,
			False
		)
		self.assertEqual( v.scale, GafferScene.IECoreScenePreview.Visualisation.Scale.None_ )
		self.assertEqual( v.category, GafferScene.IECoreScenePreview.Visualisation.Category.Frustum )
		self.assertEqual( v.affectsFramingBound, False )

	def testVisualisationConvenienceConstructors( self ) :

		g = IECoreGL.Group()

		ColorSpace = GafferScene.IECoreScenePreview.Visualisation.ColorSpace
		for colorSpace in ( ColorSpace.Scene, ColorSpace.Display ) :

			geom = GafferScene.IECoreScenePreview.Visualisation.createGeometry( g, colorSpace = colorSpace )
			self.assertEqual( geom.scale, GafferScene.IECoreScenePreview.Visualisation.Scale.Local )
			self.assertEqual( geom.category, GafferScene.IECoreScenePreview.Visualisation.Category.Generic )
			self.assertEqual( geom.affectsFramingBound, True )
			self.assertEqual( geom.colorSpace, colorSpace )

			for bounded in ( True, False ) :
				o = GafferScene.IECoreScenePreview.Visualisation.createOrnament( g, bounded, colorSpace = colorSpace )
				self.assertEqual( o.scale, GafferScene.IECoreScenePreview.Visualisation.Scale.Visualiser )
				self.assertEqual( o.category, GafferScene.IECoreScenePreview.Visualisation.Category.Generic )
				self.assertEqual( o.affectsFramingBound, bounded )
				self.assertEqual( o.colorSpace, colorSpace )

			Scale = GafferScene.IECoreScenePreview.Visualisation.Scale
			for scale in ( Scale.Local, Scale.Visualiser ) :
				f = GafferScene.IECoreScenePreview.Visualisation.createFrustum( g, scale, colorSpace = colorSpace )
				self.assertEqual( f.scale, scale )
				self.assertEqual( f.category, GafferScene.IECoreScenePreview.Visualisation.Category.Frustum )
				self.assertEqual( f.affectsFramingBound, False )
				self.assertEqual( f.colorSpace, colorSpace )

if __name__ == "__main__":
	unittest.main()
