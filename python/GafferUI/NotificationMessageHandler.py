##########################################################################
#
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

from Qt import QtGui

class NotificationMessageHandler( IECore.MessageHandler ) :

	# we want to keep the windows we create alive beyond
	# the lifetime of the handler itself, so they can remain
	# on screen until the user is done with them, so we keep
	# them in this set. they're removed when the user closes the
	# window
	__windows = set()

	def __init__( self, windowTitle = "Notifications" ) :

		IECore.MessageHandler.__init__( self )

		self.__window = None
		self.__windowTitle = windowTitle

	def handle( self, level, context, msg ) :

		if self.__window is None :
			self.__window = _Window( self.__windowTitle )
			self.__window.closedSignal().connect( NotificationMessageHandler.__windowClosed, scoped = False )
			NotificationMessageHandler.__windows.add( self.__window )

		self.__window.appendMessage( level, context, msg )

	def __exit__( self, type, value, traceBack ) :

		IECore.MessageHandler.__exit__( self, type, value, traceBack )
		if self.__window :
			self.__window.setVisible( True )

	@classmethod
	def __windowClosed( cls, window ) :

		cls.__windows.remove( window )

class _Window( GafferUI.Window ) :

	def __init__( self, title ) :

		GafferUI.Window.__init__( self, title, borderWidth = 8 )

		self.setChild( GafferUI.MessageWidget() )

		self.setResizeable( True )

	def appendMessage( self, level, context, message ) :

		self.getChild().messageHandler().handle( level, context, message )
