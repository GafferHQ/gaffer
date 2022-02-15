##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

import imath

import IECoreScene

import GafferTest
import GafferSceneTest
import GafferArnold

class ArnoldImagerTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		imager = GafferArnold.ArnoldShader()
		imager.loadShader( "imager_exposure" )
		imager["parameters"]["exposure"].setValue( 5 )

		node = GafferArnold.ArnoldImager()
		node["imager"].setInput( imager["out"] )

		for mode in node.Mode.values.values() :

			# Since there is no upstream imager, all modes
			# should have the same effect.
			node["mode"].setValue( mode )

			self.assertEqual(
				node["out"].globals()["option:ai:imager"],
				imager.attributes()["ai:imager"]
			)

	def testRejectsNonImagerInputs( self ) :

		shader = GafferArnold.ArnoldShader()
		shader.loadShader( "flat" )

		node = GafferArnold.ArnoldImager()
		self.assertFalse( node["imager"].acceptsInput( shader["out"] ) )

	def testModes( self ) :

		def order( scene ) :

			network = scene.globals()["option:ai:imager"]

			result = []
			shaderHandle = network.getOutput().shader
			while shaderHandle :
				result.append( network.getShader( shaderHandle ).parameters["exposure"].value )
				shaderHandle = network.input( ( shaderHandle, "input" ) ).shader

			result.reverse()
			return result

		imager1 = GafferArnold.ArnoldShader()
		imager1.loadShader( "imager_exposure" )
		imager1["parameters"]["exposure"].setValue( 1 )

		imager2 = GafferArnold.ArnoldShader()
		imager2.loadShader( "imager_exposure" )
		imager2["parameters"]["exposure"].setValue( 2 )

		imager3 = GafferArnold.ArnoldShader()
		imager3.loadShader( "imager_exposure" )
		imager3["parameters"]["exposure"].setValue( 3 )

		node1 = GafferArnold.ArnoldImager()
		node1["imager"].setInput( imager1["out"] )
		self.assertEqual( order( node1["out"] ), [ 1 ] )

		node2 = GafferArnold.ArnoldImager()
		node2["in"].setInput( node1["out"] )
		node2["imager"].setInput( imager2["out"] )
		self.assertEqual( order( node2["out"] ), [ 2 ] )

		node2["mode"].setValue( GafferArnold.ArnoldImager.Mode.InsertLast )
		self.assertEqual( order( node2["out"] ), [ 1, 2 ] )

		node2["mode"].setValue( GafferArnold.ArnoldImager.Mode.InsertFirst )
		self.assertEqual( order( node2["out"] ), [ 2, 1 ] )

		node3 = GafferArnold.ArnoldImager()
		node3["in"].setInput( node2["out"] )
		node3["imager"].setInput( imager3["out"] )
		self.assertEqual( order( node3["out"] ), [ 3 ] )

		node3["mode"].setValue( GafferArnold.ArnoldImager.Mode.InsertLast )
		self.assertEqual( order( node3["out"] ), [ 2, 1, 3 ] )

		node3["mode"].setValue( GafferArnold.ArnoldImager.Mode.InsertFirst )
		self.assertEqual( order( node3["out"] ), [ 3, 2, 1 ] )

if __name__ == "__main__":
	unittest.main()
