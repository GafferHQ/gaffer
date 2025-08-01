# BuildTarget: images/interfaceCameraParameters.png

import IECore
import time
import imath

import Gaffer
import GafferUI

import GafferScene
import GafferSceneUI

# Interface: the object and set sections of a camera in the Scene Inspector
script["Camera"] = GafferScene.Camera()
script["Camera"]["perspectiveMode"].setValue( 1 )
script["Camera"]["focalLength"].setValue( 50.0 )
script["Camera"]["renderSettingOverrides"]["resolution"]["enabled"].setValue( True )
script["Camera"]["renderSettingOverrides"]["overscan"]["value"].setValue( True )
script["Camera"]["renderSettingOverrides"]["overscan"]["enabled"].setValue( True )
script["Camera"]["renderSettingOverrides"]["overscanLeft"]["value"].setValue( 0.05 )
script["Camera"]["renderSettingOverrides"]["overscanLeft"]["enabled"].setValue( True )
script["Camera"]["renderSettingOverrides"]["overscanRight"]["value"].setValue( 0.05 )
script["Camera"]["renderSettingOverrides"]["overscanRight"]["enabled"].setValue( True )
script["Camera"]["renderSettingOverrides"]["overscanTop"]["value"].setValue( 0.05 )
script["Camera"]["renderSettingOverrides"]["overscanTop"]["enabled"].setValue( True )
script["Camera"]["renderSettingOverrides"]["overscanBottom"]["value"].setValue( 0.05 )
script["Camera"]["renderSettingOverrides"]["overscanBottom"]["enabled"].setValue( True )

script.selection().add( script["Camera"] )
GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( script, IECore.PathMatcher( [ "/camera" ] ) )

with GafferUI.Window( "Property" ) as window :

	sceneInspector = GafferSceneUI.SceneInspector( script)
	sceneInspector.setNodeSet( Gaffer.StandardSet( [ script["Camera"] ] ) )
	sceneInspector._SceneInspector__locationPathListing.setExpansion( IECore.PathMatcher( [ "/Location/Object", "/Location/Object/Parameters" ] ) )

window._qtWidget().resize( 400, 500 )
window.setVisible( True )
window.setPosition( imath.V2i( 0, 0 ) )

GafferUI.WidgetAlgo.grab( widget = sceneInspector, imagePath = "images/interfaceCameraParameters.png" )
