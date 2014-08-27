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

import IECore
import Gaffer

class TextWriter( Gaffer.ExecutableNode ) :

	def __init__( self, name="TextWriter", requiresSequenceExecution = False ) :

		Gaffer.ExecutableNode.__init__( self, name )

		self.__requiresSequenceExecution = requiresSequenceExecution

		self.addChild( Gaffer.StringPlug( "fileName", Gaffer.Plug.Direction.In ) )
		self.addChild( Gaffer.StringPlug( "mode", defaultValue = "w", direction = Gaffer.Plug.Direction.In ) )
		self.addChild( Gaffer.StringPlug( "text", Gaffer.Plug.Direction.In ) )

	def execute( self ) :

		context = Gaffer.Context.current()
		fileName = context.substitute( self["fileName"].getValue() )
		text = self.__processText( context )
		with file( fileName, self["mode"].getValue() ) as f :
			f.write( text )

	def executeSequence( self, frames ) :

		if not self.__requiresSequenceExecution :
			Gaffer.ExecutableNode.executeSequence( self, frames )
			return

		context = Gaffer.Context( Gaffer.Context.current() )
		fileName = context.substitute( self["fileName"].getValue() )

		with file( fileName, self["mode"].getValue() ) as f :
			with context :
				for frame in frames :
					context.setFrame( frame )
					text = self.__processText( context )
					f.write( text )

	def hash( self, context ) :

		h = Gaffer.ExecutableNode.hash( self, context )
		h.append( context.getFrame() )
		h.append( context.get( "textWriter:replace", IECore.StringVectorData() ) )
		h.append( context.substitute( self["fileName"].getValue() ) )
		h.append( self["mode"].getValue() )
		h.append( context.substitute( self["text"].getValue() ) )

		return h

	def requiresSequenceExecution( self ) :

		return self.__requiresSequenceExecution

	def __processText( self, context ) :

		text = context.substitute( self["text"].getValue() )

		replace = context.get( "textWriter:replace", IECore.StringVectorData() )
		if replace and len(replace) == 2 :
			text = text.replace( replace[0], replace[1] )

		return text

IECore.registerRunTimeTyped( TextWriter, typeName = "GafferTest::TextWriter" )
