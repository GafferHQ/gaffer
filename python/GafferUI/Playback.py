##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import enum
import math

import Gaffer
import GafferUI

from Qt import QtCore

## The Playback class controls a Context to facilitate animation
# playback. It provides methods for starting and stopping playback,
# controlling frame ranges and signalling changes in playback state.
# All UI elements requiring such functionality should operate using
# a Playback object to ensure synchronisation between elements.
class Playback( object ) :

	State = enum.Enum( "State", [ "PlayingForwards", "PlayingBackwards", "Scrubbing", "Stopped" ] )

	## Use acquire rather than this method.
	def __init__( self, __context ) :

		self.__context = __context
		self.__state = self.State.Stopped
		self.__frameRange = ( 1, 100 )

		self.__playTimer = QtCore.QTimer()
		self.__playTimer.timeout.connect( Gaffer.WeakMethod( self.__timerCallback ) )

		self.__stateChangedSignal = Gaffer.Signals.Signal1()
		self.__frameRangeChangedSignal = Gaffer.Signals.Signal1()

	__instances = []
	## Acquires the Playback instance for the specified
	# context. Playback is managed at a per-context level
	# so that Editors with different contexts may have
	# different playback states.
	@classmethod
	def acquire( cls, context ) :

		assert( isinstance( context, Gaffer.Context ) )

		for playbackContext, playback in cls.__instances :
			if context.isSame( playbackContext ) :
				return playback

		playback = Playback( context )
		cls.__instances.append( ( context, playback ) )

		return playback

	## Returns the context this object is operating on.
	def context( self ) :

		return self.__context

	## Can be called to initiate or stop playback,
	# or to signify that the current frame is about to
	# be scrubbed arbitrarily backwards and forwards.
	def setState( self, state ) :

		if state == self.__state :
			return

		self.__state = state

		if self.__state == self.State.Stopped :
			self.__playTimer.stop()
		elif self.__state in ( self.State.PlayingForwards, self.State.PlayingBackwards ) :
			self.__playTimer.start()

		self.stateChangedSignal()( self )

	def getState( self ) :

		return self.__state

	def stateChangedSignal( self ) :

		return self.__stateChangedSignal

	def setFrameRange( self, startFrame, endFrame ) :

		newRange = ( startFrame, endFrame )
		if newRange == self.__frameRange :
			return

		self.__frameRange = newRange

		self.frameRangeChangedSignal()( self )

	def getFrameRange( self ) :

		return self.__frameRange

	def frameRangeChangedSignal( self ) :

		return self.__frameRangeChangedSignal

	## Increments the current frame, wrapping around
	# if the new frame would be outside the frame range.
	# Also sets the current state to Stopped in the event
	# that it was playing.
	def incrementFrame( self, increment=1 ) :

		self.setState( self.State.Stopped )
		self.__incrementFrame( increment )

	def __timerCallback( self ) :

		increment = None
		if self.__state == self.State.PlayingForwards :
			increment = 1
		elif self.__state == self.State.PlayingBackwards :
			increment = -1

		if increment is None :
			return

		self.__incrementFrame( increment )

	def __incrementFrame( self, increment ) :

		frame = self.context().getFrame() + increment
		if frame > self.__frameRange[1] :
			frame = self.__frameRange[0] + ( frame - math.floor( frame ) )
		elif frame < self.__frameRange[0] :
			frame = self.__frameRange[1] + ( frame - math.floor( frame ) )

		self.context().setFrame( frame )
