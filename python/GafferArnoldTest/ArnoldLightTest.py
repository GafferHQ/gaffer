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

import arnold
import imath

import IECore
import IECoreScene
import IECoreArnold

import GafferSceneTest
import GafferArnold

class ArnoldLightTest( GafferSceneTest.SceneTestCase ) :

	def testUsesShaders( self ) :

		l = GafferArnold.ArnoldLight()
		l.loadShader( "point_light" )

		n = l["out"].attributes( "/light" )["ai:light"]
		self.assertTrue( isinstance( n, IECoreScene.ShaderNetwork ) )
		self.assertEqual( len( n ), 1 )
		self.assertTrue( isinstance( n.outputShader(), IECoreScene.Shader ) )
		self.assertEqual( n.outputShader().type, "ai:light" )
		self.assertEqual( n.outputShader().name, "point_light" )

	def testLoadAllLightsWithoutWarnings( self ) :

		lightNames = []
		with IECoreArnold.UniverseBlock( writable = False ) :
			it = arnold.AiUniverseGetNodeEntryIterator( arnold.AI_NODE_LIGHT )
			while not arnold.AiNodeEntryIteratorFinished( it ) :
				nodeEntry = arnold.AiNodeEntryIteratorGetNext( it )
				lightNames.append( arnold.AiNodeEntryGetName( nodeEntry ) )

		self.longMessage = True

		for lightName in lightNames :
			with IECore.CapturingMessageHandler() as mh :
				l = GafferArnold.ArnoldLight()
				l.loadShader( lightName )
				self.assertEqual( [ m.message for m in mh.messages ], [], "Error loading %s" % lightName )

	def testShaderInputs( self ) :

		s = GafferArnold.ArnoldShader( "sky" )
		s.loadShader( "physical_sky" )
		s["parameters"]["intensity"].setValue( 2 )

		# Test setting up a matte closure connected to "shader"
		# Note that this doesn't currently render correctly, but SolidAngle assures me that they are fixing
		# it and is the preferred way
		s2 = GafferArnold.ArnoldShader( "matte" )
		s2.loadShader( "matte" )
		s2["parameters"]["color"].setValue( imath.Color4f( 0, 1, 0, 0.5 ) )

		l = GafferArnold.ArnoldLight()
		l.loadShader( "skydome_light" )
		l["parameters"]["color"].setInput( s["out"] )
		l["parameters"]["shader"].setInput( s2["out"] )

		network = l["out"].attributes( "/light" )["ai:light"]
		self.assertEqual( len( network ), 3 )
		self.assertEqual( network.getShader( "sky" ).name, "physical_sky" )
		self.assertEqual( network.getShader( "sky" ).parameters["intensity"].value, 2 )
		self.assertEqual( network.getShader( "matte" ).name, "matte" )
		self.assertEqual( network.getShader( "matte" ).parameters["color"].value, imath.Color4f( 0, 1, 0, 0.5 ) )

		self.assertEqual(
			network.inputConnections( network.getOutput().shader ),
			[
				network.Connection( ( "sky", "out" ), ( network.getOutput().shader, "color" ) ),
				network.Connection( ( "matte", "out" ), ( network.getOutput().shader, "shader" ) ),
			]
		)

		s["parameters"]["intensity"].setValue( 4 )
		network = l["out"].attributes( "/light" )["ai:light"]
		self.assertEqual( network.getShader( "sky" ).parameters["intensity"].value, 4 )

	def testOSLShaderInputs( self ) :

		l = GafferArnold.ArnoldLight()
		l.loadShader( "skydome_light" )

		c = GafferSceneTest.TestShader( "mockOSL" )
		c["type"].setValue( "osl:shader" )

		l["parameters"]["color"].setInput( c["out"] )

		network = l["out"].attributes( "/light" )["ai:light"]
		self.assertEqual(
			network.inputConnections( network.getOutput().shader ),
			[
				network.Connection( ( "mockOSL", "out" ), ( network.getOutput().shader, "color" ) )
			]
		)

if __name__ == "__main__":
	unittest.main()
