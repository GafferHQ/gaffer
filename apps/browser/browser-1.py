##########################################################################
#
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import GafferUI

from Qt import QtWidgets

class browser( Gaffer.Application ) :

	def __init__( self ) :

		Gaffer.Application.__init__(
			self,
			"""
			A file browser with the ability to preview
			images and caches using Gaffer's viewers. This
			is the same as the Browser panel from the main
			gui application, but running as a standalone
			application.
			"""
		)

		self.parameters().addParameters(

			[
				IECore.PathParameter(
					"initialPath",
					"The path to browse to initially",
					"",
					allowEmptyString = True,
					check = IECore.PathParameter.CheckType.MustExist,
				)
			]

		)

		self.parameters().userData()["parser"] = IECore.CompoundObject(
			{
				"flagless" : IECore.StringVectorData( [ "initialPath" ] )
			}
		)

	def _run( self, args ) :

		scriptNode = Gaffer.ScriptNode()
		self.root()["scripts"].addChild( scriptNode )

		with GafferUI.Window( "Gaffer Browser" ) as self.__window :
			browser = GafferUI.BrowserEditor( scriptNode )

		if args["initialPath"].value :
			initialPath = os.path.abspath( args["initialPath"].value )
			browser.pathChooser().getPath().setFromString( initialPath )

		# centre the window on the primary screen at 3/4 size.
		## \todo Implement save/restore of geometry, and do all this without using Qt APIs
		# in the app itself.
		desktop = QtWidgets.QApplication.primaryScreen()
		geometry = desktop.availableGeometry()
		adjustment = geometry.size() / 8
		geometry.adjust( adjustment.width(), adjustment.height(), -adjustment.width(), -adjustment.height() )
		self.__window._qtWidget().setGeometry( geometry )

		self.__window.setVisible( True )

		GafferUI.EventLoop.mainEventLoop().start()

		return 0

IECore.registerRunTimeTyped( browser )
