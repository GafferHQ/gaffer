##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

class ProceduralHolderTest( unittest.TestCase ) :

	def testType( self ) :
	
		n = Gaffer.ProceduralHolder()
		self.assertEqual( n.typeName(), "ProceduralHolder" )
		self.failUnless( n.isInstanceOf( Gaffer.ParameterisedHolderNode.staticTypeId() ) )
		self.failUnless( n.isInstanceOf( Gaffer.Node.staticTypeId() ) )
		
	def testCompute( self ) :
	
		n = Gaffer.ProceduralHolder()
		classSpec = GafferTest.ParameterisedHolderTest.classSpecification( "read", "IECORE_PROCEDURAL_PATHS" )[:-1]
		n.setProcedural( *classSpec )
		
		p = n["output"].getValue()
				
		self.failUnless( isinstance( p, IECore.ReadProcedural ) )
		self.assertEqual( p.parameters().getValue(), n.getProcedural().parameters().getValue() )
		
	def testDirty( self ) :
	
		n = Gaffer.ProceduralHolder()
		classSpec = GafferTest.ParameterisedHolderTest.classSpecification( "read", "IECORE_PROCEDURAL_PATHS" )[:-1]
		n.setProcedural( *classSpec )
		
		self.failUnless( n["output"].getDirty() )
		
		n["output"].getValue()
		
		self.failIf( n["output"].getDirty() )
		
		n["parameters"]["motion"]["blur"].setValue( False )
		
		self.failUnless( n["output"].getDirty() )

		n["output"].getValue()
		
		self.failIf( n["output"].getDirty() )		
	
	def testRunTimeTyped( self ) :
	
		n = Gaffer.ProceduralHolder()
		
		self.assertEqual( n.typeName(), "ProceduralHolder" )
		self.assertEqual( IECore.RunTimeTyped.typeNameFromTypeId( n.typeId() ), "ProceduralHolder" )
		self.assertEqual( IECore.RunTimeTyped.baseTypeId( n.typeId() ), Gaffer.ParameterisedHolderNode.staticTypeId() )
								
if __name__ == "__main__":
	unittest.main()
	
