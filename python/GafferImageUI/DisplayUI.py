##########################################################################
#
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

import threading

import IECore

import Gaffer
import GafferUI

import GafferImage

__all__ = []

Gaffer.Metadata.registerNode(

	GafferImage.Display,

	"description",
	"""
	Interactively displays images as they are rendered.

	This node runs a server on a background thread,
	allowing it to receive images from both local and
	remote render processes. To set up a render to
	output to the Display node, use an Outputs node with
	an Interactive output configured to render to the
	same port as is specified on the Display node.
	""",

	plugs = {

		"port" : [

			"description",
			"""
			The port number on which to run the display server.
			Outputs which specify this port number will appear
			in this node - use multiple nodes with different
			port numbers to receive multiple images at once.
			""",

		],

	}

)

##########################################################################
# Code for triggering updates when data is received on a Display node
##########################################################################

## Here we're taking signals the Display node emits when it has new data, and using them
# to trigger a plugDirtiedSignal on the main ui thread. This is necessary because the Display
# receives data on a background thread, where we can't do ui stuff.

__plugsPendingUpdate = []
__plugsPendingUpdateLock = threading.Lock()

def __scheduleUpdate( plug, force = False ) :

	if not force :
		global __plugsPendingUpdate
		global __plugsPendingUpdateLock
		with __plugsPendingUpdateLock :
			for p in __plugsPendingUpdate :
				if plug.isSame( p ) :
					return

			__plugsPendingUpdate.append( plug )

	GafferUI.EventLoop.executeOnUIThread( lambda : __update( plug ) )

def __update( plug ) :
	
	# it's possible that this function can get called on a plug whose node has
	# been deleted, so we always check if the node exists:
	
	node = plug.node()
	if node:
		updateCountPlug = node["__updateCount"]
		updateCountPlug.setValue( updateCountPlug.getValue() + 1 )

	global __plugsPendingUpdate
	global __plugsPendingUpdateLock
	with __plugsPendingUpdateLock :
		__plugsPendingUpdate = [ p for p in __plugsPendingUpdate if not p.isSame( plug ) ]

__displayDataReceivedConnection = GafferImage.Display.dataReceivedSignal().connect( __scheduleUpdate )
__displayImageReceivedConnection = GafferImage.Display.imageReceivedSignal().connect( IECore.curry( __scheduleUpdate, force = True ) )
