##########################################################################
#  
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

from __future__ import with_statement

import unittest

import IECore

import Gaffer

class ParameterHandlerTest( unittest.TestCase ) :

	def testFactory( self ) :

		p = IECore.IntParameter( "i", "d", 10 )
		
		n = Gaffer.Node()
		h = Gaffer.ParameterHandler.create( p )
		h.setupPlug( n )
		
		self.failUnless( isinstance( h, Gaffer.ParameterHandler ) )
		self.failUnless( isinstance( n["i"], Gaffer.IntPlug ) )
		
	def testCustomHandler( self ) :
	
		class CustomParameter( IECore.IntParameter ) :
		
			def __init__( self, name, description, defaultValue ) :
			
				IECore.IntParameter.__init__( self, name, description, defaultValue )
		
		IECore.registerRunTimeTyped( CustomParameter )
				
		class CustomHandler( Gaffer.ParameterHandler ) :
		
			def __init__( self, parameter ) :
						
				Gaffer.ParameterHandler.__init__( self )
				
				self.__parameter = parameter
				self.__plug = None
				
			def parameter( self ) :
			
				return self.__parameter
			
			def setupPlug( self, plugParent, direction ) :
				
				self.__plug = plugParent.getChild( self.__parameter.name )
				if not isinstance( self.__plug, Gaffer.IntPlug ) or self.__plug.direction() != direction :
					self.__plug = Gaffer.IntPlug(
						self.__parameter.name,
						Gaffer.Plug.Direction.In,
						self.__parameter.numericDefaultValue,
						self.__parameter.minValue,
						self.__parameter.maxValue
					)
					
				plugParent[self.__parameter.name] = self.__plug
			
			def plug( self ) :
			
				return self.__plug
				
			def setParameterValue( self ) :
			
				self.__parameter.setValue( self.__plug.getValue() * 10 )
				
			def setPlugValue( self ) :
							
				self.__plug.setValue( self.__parameter.getNumericValue() / 10 )
						
		Gaffer.ParameterHandler.registerParameterHandler( CustomParameter.staticTypeId(), CustomHandler )
		
		p = IECore.Parameterised( "" )
		p.parameters().addParameter(
			
			CustomParameter( 
				
				"i",
				"d",
				10
			
			)
		
		)
		
		ph = Gaffer.ParameterisedHolderNode()
		ph.setParameterised( p )
		
		self.assertEqual( ph["parameters"]["i"].getValue(), 1 )
		
		with ph.parameterModificationContext() as parameters :
		
			p["i"].setNumericValue( 100 )
			
		self.assertEqual( ph["parameters"]["i"].getValue(), 10 )
		
		ph["parameters"]["i"].setValue( 1000 )
		
		ph.setParameterisedValues()
		
		self.assertEqual( p["i"].getNumericValue(), 10000 )
	
	def testPlugMethod( self ) :

		p = IECore.IntParameter( "i", "d", 10 )
		
		n = Gaffer.Node()
		h = Gaffer.ParameterHandler.create( p )
		h.setupPlug( n )
		
		self.assertEqual( h.plug().getName(), "i" )
		self.failUnless( h.plug().parent().isSame( n ) )
		
	def testCompoundParameterHandler( self ) :
		
		c = IECore.CompoundParameter(
			
			"c",
			"",
			
			[
				IECore.IntParameter( "i", "" ),
				IECore.FloatParameter( "f", "" )			
			]
	
		)
		
		n = Gaffer.Node()
		
		h = Gaffer.CompoundParameterHandler( c )
		h.setupPlug( n )
		
		self.failUnless( h.childParameterHandler( c["i"] ).parameter().isSame( c["i"] ) )
		self.failUnless( h.childParameterHandler( c["f"] ).parameter().isSame( c["f"] ) )
	
	def testReadOnly( self ) :
	
		p = IECore.IntParameter( "i", "d", 10 )
		
		n = Gaffer.Node()
		h = Gaffer.ParameterHandler.create( p )
		h.setupPlug( n )
		
		self.failIf( h.plug().getFlags( Gaffer.Plug.Flags.ReadOnly ) )
		
		p.userData()["gaffer"] = IECore.CompoundObject( {
			"readOnly" : IECore.BoolData( True ),
		} )
		
		h.setupPlug( n )
		self.failUnless( h.plug().getFlags( Gaffer.Plug.Flags.ReadOnly ) )
		
if __name__ == "__main__":
	unittest.main()
	
