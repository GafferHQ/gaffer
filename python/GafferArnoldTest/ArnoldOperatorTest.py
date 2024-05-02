##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

class ArnoldOperatorTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		operator = GafferArnold.ArnoldShader()
		operator.loadShader( "switch_operator" )
		operator["parameters"]["index"].setValue( 0 )

		node = GafferArnold.ArnoldOperator()
		node["operator"].setInput( operator["out"] )

		for mode in node.Mode.values.values() :

			# Since there is no upstream operator, all modes
			# should have the same effect.
			node["mode"].setValue( mode )

			self.assertEqual(
				node["out"].globals()["option:ai:operator"],
				operator.attributes()["ai:operator"]
			)

	def testRejectsNonOperatorInputs( self ) :

		shader = GafferArnold.ArnoldShader()
		shader.loadShader( "flat" )

		node = GafferArnold.ArnoldOperator()
		self.assertFalse( node["operator"].acceptsInput( shader["out"] ) )

	def testModes( self ) :

		def order( scene ) :

			network = scene.globals()["option:ai:operator"]

			result = []
			shaderHandle = network.getOutput().shader
			while shaderHandle :
				result.append( network.getShader( shaderHandle ).parameters["index"].value )
				shaderHandle = network.input( ( shaderHandle, "input" ) ).shader

			result.reverse()
			return result

		operator1 = GafferArnold.ArnoldShader()
		operator1.loadShader( "switch_operator" )
		operator1["parameters"]["index"].setValue( 1 )

		operator2 = GafferArnold.ArnoldShader()
		operator2.loadShader( "switch_operator" )
		operator2["parameters"]["index"].setValue( 2 )

		operator3 = GafferArnold.ArnoldShader()
		operator3.loadShader( "switch_operator" )
		operator3["parameters"]["index"].setValue( 3 )

		node1 = GafferArnold.ArnoldOperator()
		node1["operator"].setInput( operator1["out"] )
		self.assertEqual( order( node1["out"] ), [ 1 ] )

		node2 = GafferArnold.ArnoldOperator()
		node2["in"].setInput( node1["out"] )
		node2["operator"].setInput( operator2["out"] )
		self.assertEqual( order( node2["out"] ), [ 2 ] )

		node2["mode"].setValue( GafferArnold.ArnoldOperator.Mode.InsertLast )
		self.assertEqual( order( node2["out"] ), [ 1, 2 ] )

		node2["mode"].setValue( GafferArnold.ArnoldOperator.Mode.InsertFirst )
		self.assertEqual( order( node2["out"] ), [ 2, 1 ] )

		node3 = GafferArnold.ArnoldOperator()
		node3["in"].setInput( node2["out"] )
		node3["operator"].setInput( operator3["out"] )
		self.assertEqual( order( node3["out"] ), [ 3 ] )

		node3["mode"].setValue( GafferArnold.ArnoldOperator.Mode.InsertLast )
		self.assertEqual( order( node3["out"] ), [ 2, 1, 3 ] )

		node3["mode"].setValue( GafferArnold.ArnoldOperator.Mode.InsertFirst )
		self.assertEqual( order( node3["out"] ), [ 3, 2, 1 ] )

if __name__ == "__main__":
	unittest.main()
