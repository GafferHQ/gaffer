##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

import collections
import functools
import sys

import IECore

import Gaffer
import GafferUI

# Decorator to assist in Widget background processing.
# Usage example :
#
# ```
# class MyWidget( GafferUI.Widget ) :
#
# 	...
#
#	@GafferUI.BackgroundMethod()
#	def updateInBackground( self ) :
#
#		# When `updateInBackground()` is called
#		# on the UI thread, the decorator will
#		# run the function body asynchronously on
#		# a background thread.
#
#		result = heavyProcessing()
#		return result
#
#	@updateInBackground.preCall
#	def __updateInBackgroundPreCall( self )
#
#		# Will be called automatically on the UI
#		# thread before background processing starts.
#		# Typically used to indicate a "busy" status.
#
#		pass
#
#	@updateInBackground.postCall
#	def __updateInBackgroundPostCall( self, result )
#
#		# Called on the UI thread with the result
#		# of the background call (or any exception it
#		# throws). Typically used to display the result.
#		# It is guaranteed that every call to `preCall`
#		# is matched with a call to `postCall`, even if
#		# the background call is cancelled.
#
#		pass
# ```
class BackgroundMethod( object ) :

	__CurrentCall = collections.namedtuple( "__CurrentCall", [ "backgroundTask", "superceded" ] )

	def __init__( self, cancelWhenHidden = True ) :

		self.__cancelWhenHidden = cancelWhenHidden

	# Called to return the decorated method.
	def __call__( self, method ) :

		method.__preCall = None
		method.__postCall = None
		method.__plug = self.__plug

		def foregroundFunction( widget, result, superceded ) :

			if superceded.get() :
				return

			# It is possible that the widget was removed from the UI before
			# `foregroundFunction` got called. But it will have been kept
			# alive until now by this circular reference from `__CurrentCall` to the
			# BackgroundTask, which in turn holds a reference to `widget`. This
			# is crucial : without it, the widget can end up being destroyed
			# on the _background_ thread, where it is illegal to destroy a QWidget.
			# Here we break the cycle, allowing the `widget` to die on the UI thread
			# after exit from function.
			delattr( widget, method.__name__ + "__CurrentCall" )

			# Because of the above, it is possible that the QWidget part of the
			# `GafferUI.Widget has already been destroyed by Qt (due to the
			# Widget's parent dying first). So we must use `_qtObjectIsValid()`
			# to avoid invoking the `postCall` on an invalid widget.
			if method.__postCall is not None and GafferUI._qtObjectIsValid( widget._qtWidget() ) :
				method.__postCall( widget, result )

		def backgroundFunction( widget, superceded, *args, **kw ) :

			try :
				result = method( widget, *args, **kw )
			except :
				result = sys.exc_info()[1]
				# Avoid circular references that would prevent this
				# stack frame (and therefore `widget`) from dying.
				result.__traceback__ = None

			if not superceded.get() :
				Gaffer.ParallelAlgo.callOnUIThread( functools.partial( foregroundFunction, widget, result, superceded ) )

		@functools.wraps( method )
		def wrapper( widget, *args, **kw ) :

			assert( isinstance( widget, GafferUI.Widget ) )

			currentCall = getattr( widget, method.__name__ + "__CurrentCall", None )
			if currentCall is None :
				if method.__preCall is not None :
					method.__preCall( widget )
			else :
				# There's already a call in progress, but it has yet
				# to run the postCall. Mark it as superceded so that
				# it won't run the postCall. We can then "borrow" the
				# preCall that was made for it, so we don't need to make
				# one ourselves.
				currentCall.superceded.set( True )
				currentCall.backgroundTask.cancelAndWait()

			plug = method.__plug( widget )
			superceded = _ValueWrapper( False )

			backgroundTask = Gaffer.ParallelAlgo.callOnBackgroundThread(
				plug,
				functools.partial( backgroundFunction, widget, superceded, *args, **kw )
			)

			setattr( widget, method.__name__ + "__CurrentCall", self.__CurrentCall( backgroundTask, superceded ) )

			if self.__cancelWhenHidden :
				setattr(
					widget,
					method.__name__ + "__VisibilityChangedConnection",
					widget.visibilityChangedSignal().connect(
						functools.partial( self.__visibilityChanged, method = method, foregroundFunction = foregroundFunction ),
						scoped = True
					)
				)

		def preCall( f ) :
			method.__preCall = f

		def postCall( f ) :
			method.__postCall = f

		def plug( f ) :
			method.__plug = f

		def running( widget ) :
			return hasattr( widget, method.__name__ + "__CurrentCall" )

		wrapper.preCall = preCall
		wrapper.postCall = postCall
		wrapper.plug = plug
		wrapper.running = running

		return wrapper

	@staticmethod
	def __plug( widget ) :

		if hasattr( widget, "getPlug" ) :
			return widget.getPlug()
		else :
			return widget.plug()

	@staticmethod
	def __visibilityChanged( widget, method, foregroundFunction ) :

		if not widget.visible() :
			currentCall = getattr( widget, method.__name__ + "__CurrentCall", None )
			if currentCall is not None :
				currentCall.backgroundTask.cancel()
				if currentCall.backgroundTask.status() == Gaffer.BackgroundTask.Status.Cancelled :
					# Because we catch `IECore.Cancelled` ourselves in `backgroundFunction`,
					# the only way a Cancelled status can occur is if the cancellation
					# preempts the background task before it even runs. In this case we must run
					# the `foregroundFunction` so that the `preCall` we've already done has a
					# matching `postCall`.
					foregroundFunction( widget, IECore.Cancelled(), currentCall.superceded )

class _ValueWrapper( object ) :

	def __init__( self, value ) :

		self.__value = value

	def set( self, value ) :

		self.__value = value

	def get( self ) :

		return self.__value
