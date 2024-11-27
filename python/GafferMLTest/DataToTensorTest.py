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

import IECore
import Gaffer
import GafferTest
import GafferML

class DataToTensorTest( GafferTest.TestCase ) :

	def testBeforeSetup( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = GafferML.DataToTensor()
		self.assertIsNone( script["node"].getChild( "data" ) )
		self.assertTrue( script["node"].canSetup( Gaffer.FloatVectorDataPlug() ) )
		self.assertEqual( script["node"]["tensor"].getValue(), GafferML.Tensor() )

		serialisation = script.serialise()
		self.assertNotIn( "setup", serialisation )

		script2 = Gaffer.ScriptNode()
		script2.execute( serialisation )
		self.assertIsNone( script2["node"].getChild( "data" ) )
		self.assertTrue( script2["node"].canSetup( Gaffer.FloatVectorDataPlug() ) )
		self.assertEqual( script2["node"]["tensor"].getValue(), GafferML.Tensor() )

	def testSetup( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = GafferML.DataToTensor()

		prototypeDataPlug = Gaffer.FloatVectorDataPlug()
		self.assertTrue( script["node"].canSetup( Gaffer.FloatVectorDataPlug() ) )
		script["node"].setup( prototypeDataPlug )
		self.assertIsInstance( script["node"]["data"], Gaffer.FloatVectorDataPlug )
		self.assertFalse( script["node"]["data"].isSame( prototypeDataPlug ) )
		self.assertFalse( script["node"].canSetup( prototypeDataPlug ) )

		serialisation = script.serialise()
		self.assertIn( "setup", serialisation )

		script2 = Gaffer.ScriptNode()
		script2.execute( serialisation )
		self.assertEqual( script2["node"].keys(), script["node"].keys() )
		self.assertIsInstance( script2["node"]["data"], Gaffer.FloatVectorDataPlug )
		self.assertFalse( script2["node"].canSetup( prototypeDataPlug ) )

	def testTensor( self ) :

		node = GafferML.DataToTensor()
		node.setup( Gaffer.FloatVectorDataPlug( defaultValue = IECore.FloatVectorData( [ 1, 2, 3 ] ) ) )

		tensor = node["tensor"].getValue()
		self.assertEqual( tensor.shape(), [ 3 ] )
		self.assertEqual( tensor.asData(), IECore.FloatVectorData( [ 1, 2, 3 ] ) )

	def testShapeModes( self ) :

		node = GafferML.DataToTensor()
		node.setup( Gaffer.V2iVectorDataPlug( defaultValue = IECore.V2iVectorData( [ imath.V2i( i ) for i in range( 0, 3 ) ] ) ) )

		tensor = node["tensor"].getValue()
		self.assertEqual( tensor.shape(), [ 3, 2 ] )

		node["shapeMode"].setValue( node.ShapeMode.Custom )
		node["shape"].setValue( IECore.Int64VectorData( [ 1, 1, 1, 6 ] ) )
		tensor = node["tensor"].getValue()
		self.assertEqual( tensor.shape(), [ 1, 1, 1, 6 ] )

if __name__ == "__main__" :
	unittest.main()
