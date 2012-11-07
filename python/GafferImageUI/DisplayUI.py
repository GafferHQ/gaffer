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

import GafferUI

import GafferImage

__all__ = []

## Here we're taking signals the Display node emits when it has new data, and using them
# to trigger a plugDirtiedSignal on the main ui thread. This is necessary because the Display
# receives data on a background thread, where we can't do ui stuff.

__dataReceivedCount = 0
def __displayDataReceived( plug ) :

	global __dataReceivedCount
	
	## \todo We're not emitting on every update because it's quite slow doing that. When we have a proper
	# fleshed out view class, we'll be able to ignore updates unless we've processed the previous update.
	# We should also have an extra signal on ImageNode classes, which tells you which specific area of the
	# image has changed so that the updates can be much quicker.
	if __dataReceivedCount % 50 == 0:
		GafferUI.EventLoop.executeOnUIThread( lambda : plug.node().plugDirtiedSignal()( plug ) )
	
	__dataReceivedCount += 1

def __displayImageReceived( plug ) :
	
	GafferUI.EventLoop.executeOnUIThread( lambda : plug.node().plugDirtiedSignal()( plug ) )

__displayDataReceivedConnection = GafferImage.Display.dataReceivedSignal().connect( __displayDataReceived )
__displayImageReceivedConnection = GafferImage.Display.imageReceivedSignal().connect( __displayImageReceived )