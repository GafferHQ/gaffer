##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferTest
import GafferCortex
import GafferCortexTest

class OpHolderTest( GafferTest.TestCase ) :

	def testType( self ) :

		n = GafferCortex.OpHolder()
		self.assertEqual( n.typeName(), "GafferCortex::OpHolder" )
		self.assertTrue( n.isInstanceOf( GafferCortex.ParameterisedHolderComputeNode.staticTypeId() ) )
		self.assertTrue( n.isInstanceOf( Gaffer.ComputeNode.staticTypeId() ) )
		self.assertTrue( n.isInstanceOf( Gaffer.DependencyNode.staticTypeId() ) )

	def testCompute( self ) :

		class MultiplyOp( IECore.Op ) :

			def __init__( self ) :

				IECore.Op.__init__( self, "", IECore.IntParameter( "result", "", 0 ) )

				self.parameters().addParameters( [

					IECore.IntParameter(
						"a",
						"",
						0
					),

					IECore.IntParameter(
						"b",
						"",
						0
					)

				] )

			def doOperation( self, args ) :

				return IECore.IntData( args["a"].value * args["b"].value )

		n = GafferCortex.OpHolder()
		n.setParameterised( MultiplyOp() )

		n["parameters"]["a"].setValue( 2 )
		n["parameters"]["b"].setValue( 20 )
		self.assertEqual( n["result"].getValue(), 40 )

		n["parameters"]["b"].setValue( 3 )
		self.assertEqual( n["result"].getValue(), 6 )

	def testAffects( self ) :

		n = GafferCortex.OpHolder()
		opSpec = GafferCortexTest.ParameterisedHolderTest.classSpecification( "files/sequenceRenumber", "IECORE_OP_PATHS" )[:-1]
		n.setOp( *opSpec )

		a = n.affects( n["parameters"]["offset"] )
		self.assertEqual( len( a ), 1 )
		self.assertTrue( a[0].isSame( n["result"] ) )

	def testSerialise( self ) :

		s = Gaffer.ScriptNode()

		s["op"] = GafferCortex.OpHolder()
		opSpec = GafferCortexTest.ParameterisedHolderTest.classSpecification( "files/sequenceRenumber", "IECORE_OP_PATHS" )[:-1]
		s["op"].setOp( *opSpec )

		ss = s.serialise()

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

	def testFileSequenceParameters( self ) :

		class TestOp( IECore.Op ) :

			def __init__( self ) :

				IECore.Op.__init__( self, "", IECore.IntParameter( "result", "", 0 ) )

				self.parameters().addParameter(

					IECore.FileSequenceParameter(
						"sequence",
						"",
						""
					)
				)

			def doOperation( self, args ) :

				return IECore.IntData( len( self["sequence"].getFileSequenceValue().fileNames() ) )

		holder = GafferCortex.OpHolder()
		holder.setParameterised( TestOp() )
		holder["parameters"]["sequence"].setValue( "test.###.exr 1-3" )

		self.assertEqual( holder["result"].getValue(), 3 )

	def testRunTimeTyped( self ) :

		n = GafferCortex.OpHolder()

		self.assertEqual( n.typeName(), "GafferCortex::OpHolder" )
		self.assertEqual( IECore.RunTimeTyped.typeNameFromTypeId( n.typeId() ), "GafferCortex::OpHolder" )
		self.assertEqual( IECore.RunTimeTyped.baseTypeId( n.typeId() ), GafferCortex.ParameterisedHolderComputeNode.staticTypeId() )

if __name__ == "__main__":
	unittest.main()
