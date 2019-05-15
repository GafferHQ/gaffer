##########################################################################
#
#  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class SetVisualiserTest( GafferSceneTest.SceneTestCase ) :

	def testDefaultAction ( self ) :

		# Make sure we dont affect the scene by default

		inScene = self.__basicSphereScene()
		visualiser = GafferScene.SetVisualiser()
		visualiser["sets"].setValue( '*' )
		visualiser["in"].setInput( inScene["setC"]["out"] )

		self.assertTrue( "gl:surface" not in visualiser["out"].attributes( "/group" ) )
		self.assertTrue( "gl:surface" not in visualiser["out"].attributes( "/group/sphere" ) )
		self.assertTrue( "gl:surface" not in visualiser["out"].attributes( "/group/sphere1" ) )
		self.assertTrue( "gl:surface" not in visualiser["out"].attributes( "/group/sphere2" ) )

	def testOutSets( self ) :

		inScene = self.__basicSphereScene()

		visualiser = GafferScene.SetVisualiser()
		visualiser["sets"].setValue( "*" )
		visualiser["in"].setInput( inScene["setC"]["out"] )
		f = self.__addMatchAllFilter( visualiser )

		outSets = visualiser["__outSets"].getValue()

		# set names are interned strings which don't sort well as is
		inSetNames = sorted([ str(s) for s in visualiser["out"].setNames() ])
		self.assertListEqual( inSetNames, list(outSets["names"]) )

		# Make sure we are returning unique colors for each set
		colors = outSets["colors"]
		for c in colors:
			self.assertEqual( colors.count(c), 1 )

	def testSetFilter( self ) :

		inScene = self.__basicSphereScene()

		visualiser = GafferScene.SetVisualiser()
		visualiser["in"].setInput( inScene["setC"]["out"] )
		f = self.__addMatchAllFilter( visualiser )

		self.assertEqual( visualiser["sets"].getValue(), "" )
		self.assertEqual( len(visualiser["__outSets"].getValue()["names"]), 0 )

		visualiser["sets"].setValue( "setA setB setC" )
		self.assertEqual( list(visualiser["__outSets"].getValue()["names"]), self.__testSetNames )

		visualiser["sets"].setValue( "set*" )
		self.assertEqual( list(visualiser["__outSets"].getValue()["names"]), self.__testSetNames )

		visualiser["sets"].setValue( "set* setA" )
		self.assertEqual( list(visualiser["__outSets"].getValue()["names"]), self.__testSetNames )

		sceneSets = sorted([ str(s) for s in inScene["setC"]["out"].setNames() ])

		visualiser["sets"].setValue( "*" )
		self.assertEqual( list(visualiser["__outSets"].getValue()["names"]), sceneSets )

	def testShadersAssignedToAllLocations( self ) :

		inScene = self.__basicSphereScene()

		self.assertTrue( "gl:surface" not in inScene["setC"]["out"].attributes( "/group" ) )
		self.assertTrue( "gl:surface" not in inScene["setC"]["out"].attributes( "/group/sphere" ) )
		self.assertTrue( "gl:surface" not in inScene["setC"]["out"].attributes( "/group/sphere1" ) )
		self.assertTrue( "gl:surface" not in inScene["setC"]["out"].attributes( "/group/sphere2" ) )

		visualiser = GafferScene.SetVisualiser()
		visualiser["sets"].setValue( 'set*' )
		visualiser["in"].setInput( inScene["setC"]["out"] )
		f = self.__addMatchAllFilter( visualiser )

		self.assertTrue( "gl:surface" in visualiser["out"].attributes( "/group" ) )
		self.assertTrue( "gl:surface" in visualiser["out"].attributes( "/group/sphere" ) )
		self.assertTrue( "gl:surface" in visualiser["out"].attributes( "/group/sphere1" ) )
		self.assertTrue( "gl:surface" in visualiser["out"].attributes( "/group/sphere2" ) )

	def testInherited( self ) :

		inScene = self.__basicSphereScene()

		visualiser = GafferScene.SetVisualiser()
		visualiser["sets"].setValue( 'set*' )
		visualiser["in"].setInput( inScene["setC"]["out"] )
		f = self.__addMatchAllFilter( visualiser )

		self.assertTrue( visualiser["includeInherited"].getValue() )

		self.assertEqual( visualiser["out"].attributes( "/group" )["gl:surface"].outputShader().parameters["numColors"].value, 1 )
		self.assertEqual( visualiser["out"].attributes( "/group/sphere" )["gl:surface"].outputShader().parameters["numColors"].value, 1 )
		self.assertEqual( visualiser["out"].attributes( "/group/sphere1" )["gl:surface"].outputShader().parameters["numColors"].value, 2 )
		self.assertEqual( visualiser["out"].attributes( "/group/sphere2" )["gl:surface"].outputShader().parameters["numColors"].value, 3 )

		visualiser["includeInherited"].setValue( False )

		self.assertEqual( visualiser["out"].attributes( "/group" )["gl:surface"].outputShader().parameters["numColors"].value, 1 )
		self.assertEqual( visualiser["out"].attributes( "/group/sphere" )["gl:surface"].outputShader().parameters["numColors"].value, 0 )
		self.assertEqual( visualiser["out"].attributes( "/group/sphere1" )["gl:surface"].outputShader().parameters["numColors"].value, 1 )
		self.assertEqual( visualiser["out"].attributes( "/group/sphere2" )["gl:surface"].outputShader().parameters["numColors"].value, 2 )

	def testColors( self ) :

		red = imath.Color3f( 1.0, 0.0, 0.0 )
		green = imath.Color3f( 0.0, 1.0, 0.0 )
		blue = imath.Color3f( 0.0, 0.0, 1.0 )

		inScene = self.__basicSphereScene()

		visualiser = GafferScene.SetVisualiser()
		visualiser["in"].setInput( inScene["setC"]["out"] )
		visualiser["sets"].setValue( '*' )
		f = self.__addMatchAllFilter( visualiser )

		self.assertEqual( visualiser["includeInherited"].getValue(), True )

		visualiser["colorOverrides"].addChild( Gaffer.NameValuePlug( "setA", red, True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		visualiser["colorOverrides"].addChild( Gaffer.NameValuePlug( "setB", green, True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		visualiser["colorOverrides"].addChild( Gaffer.NameValuePlug( "setC", blue, True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		self.assertEqual( visualiser["out"].attributes( "/group" )["gl:surface"].outputShader().parameters["colors"][0], red )
		self.assertEqual( visualiser["out"].attributes( "/group/sphere" )["gl:surface"].outputShader().parameters["colors"][0], red )

		self.assertEqual( visualiser["out"].attributes( "/group/sphere1" )["gl:surface"].outputShader().parameters["colors"][0], red )
		self.assertEqual( visualiser["out"].attributes( "/group/sphere1" )["gl:surface"].outputShader().parameters["colors"][1], blue )

		self.assertEqual( visualiser["out"].attributes( "/group/sphere2" )["gl:surface"].outputShader().parameters["colors"][0], red )
		self.assertEqual( visualiser["out"].attributes( "/group/sphere2" )["gl:surface"].outputShader().parameters["colors"][1], green )
		self.assertEqual( visualiser["out"].attributes( "/group/sphere2" )["gl:surface"].outputShader().parameters["colors"][2], blue )

	def testColorOverrides( self ) :

		inScene = self.__basicSphereScene()

		visualiser = GafferScene.SetVisualiser()
		visualiser["in"].setInput( inScene["setC"]["out"] )
		visualiser["sets"].setValue( 'set*' )
		f = self.__addMatchAllFilter( visualiser )

		## We never generate white so we can use it as a safe test value
		white = imath.Color3f( 1.0 )
		self.assertNotIn( white, visualiser["__outSets"].getValue()["colors"] )

		self.assertEqual( len(visualiser["colorOverrides"].children()), 0 )

		def colorForSetName( name ):
			d = visualiser["__outSets"].getValue()
			i = d["names"].index( name )
			return d["colors"][i]

		visualiser["colorOverrides"].addChild( Gaffer.NameValuePlug( "setA", white, True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		self.assertEqual( colorForSetName( "setA" ), white )
		self.assertNotEqual( colorForSetName( "setB" ), white )
		self.assertNotEqual( colorForSetName( "setC" ), white )

		visualiser["colorOverrides"].children()[0]["name"].setValue( "set*" )
		self.assertEqual( colorForSetName( "setA" ), white )
		self.assertEqual( colorForSetName( "setB" ), white )
		self.assertEqual( colorForSetName( "setC" ), white )

		sceneSets = inScene["setC"]["out"].setNames()
		defaultSets = [ s for s in sceneSets if s not in self.__testSetNames ]
		for s in defaultSets :
			self.assertNotEqual(  colorForSetName( s ), white )

		visualiser["colorOverrides"].children()[0]["enabled"].setValue( False )
		self.assertNotEqual( colorForSetName( "setA" ), white )
		self.assertNotEqual( colorForSetName( "setB" ), white )
		self.assertNotEqual( colorForSetName( "setC" ), white )

	def testOverrideValidation( self ) :

		inScene = self.__basicSphereScene()

		visualiser = GafferScene.SetVisualiser()
		visualiser["in"].setInput( inScene["setC"]["out"] )
		visualiser["sets"].setValue( 'set*' )
		f = self.__addMatchAllFilter( visualiser )

		# None of these should error as empty names or disabled should be fine

		visualiser["colorOverrides"].addChild( Gaffer.NameValuePlug( "setA", imath.Color3f( 1.0 ), True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		visualiser["__outSets"].getValue()

		visualiser["colorOverrides"].addChild( Gaffer.NameValuePlug( "setB", imath.Color3f( 1.0 ), False, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		visualiser["__outSets"].getValue()

		visualiser["colorOverrides"].addChild( Gaffer.NameValuePlug( "", imath.Color3f( 1.0 ), True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		visualiser["__outSets"].getValue()

		# Non-color3f types should error
		visualiser["colorOverrides"].addChild( Gaffer.NameValuePlug( "setB", "notAColor", True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		self.assertRaises( RuntimeError, visualiser["__outSets"].getValue )

	__testSetNames = [ 'setA', 'setB', 'setC' ]

	def __basicSphereScene( self ) :

		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( sphere["out"] )
		group["in"][2].setInput( sphere["out"] )

		# For safety, make sure we don't already have any sets with our names
		# creating any sets with our test names
		defaultSetNames = group["out"].setNames()
		for s in defaultSetNames :
			self.assertFalse( s.startswith( "set" ), msg = "Default set '%s' conflicts with the test case" % s )

		setA = GafferScene.Set()
		setA["in"].setInput( group["out"] )
		setA["name"].setValue( 'setA' )
		setA["paths"].setValue( IECore.StringVectorData( [ '/group' ] ) )

		setB = GafferScene.Set()
		setB["in"].setInput( setA["out"] )
		setB["name"].setValue( 'setB' )
		setB["paths"].setValue( IECore.StringVectorData( [ '/group/sphere2' ] ) )

		setC = GafferScene.Set()
		setC["in"].setInput( setB["out"] )
		setC["name"].setValue( 'setC' )
		setC["paths"].setValue( IECore.StringVectorData( [ '/group/sphere1', '/group/sphere2' ] ) )

		self.assertSceneValid( setC["out"] )

		# So they don't all get deleted here
		return {
			"sphere" : sphere,
			"group" : group,
			"setA" : setA,
			"setB" : setB,
			"setC" : setC
		}

	def __addMatchAllFilter( self, node ):

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ '...' ] ) )
		node["filter"].setInput( f["out"] )
		return f

if __name__ == "__main__":
	unittest.main()
