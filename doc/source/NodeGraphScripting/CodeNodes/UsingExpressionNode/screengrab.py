# BuildTarget: images/graphEditorNodeError.png

import IECore
import time
import imath

import Gaffer
import GafferScene
import GafferUI

# Delay the script for x seconds
def __delay( delay ) :
	endTime = time.time() + delay
	while time.time() < endTime :
		GafferUI.EventLoop.waitForIdle( 1 )

mainWindow = GafferUI.ScriptWindow.acquire( script )
graphEditor = mainWindow.getLayout().editors( GafferUI.GraphEditor )[0]

# Sphere and Expression node with error in Graph Editor
sphereNode = GafferScene.Sphere()
script.addChild( sphereNode )
expNode = Gaffer.Expression()
script.addChild( expNode )
expNode.setExpression( 'parent["Sphere"]["radius"] = context.get("myVar")', "python")
__delay( 0.1 )
uiPos = sphereNode["__uiPosition"].getValue()
sphereNode["__uiPosition"].setValue( uiPos + imath.V2f( 8, 0 ) )
contextNode = GafferScene.SceneContextVariables()
contextNode["in"].setInput( sphereNode["out"] )
script.addChild( contextNode )
script.selection().add( sphereNode )
__delay( 0.1 )
script.selection().clear()
graphEditor.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorNodeError.png" )
