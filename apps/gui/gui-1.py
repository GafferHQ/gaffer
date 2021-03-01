##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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
import gc
import functools

import IECore

import Gaffer
import GafferUI

class gui( Gaffer.Application ) :

	def __init__( self ) :

		Gaffer.Application.__init__(
			self,
			"""
			A graphical user interface for editing node graphs. This is
			the primary user facing Gaffer application.
			"""
		)

		self.parameters().addParameters(

			[
				IECore.StringVectorParameter(
					name = "scripts",
					description = "A list of scripts to edit.",
					defaultValue = IECore.StringVectorData(),
				),

				IECore.BoolParameter(
					name = "fullScreen",
					description = "Opens the UI in full screen mode.",
					defaultValue = False,
				),
			]

		)

		self.parameters().userData()["parser"] = IECore.CompoundObject(
			{
				"flagless" : IECore.StringVectorData( [ "scripts" ] )
			}
		)

		self.__setupClipboardSync()

	def _run( self, args ) :

		GafferUI.ScriptWindow.connect( self.root() )

		# Must start the event loop before adding scripts,
		# because `FileMenu.addScript()` may launch
		# interactive dialogues.
		GafferUI.EventLoop.addIdleCallback( functools.partial( self.__addScripts, args ) )
		GafferUI.EventLoop.mainEventLoop().start()

		return 0

	def __addScripts( self, args ) :

		if len( args["scripts"] ) :
			for fileName in args["scripts"] :
				GafferUI.FileMenu.addScript( self.root(), fileName )
			if not len( self.root()["scripts"] ) :
				# Loading was cancelled, in which case we should quit the app.
				GafferUI.EventLoop.mainEventLoop().stop()
				return False # Remove idle callback
		else :
			scriptNode = Gaffer.ScriptNode()
			Gaffer.NodeAlgo.applyUserDefaults( scriptNode )
			self.root()["scripts"].addChild( scriptNode )

		if args["fullScreen"].value :
			primaryScript = self.root()["scripts"][-1]
			primaryWindow = GafferUI.ScriptWindow.acquire( primaryScript )
			primaryWindow.setFullScreen( True )

		return False # Remove idle callback

	def __setupClipboardSync( self ) :

		## This function sets up two way syncing between the clipboard held in the Gaffer::ApplicationRoot
		# and the global QtGui.QClipboard which is shared with external applications, and used by the cut and paste
		# operations in GafferUI's underlying QWidgets. This is very useful, as it allows nodes to be copied from
		# the graph and pasted into emails/chats etc, and then copied out of emails/chats and pasted into the node graph.
		#
		## \todo I don't think this is the ideal place for this functionality. Firstly, we need it in all apps
		# rather than just the gui app. Secondly, we want a way of using the global clipboard using GafferUI
		# public functions without needing an ApplicationRoot. Thirdly, it's questionable that ApplicationRoot should
		# have a clipboard anyway - it seems like a violation of separation between the gui and non-gui libraries.
		# Perhaps we should abolish the ApplicationRoot clipboard and the ScriptNode cut/copy/paste routines, relegating
		# them all to GafferUI functionality?

		from Qt import QtWidgets

		self.__clipboardContentsChangedConnection = self.root().clipboardContentsChangedSignal().connect( Gaffer.WeakMethod( self.__clipboardContentsChanged ) )
		QtWidgets.QApplication.clipboard().dataChanged.connect( Gaffer.WeakMethod( self.__qtClipboardContentsChanged ) )
		self.__ignoreQtClipboardContentsChanged = False
		self.__qtClipboardContentsChanged() # Trigger initial sync

	def __clipboardContentsChanged( self, applicationRoot ) :

		assert( applicationRoot.isSame( self.root() ) )

		data = applicationRoot.getClipboardContents()

		from Qt import QtWidgets
		clipboard = QtWidgets.QApplication.clipboard()
		try :
			self.__ignoreQtClipboardContentsChanged = True # avoid triggering an unecessary copy back in __qtClipboardContentsChanged
			clipboard.setText( str( data ) )
		finally :
			self.__ignoreQtClipboardContentsChanged = False

	def __qtClipboardContentsChanged( self ) :

		if self.__ignoreQtClipboardContentsChanged :
			return

		from Qt import QtWidgets

		text = QtWidgets.QApplication.clipboard().text().encode( "utf-8" )
		if text :
			with Gaffer.BlockedConnection( self.__clipboardContentsChangedConnection ) :
				self.root().setClipboardContents( IECore.StringData( text ) )

IECore.registerRunTimeTyped( gui )
