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

import os
import subprocess
import pathlib
import unittest

import IECore

import Gaffer
import GafferTest
import GafferML

## \todo Test cancellation. For this, we need a model that takes long enough to compute
# but is small enough to package with the tests.
class InferenceTest( GafferTest.TestCase ) :

	def testLoadModel( self ) :

		script = Gaffer.ScriptNode()

		script["inference"] = GafferML.Inference()
		script["inference"]["model"].setValue( pathlib.Path( __file__ ).parent / "models" / "add.onnx" )
		script["inference"].loadModel()

		def assertLoaded( inference ) :

			self.assertEqual( inference["in"].keys(), [ "in0", "in1" ] )
			self.assertIsInstance( inference["in"]["in0"], GafferML.TensorPlug )
			self.assertIsInstance( inference["in"]["in1"], GafferML.TensorPlug )
			self.assertEqual( Gaffer.Metadata.value( inference["in"]["in0"], "label" ), "x" )
			self.assertEqual( Gaffer.Metadata.value( inference["in"]["in1"], "label" ), "y" )

			self.assertEqual( inference["out"].keys(), [ "out0" ] )
			self.assertIsInstance( inference["out"]["out0"], GafferML.TensorPlug )
			self.assertEqual( Gaffer.Metadata.value( inference["out"]["out0"], "label" ), "sum" )

		assertLoaded( script["inference"] )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )
		assertLoaded( script2["inference"] )

	def testCompute( self ) :

		inference = GafferML.Inference()
		inference["model"].setValue( pathlib.Path( __file__ ).parent / "models" / "add.onnx" )
		inference.loadModel()

		inference["in"][0].setValue(
			GafferML.Tensor( IECore.FloatVectorData( [ 1 ] * 60 ), [ 3, 4, 5 ] )
		)

		inference["in"][1].setValue(
			GafferML.Tensor( IECore.FloatVectorData( [ 2 ] * 60 ), [ 3, 4, 5 ] )
		)

		self.assertEqual(
			inference["out"][0].getValue().asData(),
			IECore.FloatVectorData( [ 3 ] * 60 )
		)

		inference["in"][1].setValue(
			GafferML.Tensor( IECore.FloatVectorData( [ 3 ] * 60 ), [ 3, 4, 5 ] )
		)

		self.assertEqual(
			inference["out"][0].getValue().asData(),
			IECore.FloatVectorData( [ 4 ] * 60 )
		)

	def testComputeError( self ) :

		inference = GafferML.Inference()
		inference["model"].setValue( pathlib.Path( __file__ ).parent / "models" / "add.onnx" )
		inference.loadModel()

		inference["in"][0].setValue(
			GafferML.Tensor( IECore.FloatVectorData( [ 1 ] * 60 ), [ 60 ] )
		)

		inference["in"][1].setValue(
			GafferML.Tensor( IECore.FloatVectorData( [ 2 ] * 60 ), [ 3, 4, 5 ] )
		)

		with self.assertRaisesRegex( Gaffer.ProcessException, "Invalid rank for input" ) :
			inference["out"][0].getValue()

	def testModelSearchPaths( self ) :

		node = GafferML.Inference()
		node["model"].setValue( "add.onnx" )

		testPath = str( pathlib.Path( __file__ ).parent / "models" )
		if os.environ.get( "GAFFERML_MODEL_PATHS", "" ) != testPath :

			self.assertRaises( RuntimeError, node.loadModel )
			env = os.environ.copy()
			env["GAFFERML_MODEL_PATHS"] = testPath
			try :
				subprocess.check_output(
					[ str( Gaffer.executablePath() ), "test", "GafferMLTest.InferenceTest.testModelSearchPaths" ],
					env = env, stderr = subprocess.STDOUT
				)
			except subprocess.CalledProcessError as e :
				self.fail( e.output )

		else :

			node.loadModel()
			self.assertEqual( len( node["in"] ), 2 )
			self.assertEqual( len( node["out"] ), 1 )

	def testLoadModelKeepsConnections( self ) :

		dataToTensor1 = GafferML.DataToTensor()
		dataToTensor2 = GafferML.DataToTensor()
		destinationPlug = GafferML.TensorPlug()

		inference = GafferML.Inference()
		inference["model"].setValue( pathlib.Path( __file__ ).parent / "models" / "add.onnx" )
		inference.loadModel()

		inference["in"][0].setInput( dataToTensor1["tensor"] )
		inference["in"][1].setInput( dataToTensor2["tensor"] )
		destinationPlug.setInput( inference["out"][0] )

		inference.loadModel()

		self.assertTrue( inference["in"][0].getInput().isSame( dataToTensor1["tensor"] ) )
		self.assertTrue( inference["in"][1].getInput().isSame( dataToTensor2["tensor"] ) )
		self.assertTrue( destinationPlug.getInput().isSame( inference["out"][0] ) )

if __name__ == "__main__":
	unittest.main()
