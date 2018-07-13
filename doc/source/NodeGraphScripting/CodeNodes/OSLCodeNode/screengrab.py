# BuildTarget: images/mainOSLCodeNode.png

import IECore
import imath
import time

import Gaffer
import GafferOSL

import GafferUI

# Delay the script for x seconds
def __delay( delay ) :
	endTime = time.time() + delay
	while time.time() < endTime :
		GafferUI.EventLoop.waitForIdle( 1 )

mainWindow = GafferUI.ScriptWindow.acquire( script )

# OSLCode node in main window
OSLNode = GafferOSL.OSLCode()
script.addChild( OSLNode )
script.selection().add( OSLNode )
__delay( 1 )
GafferUI.WidgetAlgo.grab( widget = mainWindow, imagePath = "images/mainOSLCodeNode.png" )
