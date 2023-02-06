##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

class TextWriter( GafferDispatch.TaskNode ) :

	def __init__( self, name="TextWriter", requiresSequenceExecution = False ) :

		GafferDispatch.TaskNode.__init__( self, name )

		self.__requiresSequenceExecution = requiresSequenceExecution

		self.addChild( Gaffer.StringPlug( "fileName", Gaffer.Plug.Direction.In ) )
		self.addChild( Gaffer.StringPlug( "mode", defaultValue = "w", direction = Gaffer.Plug.Direction.In ) )
		self.addChild( Gaffer.StringPlug( "text", Gaffer.Plug.Direction.In ) )

	def execute( self ) :

		context = Gaffer.Context.current()
		fileName = self["fileName"].getValue()

		directory = os.path.dirname( fileName )
		if directory :
			try :
				os.makedirs( directory )
			except OSError :
				# makedirs very unhelpfully raises an exception if
				# the directory already exists, but it might also
				# raise if it fails. we reraise only in the latter case.
				if not os.path.isdir( directory ) :
					raise

		text = self.__processText( context )
		with open( fileName, self["mode"].getValue(), encoding = "utf-8" ) as f :
			f.write( text )

	def executeSequence( self, frames ) :

		if not self.__requiresSequenceExecution :
			GafferDispatch.TaskNode.executeSequence( self, frames )
			return

		context = Gaffer.Context( Gaffer.Context.current() )
		fileName = self["fileName"].getValue()

		with open( fileName, self["mode"].getValue(), encoding = "utf-8" ) as f :
			with context :
				for frame in frames :
					context.setFrame( frame )
					text = self.__processText( context )
					f.write( text )

	def hash( self, context ) :

		h = GafferDispatch.TaskNode.hash( self, context )
		h.append( context.getFrame() )
		h.append( context.get( "textWriter:replace", IECore.StringVectorData() ) )
		self["fileName"].hash( h )
		self["mode"].hash( h )
		self["text"].hash( h )

		return h

	def requiresSequenceExecution( self ) :

		return self.__requiresSequenceExecution

	def __processText( self, context ) :

		text = self["text"].getValue()
		replace = context.get( "textWriter:replace", IECore.StringVectorData() )
		if replace and len(replace) == 2 :
			text = text.replace( replace[0], replace[1] )

		return text

IECore.registerRunTimeTyped( TextWriter, typeName = "GafferDispatchTest::TextWriter" )
