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

from __future__ import with_statement

import IECore

import Gaffer
import GafferUI


def appendDefinitions( menuDefinition, prefix="" ) :

	menuDefinition.append( prefix + "/Play", { "command" : play, "shortCut" : "[", "active" : __stopped } )
	menuDefinition.append( prefix + "/Stop", { "command" : stop, "shortCut" : "]", "active" : __playing } )
	menuDefinition.append( prefix + "/PlayStopDivider", { "divider" : True } )
	menuDefinition.append( prefix + "/Increment Frame", { "command" : __incrementFrame, "shortCut" : "Right" } )
	menuDefinition.append( prefix + "/Decrement Frame", { "command" : __decrementFrame, "shortCut" : "Left" } )


## A function suitable as the command for an Playback/Play menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def play( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	
	#TODO call method to start playback


## A function suitable as the command for an Playback/Stop menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def stop( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()

	#TODO call method to stop playback


## Increases frame count by 1
def __incrementFrame( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	script.context().setFrame( script.context().getFrame() + 1)


## Decreases frame count by 1
def __decrementFrame( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	script.context().setFrame( script.context().getFrame() - 1)



## Allows Play menuitem to be disabled if currently playing (i.e. stopped == False)
def __stopped( menu ) :

	scriptNode = menu.ancestor( GafferUI.ScriptWindow ).scriptNode()
	#TODO check playback state and return True if is stopped
	return False

## Allows Stop menuitem to be disabled if currently playing (i.e. playing == False)
def __playing( menu ) :
	
	scriptNode = menu.ancestor( GafferUI.ScriptWindow ).scriptNode()
	#TODO check playback state and return True if is playing
	return False


