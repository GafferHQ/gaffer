##########################################################################
#
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

import weakref
import threading

import IECore

import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )

## This abstract class provides a base for all PathPreviewWidgets which may
# take some time in generating the preview, and would therefore like to do it
# on a background thread.
class DeferredPathPreview( GafferUI.PathPreviewWidget ) :

	def __init__( self, displayWidget, path ) :

		self.__tabbedContainer = GafferUI.TabbedContainer()

		GafferUI.PathPreviewWidget.__init__( self, self.__tabbedContainer, path )

		self.__tabbedContainer.setTabsVisible( False )
		self.__tabbedContainer.append( GafferUI.BusyWidget( size = 25 ) ) # for when we're loading
		self.__tabbedContainer.append( displayWidget ) # for when we loaded ok
		self.__tabbedContainer.append( GafferUI.Spacer( size = IECore.V2i( 10 ) ) ) # for when we didn't load ok

		# a timer we use to display the busy status if loading takes too long
		self.__busyTimer = QtCore.QTimer()
		self.__busyTimer.setSingleShot( True )
		self.__busyTimer.timeout.connect( IECore.curry( DeferredPathPreview.__displayBusy, weakref.ref( self ) ) )

	def _updateFromPath( self ) :

		if self.isValid() :
			# start loading in the background. whenever we spawn activity on another
			# thread (or schedule a timer as above), we do so using only a weak reference
			# to ourselves. this means that we can die appropriately even while loading
			# something.
			thread = threading.Thread( target = IECore.curry( DeferredPathPreview.__load, weakref.ref( self ) ) )
			thread.daemon = True
			thread.start()
			# start the timer to show the busy widget if loading takes too long
			self.__busyTimer.start( 500 )
		else :
			DeferredPathPreview.__display( weakref.ref( self ), None )

	## Must be implemented in subclasses to load something
	# from the path and return it. The assumption is that this
	# will take some time, so this function will be called on
	# a separate thread.
	def _load( self ) :

		raise NotImplementedError

	## Must be implemented in subclasses to update the display widget with
	# the object just loaded with _load().
	def _deferredUpdate( self, loaded ) :

		raise NotImplementedError

	@staticmethod
	def __load( selfWeakRef ) :

		self = selfWeakRef()
		if self is None :
			return

		o = self._load()
		GafferUI.EventLoop.executeOnUIThread( IECore.curry( DeferredPathPreview.__display, selfWeakRef, o ) )

	@staticmethod
	def __display( selfWeakRef, o ) :

		self = selfWeakRef()
		if self is None :
			return

		self.__busyTimer.stop()

		if o is not None :
			self._deferredUpdate( o )
			self.__tabbedContainer.setCurrent( self.__tabbedContainer[1] )
		else :
			self.__tabbedContainer.setCurrent( self.__tabbedContainer[2] )

	@staticmethod
	def __displayBusy( selfWeakRef ) :

		self = selfWeakRef()
		if self is None :
			return

		self.__tabbedContainer.setCurrent( self.__tabbedContainer[0] )
