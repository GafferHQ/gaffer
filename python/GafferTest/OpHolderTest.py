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

class OpHolderTest( unittest.TestCase ) :

	def testType( self ) :
	
		n = Gaffer.OpHolder()
		self.assertEqual( n.typeName(), "Gaffer::OpHolder" )
		self.failUnless( n.isInstanceOf( Gaffer.ParameterisedHolderComputeNode.staticTypeId() ) )
		self.failUnless( n.isInstanceOf( Gaffer.ComputeNode.staticTypeId() ) )
		self.failUnless( n.isInstanceOf( Gaffer.DependencyNode.staticTypeId() ) )
		
	def testCompute( self ) :
	
		m = IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) )
		self.failUnless( "P" in m )
		self.failUnless( "renamed" not in m )
		
		n = Gaffer.OpHolder()
		opSpec = GafferTest.ParameterisedHolderTest.classSpecification( "primitive/renameVariables", "IECORE_OP_PATHS" )[:-1]
		n.setOp( *opSpec )
		
		n["parameters"]["input"].setValue( m )
		n["parameters"]["names"].setValue( IECore.StringVectorData( [ "P renamed" ] ) )
		
		m2 = n["result"].getValue()
				
		self.failUnless( "P" not in m2 )
		self.failUnless( "renamed" in m2 )
		
		n["parameters"]["names"].setValue( IECore.StringVectorData( [ "P renamedAgain" ] ) )

		self.failUnless( "P" not in m2 )
		self.failUnless( "renamed" in m2 )
		
	def testAffects( self ) :
	
		n = Gaffer.OpHolder()
		opSpec = GafferTest.ParameterisedHolderTest.classSpecification( "primitive/renameVariables", "IECORE_OP_PATHS" )[:-1]
		n.setOp( *opSpec )
		
		a = n.affects( n["parameters"]["input"] )
		self.assertEqual( len( a ), 1 )
		self.failUnless( a[0].isSame( n["result"] ) )
		
	def testSerialise( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["op"] = Gaffer.OpHolder()
		opSpec = GafferTest.ParameterisedHolderTest.classSpecification( "primitive/renameVariables", "IECORE_OP_PATHS" )[:-1]
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
	
		holder = Gaffer.OpHolder()
		holder.setParameterised( TestOp() )
		holder["parameters"]["sequence"].setValue( "test.###.exr 1-3" )
		
		self.assertEqual( holder["result"].getValue(), 3 )
	
	def testRunTimeTyped( self ) :
	
		n = Gaffer.OpHolder()
		
		self.assertEqual( n.typeName(), "Gaffer::OpHolder" )
		self.assertEqual( IECore.RunTimeTyped.typeNameFromTypeId( n.typeId() ), "Gaffer::OpHolder" )
		self.assertEqual( IECore.RunTimeTyped.baseTypeId( n.typeId() ), Gaffer.ParameterisedHolderComputeNode.staticTypeId() )
								
if __name__ == "__main__":
	unittest.main()
	
