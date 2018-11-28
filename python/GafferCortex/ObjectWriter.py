##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferDispatch
import GafferCortex

class ObjectWriter( GafferDispatch.TaskNode ) :

	def __init__( self, name="ObjectWriter" ) :

		GafferDispatch.TaskNode.__init__( self, name )

		inPlug = Gaffer.ObjectPlug( "in", Gaffer.Plug.Direction.In, IECore.NullObject.defaultNullObject() )
		self.addChild( inPlug )

		fileNamePlug = Gaffer.FilePathPlug( "fileName", Gaffer.Plug.Direction.In )
		self.addChild( fileNamePlug )

		self.addChild( Gaffer.Plug( "parameters" ) )

		self.__writer = None
		self.__writerExtension = ""
		self.__exposedParameters = IECore.CompoundParameter()
		self.__parameterHandler = GafferCortex.CompoundParameterHandler( self.__exposedParameters )
		self.__parameterHandler.setupPlug( self )

		self.__plugSetConnection = self.plugSetSignal().connect( Gaffer.WeakMethod( self.__plugSet ), scoped = True )

	def parameterHandler( self ) :

		return self.__parameterHandler

	def hash( self, context ) :

		with context :
			if not self["fileName"].getValue() or self["in"].source() == self["in"] :
				return IECore.MurmurHash()

			h = GafferDispatch.TaskNode.hash( self, context )
			h.append( self["fileName"].hash() )
			h.append( self["in"].hash() )
			h.append( self.__parameterHandler.hash() )

			return h

	def execute( self ) :

		self.__ensureWriter()

		if self.__writer is None :
			raise RuntimeError( "No Writer" )

		self.__writer["object"].setValue( self["in"].getValue() )
		self.__writer.write()

	def __plugSet( self, plug ) :

		if plug.isSame( self["fileName"] ) or plug.isSame( self["in"] ) :
			self.__ensureWriter()

	def __ensureWriter( self ) :

		fileName = self["fileName"].getValue()
		if fileName :

			extension = os.path.splitext( fileName )[-1]
			if self.__writer is not None and extension==self.__writerExtension :

				self.__writer["fileName"].setTypedValue( fileName )

			else :

				self.__writer = None
				self.__exposedParameters.clearParameters()
				with IECore.IgnoredExceptions( RuntimeError ) :
					self.__writer = IECore.Writer.create( fileName )

				if self.__writer is not None :
					self.__writerExtension = extension
					for parameter in self.__writer.parameters().values() :
						if parameter.name not in ( "fileName", "object" ) :
							self.__exposedParameters.addParameter( parameter )

				self.__parameterHandler.setupPlug( self )

		else :

			self.__writer = None
			self.__exposedParameters.clearParameters()
			self.__parameterHandler.setupPlug( self )

		self["parameters"].setFlags( Gaffer.Plug.Flags.Dynamic, False )

IECore.registerRunTimeTyped( ObjectWriter, typeName = "GafferCortex::ObjectWriter" )
