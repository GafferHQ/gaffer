##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import os
import imath

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class AttributeVisualiserTest( GafferSceneTest.SceneTestCase ) :

	def testColorMode( self ) :

		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( sphere["out"] )
		group["in"][2].setInput( sphere["out"] )

		filter1 = GafferScene.PathFilter()
		filter1["paths"].setValue( IECore.StringVectorData( [ "/group/sphere1" ] ) )

		attributes1 = GafferScene.StandardAttributes()
		attributes1["in"].setInput( group["out"] )
		attributes1["attributes"]["transformBlurSegments"]["enabled"].setValue( 1 )
		attributes1["attributes"]["transformBlurSegments"]["value"].setValue( 4 )
		attributes1["filter"].setInput( filter1["out"] )

		filter2 = GafferScene.PathFilter()
		filter2["paths"].setValue( IECore.StringVectorData( [ "/group/sphere2" ] ) )

		attributes2 = GafferScene.StandardAttributes()
		attributes2["in"].setInput( attributes1["out"] )
		attributes2["attributes"]["transformBlurSegments"]["enabled"].setValue( 1 )
		attributes2["attributes"]["transformBlurSegments"]["value"].setValue( 2 )
		attributes2["filter"].setInput( filter2["out"] )

		self.assertTrue( "gl:surface" not in attributes2["out"].attributes( "/group/sphere" ) )
		self.assertTrue( "gl:surface" not in attributes2["out"].attributes( "/group/sphere1" ) )
		self.assertTrue( "gl:surface" not in attributes2["out"].attributes( "/group/sphere2" ) )

		visualiser = GafferScene.AttributeVisualiser()
		visualiser["in"].setInput( attributes2["out"] )
		self.assertSceneValid( visualiser["out"] )

		self.assertTrue( "gl:surface" not in visualiser["out"].attributes( "/group/sphere" ) )
		self.assertTrue( "gl:surface" not in visualiser["out"].attributes( "/group/sphere1" ) )
		self.assertTrue( "gl:surface" not in visualiser["out"].attributes( "/group/sphere2" ) )

		visualiser["attributeName"].setValue( "gaffer:transformBlurSegments" )
		visualiser["mode"].setValue( visualiser.Mode.Color )
		visualiser["max"].setValue( 4 )

		self.assertTrue( "gl:surface" not in visualiser["out"].attributes( "/group/sphere" ) )
		self.assertTrue( "gl:surface" in visualiser["out"].attributes( "/group/sphere1" ) )
		self.assertTrue( "gl:surface" in visualiser["out"].attributes( "/group/sphere2" ) )
		self.assertEqual(
			visualiser["out"].attributes( "/group/sphere1" )["gl:surface"].outputShader().parameters["Cs"].value,
			imath.Color3f( 1 ),
		)
		self.assertEqual(
			visualiser["out"].attributes( "/group/sphere2" )["gl:surface"].outputShader().parameters["Cs"].value,
			imath.Color3f( .5 ),
		)

	def testShaderNodeColorMode( self ) :

		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( sphere["out"] )
		group["in"][2].setInput( sphere["out"] )

		shader1 = GafferSceneTest.TestShader()
		shader1["name"].setValue( "test" )
		shader1["type"].setValue( "gfr:surface" )

		filter1 = GafferScene.PathFilter()
		filter1["paths"].setValue( IECore.StringVectorData( [ "/group/sphere1" ] ) )

		assignment1 = GafferScene.ShaderAssignment()
		assignment1["in"].setInput( group["out"] )
		assignment1["filter"].setInput( filter1["out"] )
		assignment1["shader"].setInput( shader1["out"] )

		shader2 = GafferSceneTest.TestShader()
		shader2["name"].setValue( "test" )
		shader2["type"].setValue( "gfr:surface" )
		Gaffer.Metadata.registerValue( shader2, "nodeGadget:color", imath.Color3f( 1, 0, 0 ) )

		filter2 = GafferScene.PathFilter()
		filter2["paths"].setValue( IECore.StringVectorData( [ "/group/sphere2" ] ) )

		assignment2 = GafferScene.ShaderAssignment()
		assignment2["in"].setInput( assignment1["out"] )
		assignment2["filter"].setInput( filter2["out"] )
		assignment2["shader"].setInput( shader2["out"] )

		self.assertTrue( "gl:surface" not in assignment2["out"].attributes( "/group/sphere" ) )
		self.assertTrue( "gl:surface" not in assignment2["out"].attributes( "/group/sphere1" ) )
		self.assertTrue( "gl:surface" not in assignment2["out"].attributes( "/group/sphere2" ) )

		visualiser = GafferScene.AttributeVisualiser()
		visualiser["in"].setInput( assignment2["out"] )
		self.assertSceneValid( visualiser["out"] )

		self.assertTrue( "gl:surface" not in visualiser["out"].attributes( "/group/sphere" ) )
		self.assertTrue( "gl:surface" not in visualiser["out"].attributes( "/group/sphere1" ) )
		self.assertTrue( "gl:surface" not in visualiser["out"].attributes( "/group/sphere2" ) )

		visualiser["attributeName"].setValue( "gfr:surface" )
		visualiser["mode"].setValue( visualiser.Mode.ShaderNodeColor )
		self.assertSceneValid( visualiser["out"] )

		self.assertTrue( "gl:surface" not in visualiser["out"].attributes( "/group/sphere" ) )
		self.assertTrue( "gl:surface" in visualiser["out"].attributes( "/group/sphere1" ) )
		self.assertTrue( "gl:surface" in visualiser["out"].attributes( "/group/sphere2" ) )
		self.assertEqual(
			visualiser["out"].attributes( "/group/sphere1" )["gl:surface"].outputShader().parameters["Cs"].value,
			imath.Color3f( 0 ),
		)
		self.assertEqual(
			visualiser["out"].attributes( "/group/sphere2" )["gl:surface"].outputShader().parameters["Cs"].value,
			imath.Color3f( 1, 0, 0 ),
		)

	def testVectors( self ) :

		fileName = os.path.join( self.temporaryDirectory(), "attributes.scc" )
		scene = IECoreScene.SceneInterface.create( fileName, IECore.IndexedIO.Write )
		child = scene.createChild( "child" )
		for name, value in [
			( "v2f", IECore.V2fData( imath.V2f( 1, 2 ) ) ),
			( "v3f", IECore.V3fData( imath.V3f( 3, 4, 5 ) ) ),
			( "v2i", IECore.V2iData( imath.V2i( 6, 7 ) ) ),
			( "v3i", IECore.V3iData( imath.V3i( 8, 9, 10 ) ) ),
			( "v2d", IECore.V2dData( imath.V2d( 11, 12 ) ) ),
			( "v3d", IECore.V3dData( imath.V3d( 13, 14, 15 ) ) ),
		] :
			child.writeAttribute( name, value, 1 )
		del scene, child

		sceneReader = GafferScene.SceneReader()
		sceneReader["fileName"].setValue( fileName )

		childFilter = GafferScene.PathFilter()
		childFilter["paths"].setValue( IECore.StringVectorData( [ "/child" ] ) )

		visualiser = GafferScene.AttributeVisualiser()
		visualiser["in"].setInput( sceneReader["out"] )
		visualiser["filter"].setInput( childFilter["out"] )

		for name, value in [
			( "v2f", imath.Color3f( 1, 2, 0 ) ),
			( "v3f", imath.Color3f( 3, 4, 5 ) ),
			( "v2i", imath.Color3f( 6, 7, 0 ) ),
			( "v3i", imath.Color3f( 8, 9, 10 ) ),
			( "v2d", imath.Color3f( 11, 12, 0 ) ),
			( "v3d", imath.Color3f( 13, 14, 15 ) ),
		] :

			visualiser["attributeName"].setValue( name )
			self.assertEqual(
				visualiser["out"].attributes( "/child" )["gl:surface"].outputShader().parameters["Cs"].value,
				value,
			)

if __name__ == "__main__":
	unittest.main()
