##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer

class ObjectReader( Gaffer.ComputeNode ) :

	def __init__( self, name="ObjectReader" ) :
	
		Gaffer.ComputeNode.__init__( self, name )
		
		fileNamePlug = Gaffer.StringPlug( "fileName", Gaffer.Plug.Direction.In )
		self.addChild( fileNamePlug )
		self.__plugSetConnection = self.plugSetSignal().connect( Gaffer.WeakMethod( self.__plugSet ) )
		
		self.addChild( Gaffer.CompoundPlug( "parameters" ) )
		
		resultPlug = Gaffer.ObjectPlug( "out", Gaffer.Plug.Direction.Out, IECore.NullObject.defaultNullObject() )
		self.addChild( resultPlug )
				
		self.__reader = None
		self.__exposedParameters = IECore.CompoundParameter()
		self.__parameterHandler = Gaffer.CompoundParameterHandler( self.__exposedParameters )
 		self.__parameterHandler.setupPlug( self )

	def affects( self, input ) :
		
		outputs = []
		if self["parameters"].isAncestorOf( input ) or input.isSame( self["fileName"] ) :
			outputs.append( self["out"] )

		return outputs
	
	def hash( self, output, context, h ) :
	
		assert( output.isSame( self["out"] ) )

		self["fileName"].hash( h )
		self["parameters"].hash( h )
		
	def compute( self, plug, context ) :
	
		assert( plug.isSame( self["out"] ) )
		
		result = None
		if self.__reader is not None :
			self.__parameterHandler.setParameterValue()
			result = self.__reader.read()
		
		plug.setValue( result if result is not None else plug.defaultValue() )
	
	def parameterHandler( self ) :
	
		return self.__parameterHandler
		
	def __plugSet( self, plug ) :
	
		if plug.isSame( self["fileName"] ) :
			self.__ensureReader()
			
	def __ensureReader( self ) :
			
		fileName = self["fileName"].getValue()
		if fileName :
			
			if self.__reader is not None and self.__reader.canRead( fileName ) :
				self.__reader["fileName"].setTypedValue( fileName )
			else :
				self.__reader = None
				self.__exposedParameters.clearParameters()
				with IECore.IgnoredExceptions( RuntimeError ) :
					self.__reader = IECore.Reader.create( fileName )
					
				if self.__reader is not None :
					for parameter in self.__reader.parameters().values() :
						if parameter.name != "fileName" :
							self.__exposedParameters.addParameter( parameter )
				self.__parameterHandler.setupPlug( self )
				self["parameters"].setFlags( Gaffer.Plug.Flags.Dynamic, False )
		else :
		
			self.__reader = None
			self.__exposedParameters.clearParameters()
			self.__parameterHandler.setupPlug( self )

IECore.registerRunTimeTyped( ObjectReader, typeName = "Gaffer::ObjectReader" )
