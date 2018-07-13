# BuildTarget: images/graphEditorExpressionNode.png

import IECore
import imath
import time

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
viewer = mainWindow.getLayout().editors( GafferUI.Viewer )[0]

# Expression node in Graph Editor
expNode = Gaffer.Expression()
script.addChild( expNode )
# TODO: zoom in on node
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorExpressionNode.png" )

# Expression node with code in Node Editor window
sphereNode = GafferScene.Sphere()
script.addChild( sphereNode )
__delay( 0.1 )
expNode.setExpression( 'print "Hello, World!"', "python")
uiPos = sphereNode["__uiPosition"].getValue()
sphereNode["__uiPosition"].setValue( uiPos + imath.V2f( 8, 0 ) )
graphEditor.frame( script.children( Gaffer.Node ) )
nodeEditorWindow = GafferUI.NodeEditor.acquire( expNode, floating=True )
nodeEditorWindow._qtWidget().setFocus()
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/nodeEditorWindowExpressionCode.png" )
nodeEditorWindow.parent().setVisible( False )

# Expression node referencing Sphere node in Graph Editor
expNode.setExpression( 'parent["Sphere"]["radius"]')
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorExpressionNodeReference.png" )

# Expression node modifying Sphere node in Graph Editor
expNode.setExpression( 'parent["Sphere"]["radius"] = 2' )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorExpressionNodeModify.png" )
