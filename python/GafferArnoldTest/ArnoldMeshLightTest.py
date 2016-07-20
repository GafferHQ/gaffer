##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferScene
import GafferSceneTest
import GafferArnold

class ArnoldMeshLightTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Sphere()
		g = GafferScene.Group()
		g["in"][0].setInput( p["out"] )
		g["in"][1].setInput( s["out"] )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )

		l = GafferArnold.ArnoldMeshLight()

		l["in"].setInput( g["out"] )
		l["filter"].setInput( f["out"] )

		self.assertEqual( l["out"].attributes( "/group/sphere" )["ai:light"][0].name, "mesh_light" )
		self.assertTrue( "ai:light" not in l["out"].attributes( "/group/plane" ) )

		for v in ( "shadow", "reflected", "refracted", "diffuse", "glossy" ) :
			v = "ai:visibility:" + v
			self.assertEqual( l["out"].attributes( "/group/sphere" )[v].value, False )
			self.assertTrue( v not in l["out"].attributes( "/group/plane" ) )

		self.assertEqual( set( l["out"].set( "__lights" ).value.paths() ), { "/group/sphere" } )

	def testShader( self ) :

		s = GafferScene.Sphere()
		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		l = GafferArnold.ArnoldMeshLight()

		l["in"].setInput( s["out"] )
		l["filter"].setInput( f["out"] )

		l["parameters"]["intensity"].setValue( 10 )
		l["parameters"]["color"].setValue( IECore.Color3f( 1, 0, 0 ) )

		shaders = l["out"].attributes( "/sphere" )["ai:light"]
		self.assertEqual( len( shaders ), 1 )
		self.assertEqual( shaders[0].parameters["intensity"].value, 10 )
		self.assertEqual( shaders[0].parameters["color"].value, IECore.Color3f( 1, 0, 0 ) )

	def testCameraVisibility( self ) :

		s = GafferScene.Sphere()
		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		l = GafferArnold.ArnoldMeshLight()

		l["in"].setInput( s["out"] )
		l["filter"].setInput( f["out"] )

		self.assertTrue( "ai:visibility:camera" not in l["out"].attributes( "/sphere" ) )

		l["cameraVisibility"]["enabled"].setValue( True )
		self.assertEqual( l["out"].attributes( "/sphere" )["ai:visibility:camera"].value, True )

		l["cameraVisibility"]["value"].setValue( False )
		self.assertEqual( l["out"].attributes( "/sphere" )["ai:visibility:camera"].value, False )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["p"] = GafferScene.Plane()
		s["f"] = GafferScene.PathFilter()
		s["f"]["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )
		s["l"] = GafferArnold.ArnoldMeshLight()
		s["l"]["in"].setInput( s["p"]["out"] )
		s["l"]["filter"].setInput( s["f"]["out"] )

		ss = s.serialise()
		self.assertFalse( '["out"].setInput' in ss )

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

		self.assertEqual( s["l"]["parameters"].keys(), s2["l"]["parameters"].keys() )
		self.assertEqual( s["l"]["out"].attributes( "/plane" ), s2["l"]["out"].attributes( "/plane" ) )

if __name__ == "__main__":
	unittest.main()
