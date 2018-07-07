# BuildTarget: images/viewerShader.png

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
viewer = mainWindow.getLayout().editors( GafferUI.Viewer )[0]

# OSLCode node in Viewer
OSLNode = GafferOSL.OSLCode()
script["OSLCode"] = OSLNode
script.selection().add( OSLNode )
__delay( 1 )
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerShader.png" )

# OSLCode node in Node Editor
nodeEditorWindow = GafferUI.NodeEditor.acquire( OSLNode, floating=True )
nodeEditorWindow._qtWidget().setFocus()
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/nodeEditorShader.png" )

# OSLCode node with new parameters in Node Editor window
OSLNode["parameters"]["width"] = Gaffer.FloatPlug( defaultValue = 0.0 )
OSLNode["parameters"]["width"].setValue( 0.025 )
OSLNode["out"]["stripes"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out, defaultValue = imath.Color3f( 0, 0, 0 ) )
OSLNode["code"].setValue( "stripes = aastep( 0, sin( v * M_PI / width ) )" )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/nodeEditorShaderParameters.png" )
nodeEditorWindow.parent().setVisible( False )

# OSLCode node with new parameters in Viewer
__delay( 3 )
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerShaderStripes.png" )

# Plug parameters of OSLCode node in Node Editor window
OSLNode["parameters"]["color1"] = Gaffer.Color3fPlug( defaultValue = imath.Color3f( 0, 0, 0 ) )
OSLNode["parameters"]["color2"] = Gaffer.Color3fPlug( defaultValue = imath.Color3f( 0, 0, 0 ) )
nodeEditorWindow.parent().setVisible( True )
plugParameters = nodeEditorWindow.nodeUI().plugValueWidget( OSLNode["parameters"] )
GafferUI.WidgetAlgo.grab( widget = plugParameters, imagePath = "images/nodeEditorColorInputs.png" )
nodeEditorWindow.parent().setVisible( False )

# OSLCode node with colours and wobble in Viewer
OSLNode["parameters"]["color1"].setValue( imath.Color3f( 0.814999998, 0.0401652865, 0 ) )
OSLNode["parameters"]["color2"].setValue( imath.Color3f( 0.210374981, 0.581973732, 0.764999986 ) )
OSLNode["code"].setValue( "float vv = v + 0.05 * pnoise( u * 20, 4 );\nfloat m = aastep( 0, sin( vv * M_PI / width ) );\nstripes = mix( color1, color2, m );" )
__delay( 3 )
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerShaderStripesColors.png" )
