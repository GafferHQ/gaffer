##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

import unittest
import math
import imath
import random


import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class CameraTweaksTest( GafferSceneTest.SceneTestCase ) :

	def testTweaks( self ) :

		c = GafferScene.Camera()

		tweaks = GafferScene.CameraTweaks()
		tweaks["in"].setInput( c["out"] )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/camera" ] ) )

		tweaks["filter"].setInput( f["out"] )

		self.assertEqual( c["out"].object( "/camera" ), tweaks["out"].object( "/camera" ) )

		random.seed( 42 )

		for i in range( 20 ):
			tweaks["tweaks"].clearChildren()

			c["projection"].setValue( "perspective" )
			c["perspectiveMode"].setValue( GafferScene.Camera.PerspectiveMode.ApertureFocalLength )
			c["aperture"].setValue( imath.V2f( random.uniform( 1, 20 ), random.uniform( 1, 20 ) ) )
			c["apertureOffset"].setValue( imath.V2f( random.uniform( -10, 10 ), random.uniform( -10, 10 ) ) )
			c["focalLength"].setValue( random.uniform( 0.5, 50 ) )
			c["clippingPlanes"].setValue( imath.V2f( random.uniform( 0.5, 100 ) ) + imath.V2f( 0, random.uniform( 0.5, 100 ) ) )
			c["fStop"].setValue( random.uniform( 0, 16 ) )
			c["focalLengthWorldScale"].setValue( random.uniform( 0.01, 10 ) )
			c["focusDistance"].setValue( random.uniform( 0.01, 100 ) )
			c["renderSettingOverrides"]["filmFit"]["enabled"].setValue( True )
			c["renderSettingOverrides"]["filmFit"]["value"].setValue( random.choice( list( IECoreScene.Camera.FilmFit.names.values() ) ) )
			c["renderSettingOverrides"]["shutter"]["enabled"].setValue( True )
			c["renderSettingOverrides"]["shutter"]["value"].setValue( imath.V2f( random.uniform( -0.5, 0 ), random.uniform( 0, 0.5 ) ) )
			c["renderSettingOverrides"]["pixelAspectRatio"]["enabled"].setValue( True )
			c["renderSettingOverrides"]["pixelAspectRatio"]["value"].setValue( random.uniform( 0.1, 10 ) )

			self.assertEqual( c["out"].object( "/camera" ), tweaks["out"].object( "/camera" ) )

			for mode in [
				m for m in Gaffer.TweakPlug.Mode.names.values() if m not in [
					Gaffer.TweakPlug.Mode.ListAppend,
					Gaffer.TweakPlug.Mode.ListPrepend,
					Gaffer.TweakPlug.Mode.ListRemove
				]
			] :
				for name, value in [
						("projection", "orthographic" ),
						( "aperture", imath.V2f( 10, 20 ) ),
						( "apertureOffset", imath.V2f( 5, -7 ) ),
						( "focalLength", 4.2 ),
						( "clippingPlanes", imath.V2f( 5, 7 ) ),
						( "fStop", 1.2 ),
						( "focalLengthWorldScale", 0.12 ),
						( "focusDistance", 3.2 ),
						( "filmFit", 1 ),
						( "shutter", imath.V2f( 0.1, 0.2 ) ),
						( "pixelAspectRatio", 0.11 ),
						( "fieldOfView", 5.7 ),
						( "apertureAspectRatio", 0.15 ),
					]:

					if type( value ) in [ str ] and mode in [
						Gaffer.TweakPlug.Mode.Add,
						Gaffer.TweakPlug.Mode.Subtract,
						Gaffer.TweakPlug.Mode.Multiply,
						Gaffer.TweakPlug.Mode.Min,
						Gaffer.TweakPlug.Mode.Max
					] :
						continue

					tweaks["tweaks"].clearChildren()
					tweaks["tweaks"].addChild( Gaffer.TweakPlug( name, value ) )
					tweaks["tweaks"]["tweak"]["mode"].setValue( mode )

					if name == "fieldOfView":
						orig = c["out"].object( "/camera" ).calculateFieldOfView()[0]
					elif name == "apertureAspectRatio":
						origWindow  = c["out"].object( "/camera" ).frustum(
								IECoreScene.Camera.FilmFit.Distort
							).size()
						orig = origWindow[0] / origWindow[1]
					else:
						orig = c["out"].object( "/camera" ).parameters()[name].value

					if mode == Gaffer.TweakPlug.Mode.Remove:
						if not name in [ "fieldOfView", "apertureAspectRatio" ]:
							self.assertFalse( name in tweaks["out"].object( "/camera" ).parameters() )
						continue
					elif mode == Gaffer.TweakPlug.Mode.Replace:
						ref = value
					elif mode == Gaffer.TweakPlug.Mode.Add:
						ref = orig + value
					elif mode == Gaffer.TweakPlug.Mode.Multiply:
						ref = orig * value
					elif mode == Gaffer.TweakPlug.Mode.Subtract:
						ref = orig - value
					elif mode == Gaffer.TweakPlug.Mode.Create:
						ref = value
					elif mode == GafferScene.TweakPlug.Mode.Min:
						if type( value ) == imath.V2f:
							ref = imath.V2f( min( orig[0], value[0] ), min( orig[1], value[1] ) )
						else:
							ref = min( orig, value )
					elif mode == GafferScene.TweakPlug.Mode.Max:
						if type( value ) == imath.V2f:
							ref = imath.V2f( max( orig[0], value[0] ), max( orig[1], value[1] ) )
						else:
							ref = max( orig, value )

					if name == "fieldOfView":
						modified = tweaks["out"].object( "/camera" ).calculateFieldOfView()[0]
						ref = max( 0, min( 179.99, ref ) )
					elif name == "apertureAspectRatio":
						modWindow  = tweaks["out"].object( "/camera" ).frustum(
								IECoreScene.Camera.FilmFit.Distort
							).size()
						modified = modWindow[0] / modWindow[1]
						ref = max( 0.0000001, ref )
					else:
						modified = tweaks["out"].object( "/camera" ).parameters()[name].value

					if type( value ) == imath.V2f:
						self.assertAlmostEqual( modified[0], ref[0], places = 4 )
						self.assertAlmostEqual( modified[1], ref[1], places = 4 )
					else:
						self.assertAlmostEqual( modified, ref, places = 4 )

if __name__ == "__main__":
	unittest.main()
