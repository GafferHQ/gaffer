# BuildTarget: images/blank.png
# BuildTarget: images/parameters.png
# BuildTarget: images/shaderBallColoredStripes.png
# BuildTarget: images/shaderBallStripes.png

import time

import imath

import Gaffer
import GafferOSL

import GafferUI

scriptWindow = GafferUI.ScriptWindow.acquire( script )

script["OSLCode"] = GafferOSL.OSLCode()
script.setFocus( script["OSLCode"] )
oslEditor = GafferUI.NodeEditor.acquire( script["OSLCode"], floating=True )
GafferUI.WidgetAlgo.grab( widget = oslEditor, imagePath = "images/blank.png" )

script["OSLCode"]["parameters"]["width"] = Gaffer.FloatPlug( defaultValue = 0.0 )
script["OSLCode"]["parameters"]["width"].setValue( 0.025 )
script["OSLCode"]["out"]["stripes"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out, defaultValue = imath.Color3f( 0, 0, 0 ) )
GafferUI.WidgetAlgo.grab( widget = oslEditor, imagePath = "images/parameters.png" )
oslEditor.parent().setVisible( False )

script["OSLCode"]["code"].setValue( "stripes = aastep( 0, sin( v * M_PI / width ) )" )
viewer = scriptWindow.getLayout().editors( GafferUI.Viewer )[0]
# delay so it can render
t = time.time() + 3
while time.time() < t :
	GafferUI.EventLoop.waitForIdle( 1 )
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/shaderBallStripes.png" )

script["OSLCode"]["parameters"]["color1"] = Gaffer.Color3fPlug( defaultValue = imath.Color3f( 0, 0, 0 ) )
script["OSLCode"]["parameters"]["color1"].setValue( imath.Color3f( 0.814999998, 0.0401652865, 0 ) )
script["OSLCode"]["parameters"]["color2"] = Gaffer.Color3fPlug( defaultValue = imath.Color3f( 0, 0, 0 ) )
script["OSLCode"]["parameters"]["color2"].setValue( imath.Color3f( 0.210374981, 0.581973732, 0.764999986 ) )
script["OSLCode"]["code"].setValue( "float vv = v + 0.05 * pnoise( u * 20, 4 );\nfloat m = aastep( 0, sin( vv * M_PI / width ) );\nstripes = mix( color1, color2, m );" )
# delay so it can render
t = time.time() + 3
while time.time() < t :
	GafferUI.EventLoop.waitForIdle( 1 )
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/shaderBallColoredStripes.png" )
