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
	
	def testVectorTypedParameter( self ) :
	
		p = IECore.Parameterised( "" )
		
		p.parameters().addParameters(
			
			[
		
				IECore.IntVectorParameter( "iv", "", IECore.IntVectorData() ),
				IECore.FloatVectorParameter( "fv", "", IECore.FloatVectorData() ),
				IECore.StringVectorParameter( "sv", "", IECore.StringVectorData() ),
				IECore.V3fVectorParameter( "vv", "", IECore.V3fVectorData() ),
		
			]
			
		)	
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( p )
		
		self.assertEqual( ph["parameters"]["iv"].defaultValue(), IECore.IntVectorData() )
		self.assertEqual( ph["parameters"]["fv"].defaultValue(), IECore.FloatVectorData() )
		self.assertEqual( ph["parameters"]["sv"].defaultValue(), IECore.StringVectorData() )
		self.assertEqual( ph["parameters"]["vv"].defaultValue(), IECore.V3fVectorData() )
		
		self.assertEqual( ph["parameters"]["iv"].getValue(), IECore.IntVectorData() )
		self.assertEqual( ph["parameters"]["fv"].getValue(), IECore.FloatVectorData() )
		self.assertEqual( ph["parameters"]["sv"].getValue(), IECore.StringVectorData() )
		self.assertEqual( ph["parameters"]["vv"].getValue(), IECore.V3fVectorData() )
		
		with ph.parameterModificationContext() as parameters :
		
			parameters["iv"].setValue( IECore.IntVectorData( [ 1, 2, 3 ] ) )
			parameters["fv"].setValue( IECore.FloatVectorData( [ 1 ] ) )
			parameters["sv"].setValue( IECore.StringVectorData( [ "a" ] ) )
			parameters["vv"].setValue( IECore.V3fVectorData( [ IECore.V3f( 1, 2, 3 ) ] ) )
		
		self.assertEqual( ph["parameters"]["iv"].getValue(), IECore.IntVectorData( [ 1, 2, 3 ] ) )
		self.assertEqual( ph["parameters"]["fv"].getValue(), IECore.FloatVectorData( [ 1 ] ) )
		self.assertEqual( ph["parameters"]["sv"].getValue(), IECore.StringVectorData( [ "a" ] ) )	
		self.assertEqual( ph["parameters"]["vv"].getValue(), IECore.V3fVectorData( [ IECore.V3f( 1, 2, 3 ) ] ) )
		
		ph["parameters"]["iv"].setValue( IECore.IntVectorData( [ 2, 3, 4 ] ) )
		ph["parameters"]["fv"].setValue( IECore.FloatVectorData( [ 2 ] ) )
		ph["parameters"]["sv"].setValue( IECore.StringVectorData( [ "b" ] ) )
		ph["parameters"]["vv"].setValue( IECore.V3fVectorData( [ IECore.V3f( 10, 20, 30 ) ] ) )
		
		ph.setParameterisedValues()
		
		self.assertEqual( parameters["iv"].getValue(), IECore.IntVectorData( [ 2, 3, 4 ] ) )
		self.assertEqual( parameters["fv"].getValue(), IECore.FloatVectorData( [ 2 ] ) )
		self.assertEqual( parameters["sv"].getValue(), IECore.StringVectorData( [ "b" ] ) )
		self.assertEqual( parameters["vv"].getValue(), IECore.V3fVectorData( [ IECore.V3f( 10, 20, 30 ) ] ) )
		
	def testNoHostMapping( self ) :
	
		p = IECore.Parameterised( "" )
		
		p.parameters().addParameters(
			
			[
		
				IECore.IntParameter( "i1", "", 1, userData = { "noHostMapping" : IECore.BoolData( False ) } ),
				IECore.IntParameter( "i2", "", 2, userData = { "noHostMapping" : IECore.BoolData( True ) } ),
				IECore.IntParameter( "i3", "", 2 ),
		
			]
			
		)
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( p )
		
		self.failUnless( "i1" in ph["parameters"] )
		self.failIf( "i2" in ph["parameters"] )
		self.failUnless( "i3" in ph["parameters"] )
	
	def testCreateWithNonDefaultValues( self ) :
	
		p = IECore.Parameterised( "" )
		p.parameters().addParameter( IECore.IntParameter( "i1", "", 1, ) )
		
		p["i1"].setNumericValue( 10 )
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( p )
		
		self.assertEqual( ph["parameters"]["i1"].defaultValue(), 1 )
		self.assertEqual( ph["parameters"]["i1"].getValue(), 10 )
	
	def testCompoundNumericTypes( self ) :
	
		p = IECore.Parameterised( "" )
		
		p.parameters().addParameters(
		
			[
				IECore.V2iParameter( "v2i", "", IECore.V2i( 1, 2 ) ),
				IECore.V3fParameter( "v3f", "", IECore.V3f( 1, 2, 3 ) ),
				IECore.Color4fParameter( "color4f", "", IECore.Color4f( 0.25, 0.5, 0.75, 1 ) ),
			]
		
		)
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( p )
		
		self.assertEqual( ph["parameters"]["v2i"].defaultValue(), IECore.V2i( 1, 2 ) )
		self.assertEqual( ph["parameters"]["v3f"].defaultValue(), IECore.V3f( 1, 2, 3 ) )
		self.assertEqual( ph["parameters"]["color4f"].defaultValue(), IECore.Color4f( 0.25, 0.5, 0.75, 1 ) )
		
		self.assertEqual( ph["parameters"]["v2i"].getValue(), IECore.V2i( 1, 2 ) )
		self.assertEqual( ph["parameters"]["v3f"].getValue(), IECore.V3f( 1, 2, 3 ) )
		self.assertEqual( ph["parameters"]["color4f"].getValue(), IECore.Color4f( 0.25, 0.5, 0.75, 1 ) )
		
		ph["parameters"]["v2i"].setValue( IECore.V2i( 2, 3 ) )
		ph["parameters"]["v3f"].setValue( IECore.V3f( 4, 5, 6 ) )
		ph["parameters"]["color4f"].setValue( IECore.Color4f( 0.1, 0.2, 0.3, 0.5 ) )
		
		ph.setParameterisedValues()

		self.assertEqual( p["v2i"].getTypedValue(), IECore.V2i( 2, 3 ) )
		self.assertEqual( p["v3f"].getTypedValue(), IECore.V3f( 4, 5, 6 ) )
		self.assertEqual( p["color4f"].getTypedValue(), IECore.Color4f( 0.1, 0.2, 0.3, 0.5 ) )
		
if __name__ == "__main__":
	unittest.main()
	
