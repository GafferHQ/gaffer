# BuildTarget: images/interfaceCameraParameters.png
# BuildTarget: images/interfaceCameraSets.png

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
__path = "/camera"
__paths = IECore.PathMatcher( [ __path ] )
GafferSceneUI.ContextAlgo.expand( script.context(), __paths )

from GafferSceneUI.SceneInspector import __TransformSection, __BoundSection, __ObjectSection, __AttributesSection, __SetMembershipSection

for imageName, sectionClass in [
	( "Parameters.png", __ObjectSection ),
    ( "Sets.png", __SetMembershipSection )
] :

	section = sectionClass()
	section._Section__collapsible.setCollapsed( False )

	with GafferUI.Window( "Property" ) as window :

		sceneInspector = GafferSceneUI.SceneInspector( script, sections = [ section ] )
		sceneInspector.setNodeSet( Gaffer.StandardSet( [ script["Camera"] ] ) )
		sceneInspector.setTargetPaths( [ __path ] )

	window.resizeToFitChild()
	window.setVisible( True )

	GafferUI.WidgetAlgo.grab( widget = sceneInspector, imagePath = "images/interfaceCamera" + imageName )
