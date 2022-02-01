##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
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
import GafferUI

class view( Gaffer.Application ) :

	def __init__( self ) :

		Gaffer.Application.__init__(
			self,
			"""
			Uses Gaffer's viewers and widgets to provide
			a preview of a file. This is equivalent to the
			preview pane in the Browser panel or the browser
			app.
			"""
		)

		self.parameters().addParameters(

			[
				IECore.StringVectorParameter(
					name = "files",
					description = "A list of files to view.",
					defaultValue = IECore.StringVectorData()
				)
			]

		)

		self.parameters().userData()["parser"] = IECore.CompoundObject(
			{
				"flagless" : IECore.StringVectorData( [ "files" ] )
			}
		)

	def _run( self, args ) :

		if len( args["files"] ) < 1 or len( args["files"] ) > 2 :

			raise Exception( "Must view exactly one file." )

		self.__window = GafferUI.Window(
			title = "Gaffer Viewer",
			sizeMode = GafferUI.Window.SizeMode.Manual,
			borderWidth = 6
		)

		self.__window.setChild(
			GafferUI.CompoundPathPreview(
				Gaffer.FileSystemPath( args["files"][0] )
			)
		)

		self.__closedConnection = self.__window.closedSignal().connect( Gaffer.WeakMethod( self.__closed ), scoped = True )

		## \todo The window doesn't appear without this naughtiness. I think we either need to
		# add a similar method in the public interface, or maybe make a SizeConstraintContainer
		# or something along those lines.
		self.__window._qtWidget().setMinimumSize( 300, 200 )
		self.__window.setVisible( True )

		GafferUI.EventLoop.mainEventLoop().start()

		return 0

	def __closed( self, window ) :

		GafferUI.EventLoop.mainEventLoop().stop()

IECore.registerRunTimeTyped( view )
