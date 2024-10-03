##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
import functools
import collections

import IECore

import GafferUI

class LazyMethod( object ) :

	__PendingCall = collections.namedtuple( "__PendingCall", [ "args", "kw" ] )

	# Using `deferUntilPlaybackStops` requires that the widget has a
	# `scriptNode()` method that returns the appropriate ScriptNode from which
	# to acquire a Playback object.
	def __init__( self, deferUntilVisible = True, deferUntilIdle = True, deferUntilPlaybackStops = False, replacePendingCalls = True ) :

		self.__deferUntilVisible = deferUntilVisible
		self.__deferUntilIdle = deferUntilIdle
		self.__deferUntilPlaybackStops = deferUntilPlaybackStops
		self.__replacePendingCalls = replacePendingCalls

	# Called to return the decorated method.
	def __call__( self, method ) :

		@functools.wraps( method )
		def wrapper( widget, *args, **kw ) :

			assert( isinstance( widget, GafferUI.Widget ) )

			# Update the list of pending method calls for this widget.

			try :
				pendingCalls = getattr( widget, method.__name__ + "__PendingCalls" )
			except AttributeError :
				pendingCalls = []
				setattr( widget, method.__name__ + "__PendingCalls", pendingCalls )

			hadPendingCalls = bool( pendingCalls )
			if self.__replacePendingCalls :
				del pendingCalls[:]

			pendingCalls.append( self.__PendingCall( args, kw ) )

			# Arrange to make the pending calls at an appropriate time.

			if hadPendingCalls :

				# The previous call will have set up the machinery to
				# make the pending call, so we don't need to.
				return

			elif self.__deferUntilVisible and not widget.visible() :

				setattr(
					widget,
					method.__name__ + "__VisibilityChangedConnection",
					widget.visibilityChangedSignal().connect(
						functools.partial( self.__visibilityChanged, method = method ),
						scoped = True
					)
				)

			elif self.__deferUntilPlaybackStops and self.__playback( widget ).getState() != GafferUI.Playback.State.Stopped :

				setattr(
					widget,
					method.__name__ + "__PlaybackStateChangedConnection",
					self.__playback( widget ).stateChangedSignal().connect(
						functools.partial( self.__playbackStateChanged, widgetWeakref = weakref.ref( widget ), method = method ),
						scoped = True
					)
				)

			elif self.__deferUntilIdle :

				GafferUI.EventLoop.addIdleCallback( functools.partial( self.__idle, weakref.ref( widget ), method ) )

			else :

				self.__doPendingCalls( widget, method )

		def flush( widget ) :

			self.__doPendingCalls( widget, method )

		wrapper.flush = flush

		return wrapper

	@classmethod
	def __playback( cls, widget ) :

		return GafferUI.Playback.acquire(
			widget.scriptNode().context()
		)

	@classmethod
	def __visibilityChanged( cls, widget, method ) :

		if not widget.visible() :
			return

		cls.__doPendingCalls( widget, method )

	@classmethod
	def __playbackStateChanged( cls, playback, widgetWeakref, method ) :

		if playback.getState() != playback.State.Stopped :
			return

		widget = widgetWeakref()
		if widget is None :
			return

		cls.__doPendingCalls( widget, method )

	@classmethod
	def __idle( cls, widgetWeakref, method ) :

		widget = widgetWeakref()
		if widget is None or not GafferUI._qtObjectIsValid( widget._qtWidget() ):
			return

		cls.__doPendingCalls( widget, method )

		return False # Remove idle callback

	@classmethod
	def __doPendingCalls( cls, widget, method ) :

		pendingCalls = getattr( widget, method.__name__ + "__PendingCalls", None )
		if pendingCalls is None :
			return

		while pendingCalls :
			pendingCall = pendingCalls.pop( 0 )
			method( widget, *pendingCall.args, **pendingCall.kw )
