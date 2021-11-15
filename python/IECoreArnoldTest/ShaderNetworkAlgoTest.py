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

import ctypes
import unittest

import arnold

import imath

import IECore
import IECoreScene
import IECoreArnold

class ShaderNetworkAlgoTest( unittest.TestCase ) :

	def test( self ) :

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"noiseHandle" : IECoreScene.Shader( "noise" ),
				"flatHandle" : IECoreScene.Shader( "flat" ),
			},
			connections = [
				( ( "noiseHandle", "" ), ( "flatHandle", "color" ) ),
			],
			output = "flatHandle"
		)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			nodes = IECoreArnold.ShaderNetworkAlgo.convert( network, universe, "test" )

			self.assertEqual( len( nodes ), 2 )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[0] ) ), "noise" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[1] ) ), "flat" )

			self.assertEqual( arnold.AiNodeGetName( nodes[0] ), "test:noiseHandle" )
			self.assertEqual( arnold.AiNodeGetName( nodes[1] ), "test" )

			self.assertEqual(
				ctypes.addressof( arnold.AiNodeGetLink( nodes[1], "color" ).contents ),
				ctypes.addressof( nodes[0].contents )
			)

	def testUpdate( self ) :

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"noiseHandle" : IECoreScene.Shader( "noise" ),
				"flatHandle" : IECoreScene.Shader( "flat" ),
			},
			connections = [
				( ( "noiseHandle", "" ), ( "flatHandle", "color" ) ),
			],
			output = "flatHandle"
		)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			# Convert

			nodes = IECoreArnold.ShaderNetworkAlgo.convert( network, universe, "test" )

			def assertNoiseAndFlatNodes() :

				self.assertEqual( len( nodes ), 2 )
				self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[0] ) ), "noise" )
				self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[1] ) ), "flat" )

				self.assertEqual( arnold.AiNodeGetName( nodes[0] ), "test:noiseHandle" )
				self.assertEqual( arnold.AiNodeGetName( nodes[1] ), "test" )

				self.assertEqual(
					ctypes.addressof( arnold.AiNodeGetLink( nodes[1], "color" ).contents ),
					ctypes.addressof( nodes[0].contents )
				)

			assertNoiseAndFlatNodes()

			# Convert again with no changes at all. We want to see the same nodes reused.

			originalNodes = nodes[:]
			self.assertTrue( IECoreArnold.ShaderNetworkAlgo.update( nodes, network ) )
			assertNoiseAndFlatNodes()

			self.assertEqual( ctypes.addressof( nodes[0].contents ), ctypes.addressof( originalNodes[0].contents ) )
			self.assertEqual( ctypes.addressof( nodes[1].contents ), ctypes.addressof( originalNodes[1].contents ) )

			# Convert again with a tweak to a noise parameter. We want to see the same nodes
			# reused, with the new parameter value taking hold.

			noise = network.getShader( "noiseHandle" )
			noise.parameters["octaves"] = IECore.IntData( 3 )
			network.setShader( "noiseHandle", noise )

			originalNodes = nodes[:]
			self.assertTrue( IECoreArnold.ShaderNetworkAlgo.update( nodes, network ) )
			assertNoiseAndFlatNodes()

			self.assertEqual( ctypes.addressof( nodes[0].contents ), ctypes.addressof( originalNodes[0].contents ) )
			self.assertEqual( ctypes.addressof( nodes[1].contents ), ctypes.addressof( originalNodes[1].contents ) )
			self.assertEqual( arnold.AiNodeGetInt( nodes[0], "octaves" ), 3 )

			# Remove the noise shader, and replace it with an image. Make sure the new network is as we expect, and
			# the old noise node has been destroyed.

			network.removeShader( "noiseHandle" )
			network.setShader( "imageHandle", IECoreScene.Shader( "image" ) )
			network.addConnection( ( ( "imageHandle", "" ), ( "flatHandle", "color" ) ) )

			originalNodes = nodes[:]
			self.assertTrue( IECoreArnold.ShaderNetworkAlgo.update( nodes, network ) )

			self.assertEqual( ctypes.addressof( nodes[1].contents ), ctypes.addressof( originalNodes[1].contents ) )

			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[0] ) ), "image" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[1] ) ), "flat" )

			self.assertEqual( arnold.AiNodeGetName( nodes[0] ), "test:imageHandle" )
			self.assertEqual( arnold.AiNodeGetName( nodes[1] ), "test" )

			self.assertEqual(
				ctypes.addressof( arnold.AiNodeGetLink( nodes[1], "color" ).contents ),
				ctypes.addressof( nodes[0].contents )
			)

			self.assertIsNone( arnold.AiNodeLookUpByName( universe, "test:noiseHandle" ) )

			# Replace the output shader with something else.

			network.removeShader( "flatHandle" )
			network.setShader( "lambertHandle", IECoreScene.Shader( "lambert" ) )
			network.addConnection( ( ( "imageHandle", "" ), ( "lambertHandle", "Kd_color" ) ) )
			network.setOutput( ( "lambertHandle", "" ) )

			originalNodes = nodes[:]
			self.assertFalse( IECoreArnold.ShaderNetworkAlgo.update( nodes, network ) )

			self.assertEqual( ctypes.addressof( nodes[0].contents ), ctypes.addressof( originalNodes[0].contents ) )

			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[0] ) ), "image" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[1] ) ), "lambert" )

			self.assertEqual( arnold.AiNodeGetName( nodes[0] ), "test:imageHandle" )
			self.assertEqual( arnold.AiNodeGetName( nodes[1] ), "test" )

			self.assertEqual(
				ctypes.addressof( arnold.AiNodeGetLink( nodes[1], "Kd_color" ).contents ),
				ctypes.addressof( nodes[0].contents )
			)

	def testBlindData( self ) :

		flat = IECoreScene.Shader( "flat" )
		flat.blindData().update( {
				"user:testInt" : IECore.IntData( 1 ),
				"user:testFloat" : IECore.FloatData( 2.5 ),
				"user:testV3f" : IECore.V3fData( imath.V3f( 1, 2, 3 ) ),
				"user:testColor3f" : IECore.Color3fData( imath.Color3f( 4, 5, 6 ) ),
				"user:testString" : IECore.StringData( "we're all doomed" ),
		} )

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"noiseHandle" : IECoreScene.Shader( "noise" ),
				"flatHandle" : flat,
			},
			connections = [
				( ( "noiseHandle", "" ), ( "flatHandle", "color" ) ),
			],
			output = "flatHandle"
		)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			nodes = IECoreArnold.ShaderNetworkAlgo.convert( network, universe, "test" )

			self.assertEqual( len( nodes ), 2 )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[0] ) ), "noise" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[1] ) ), "flat" )

			self.assertEqual( arnold.AiNodeGetName( nodes[0] ), "test:noiseHandle" )
			self.assertEqual( arnold.AiNodeGetName( nodes[1] ), "test" )

			self.assertEqual( arnold.AiNodeGetInt( nodes[1], "user:testInt" ), 1 )
			self.assertEqual( arnold.AiNodeGetFlt( nodes[1], "user:testFloat" ), 2.5 )
			self.assertEqual( arnold.AiNodeGetVec( nodes[1], "user:testV3f" ), arnold.AtVector( 1, 2, 3 ) )
			self.assertEqual( arnold.AiNodeGetRGB( nodes[1], "user:testColor3f" ), arnold.AtRGB( 4, 5, 6 ) )
			self.assertEqual( arnold.AiNodeGetStr( nodes[1], "user:testString" ), "we're all doomed" )

if __name__ == "__main__":
	unittest.main()
