##########################################################################
#  
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

class ParameterisedHolderTest( unittest.TestCase ) :

	def testCreateEmpty( self ) :
	
		n = Gaffer.ParameterisedHolderNode()
		self.assertEqual( n.getName(), "ParameterisedHolderNode" )
		self.assertEqual( n.getParameterised(), ( None, "", -1, "" ) )

	def testSetParameterisedWithoutClassLoader( self ) :
	
		n = Gaffer.ParameterisedHolderNode()
		op = IECore.SequenceRenumberOp()
		
		n.setParameterised( op )
		self.assertEqual( n.getParameterised(), ( op, "", -1, "" ) )
		
	def testSimplePlugTypes( self ) :
	
		n = Gaffer.ParameterisedHolderNode()
		op = IECore.SequenceRenumberOp()		
		n.setParameterised( op )
		
		self.failUnless( isinstance( n["parameters"]["src"], Gaffer.StringPlug ) )
		self.failUnless( isinstance( n["parameters"]["dst"], Gaffer.StringPlug ) )
		self.failUnless( isinstance( n["parameters"]["multiply"], Gaffer.IntPlug ) )
		self.failUnless( isinstance( n["parameters"]["offset"], Gaffer.IntPlug ) )
		
		self.assertEqual( n["parameters"]["src"].defaultValue(), "" )
		self.assertEqual( n["parameters"]["dst"].defaultValue(), "" )
		self.assertEqual( n["parameters"]["multiply"].defaultValue(), 1 )
		self.assertEqual( n["parameters"]["offset"].defaultValue(), 0 )
		
		self.assertEqual( n["parameters"]["src"].getValue(), "" )
		self.assertEqual( n["parameters"]["dst"].getValue(), "" )
		self.assertEqual( n["parameters"]["multiply"].getValue(), 1 )
		self.assertEqual( n["parameters"]["offset"].getValue(), 0 )
		
		for k in op.parameters().keys() :
			self.assertEqual( n["parameters"][k].defaultValue(), op.parameters()[k].defaultValue.value )
			
		with n.parameterModificationContext() as parameters :
		
			parameters["multiply"].setNumericValue( 10 )
			parameters["dst"].setTypedValue( "/tmp/s.####.exr" )
			
		self.assertEqual( n["parameters"]["multiply"].getValue(), 10 )
		self.assertEqual( n["parameters"]["dst"].getValue(), "/tmp/s.####.exr" )
		
		n["parameters"]["multiply"].setValue( 20 )
		n["parameters"]["dst"].setValue( "lalalal.##.tif" )
		
		n.setParameterisedValues()
		
		self.assertEqual( op["multiply"].getNumericValue(), 20 )
		self.assertEqual( op["dst"].getTypedValue(), "lalalal.##.tif" )
		
		
		
if __name__ == "__main__":
	unittest.main()
	
