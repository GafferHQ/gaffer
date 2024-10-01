##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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
import IECoreScene

import Gaffer
import GafferSceneTest
import GafferArnold

class ArnoldLightFilterTest( GafferSceneTest.SceneTestCase ) :

	def testUsesShaders( self ) :

		l = GafferArnold.ArnoldLightFilter()
		l.loadShader( "light_blocker" )

		n = l["out"].attributes( "/lightFilter" )["ai:lightFilter:filter"]
		self.assertTrue( isinstance( n, IECoreScene.ShaderNetwork ) )
		self.assertEqual( len( n ), 1 )
		self.assertTrue( isinstance( n.outputShader(), IECoreScene.Shader ) )
		self.assertEqual( n.outputShader().type, "ai:lightFilter" )
		self.assertEqual( n.outputShader().name, "light_blocker" )

	def testShaderInputs( self ) :

		# Test setting up a checkerboard connected to the lightfilter's "shader" input.

		s = GafferArnold.ArnoldShader( "Checkerboard" )
		s.loadShader( "checkerboard" )

		l = GafferArnold.ArnoldLightFilter()
		l.loadShader( "light_blocker" )

		l["parameters"]["shader"].setInput( s["out"] )

		network = l["out"].attributes( "/lightFilter" )["ai:lightFilter:filter"]
		self.assertEqual( len( network ), 2 )
		self.assertEqual( network.getShader( "__shader" ).name, "light_blocker" )
		self.assertEqual( network.getShader( "Checkerboard" ).name, "checkerboard" )
		self.assertEqual( network.getShader( "Checkerboard" ).parameters["color1"].value, imath.Color3f( 1, 1, 1 ) )

		self.assertEqual(
			network.inputConnections( network.getOutput().shader ),
			[
				network.Connection( ( "Checkerboard", "out" ), ( network.getOutput().shader, "shader" ) ),
			]
		)

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["l"] = GafferArnold.ArnoldLightFilter()
		s["l"].loadShader( "light_blocker" )

		ss = s.serialise()

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

		self.assertEqual( s["l"]["parameters"].keys(), s2["l"]["parameters"].keys() )

		for plug in s["l"]['parameters'].values():
			relativeName = plug.relativeName( s["l"] )
			self.assertEqual( s2["l"].descendant( relativeName ).getValue(), plug.getValue() )

		self.assertEqual( s["l"]["out"].attributes( "/lightFilter" ), s2["l"]["out"].attributes( "/lightFilter" ) )

	def testDisabling( self ) :

		l = GafferArnold.ArnoldLightFilter()
		l.loadShader( "light_blocker" )

		attributesHash = l["out"].attributesHash( "/lightFilter" )
		attributes = l["out"].attributes( "/lightFilter" )

		self.assertSceneValid( l["out"] )

		l["enabled"].setValue( False )

		attributesHash2 = l["out"].attributesHash( "/lightFilter" )
		self.assertNotEqual( attributesHash2, attributesHash )

		attributes2 = l["out"].attributes( "/lightFilter" )
		self.assertEqual( len( attributes2 ), 0 )

		self.assertSceneValid( l["out"] )

	def testReload( self ) :

		l = GafferArnold.ArnoldLightFilter()
		l.loadShader( "light_blocker" )

		l["parameters"]["density"].setValue( 3.14 )
		l["parameters"]["geometry_type"].setValue( "plane" )
		l["parameters"]["ramp"].setValue( 0.4 )
		l["parameters"]["width_edge"].setValue( 0.2 )

		l.loadShader( "light_blocker", keepExistingValues = True )

		self.assertAlmostEqual( l["parameters"]["density"].getValue(), 3.14, 5 )
		self.assertEqual( l["parameters"]["geometry_type"].getValue(), "plane" )
		self.assertAlmostEqual( l["parameters"]["ramp"].getValue(), 0.4, 5 )
		self.assertAlmostEqual( l["parameters"]["width_edge"].getValue(), 0.2, 5 )

		l.loadShader( "light_blocker", keepExistingValues = False )

		self.assertTrue( l["parameters"]["density"].isSetToDefault() )
		self.assertTrue( l["parameters"]["geometry_type"].isSetToDefault() )
		self.assertTrue( l["parameters"]["ramp"].isSetToDefault() )
		self.assertTrue( l["parameters"]["width_edge"].isSetToDefault() )

	def testSets( self ) :

		l = GafferArnold.ArnoldLightFilter()
		l.loadShader( "light_blocker" )

		self.assertEqual( l["out"].set( "__lightFilters" ).value.paths(), ["/lightFilter"] )

		l["sets"].setValue( "myLightFilters" )

		self.assertEqual( l["out"].set( "myLightFilters" ).value.paths(), ["/lightFilter"] )

	def testFilteredLightsPlug( self ) :

		l = GafferArnold.ArnoldLightFilter()
		l.loadShader( "light_blocker" )

		self.assertNotIn( "filteredLights", l["out"].attributes( "/lightFilter" ) )

		l["filteredLights"].setValue( "defaultLights" )

		self.assertIn( "filteredLights", l["out"].attributes( "/lightFilter" ) )
		self.assertEqual( l["out"].attributes( "/lightFilter" )["filteredLights"], IECore.StringData( "defaultLights"  ) )

		h1 = l["out"].attributesHash( "/lightFilter" )
		l["filteredLights"].setValue( "/does/not/exist" )
		h2 = l["out"].attributesHash( "/lightFilter" )

		self.assertNotEqual( h1, h2 )

		self.assertEqual( l["out"].attributes( "/lightFilter" )["filteredLights"], IECore.StringData( "/does/not/exist" ) )
