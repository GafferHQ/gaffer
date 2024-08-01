# BuildTarget: images/exampleAnamorphicCameraSetup.png
# BuildTarget: images/exampleSphericalCameraSetupArnoldTweaks.png
# BuildTarget: images/interfaceCameraVisualizer.png
# BuildTarget: images/renderDepthOfFieldBlur.png
# BuildTarget: images/taskCameraApertureFocalLengthPlugs.png
# BuildTarget: images/taskCameraCustomAperturePlugs.png
# BuildTarget: images/taskCameraDepthOfFieldPlugs.png
# BuildTarget: images/taskCameraFOVPlugs.png
# BuildTarget: images/taskCameraRenderOverridePlugs.png
# BuildTarget: images/taskCameraTweaksTweaks.png
# BuildTarget: images/taskStandardOptionsDepthOfFieldPlug.png
# BuildDependency: scripts/renderDepthOfFieldBlur.gfr
# BuildDependency: scripts/taskCameraApertureFocalLengthPlugs_edit.gfr
# BuildDependency: scripts/taskCameraCustomAperturePlugs_edit.gfr
# BuildDependency: scripts/taskCameraFOVPlugs_edit.gfr
# BuildDependency: scripts/taskStandardOptionsDepthOfFieldPlug_edit.gfr

import os
import pathlib
import subprocess
import tempfile
import time

import imath
import IECore
import Gaffer
import GafferScene
import GafferUI
import GafferSceneUI

scriptWindow = GafferUI.ScriptWindow.acquire( script )
viewer = scriptWindow.getLayout().editors( GafferUI.Viewer )[0]
graphEditor = scriptWindow.getLayout().editors( GafferUI.GraphEditor )[0]
hierarchyView = scriptWindow.getLayout().editors( GafferSceneUI.HierarchyView )[0]

# Delay for x seconds
def __delay( delay ) :
	endtime = time.time() + delay
	while time.time() < endtime :
		GafferUI.EventLoop.waitForIdle( 1 )

# Create a random directory in `/tmp` for the dispatcher's `jobsDirectory`, so we don't clutter the user's `~gaffer` directory
__temporaryDirectory = pathlib.Path( tempfile.mkdtemp( prefix = "gafferDocs" ) )

def __getTempFilePath( fileName, directory = __temporaryDirectory ) :

	return ( directory / fileName ).as_posix()

def __outputImagePath( fileName ) :

	return pathlib.Path( "images/{}.png".format( fileName ) ).absolute().as_posix()

def __dispatchScript( script, tasks, settings ) :
	command = "gaffer dispatch -script {} -tasks {} -dispatcher Local -settings {} -dispatcher.jobsDirectory '\"{}/dispatcher/local\"'".format(
		script,
		" ".join( tasks ),
		" ".join( settings ),
		__temporaryDirectory.as_posix()
	)
	subprocess.check_call( command, shell=True )

# Interface: a Camera node in the Graph Editor
script["Camera"] = GafferScene.Camera()
graphEditor.frame( Gaffer.StandardSet( [ script["Camera"] ] ) )
## TODO: Automate `images/interfaceCameraNode.png` when these tools become available:
# - API method for zooming the Graph Editor

# Interface: the camera visualizer in the Viewer
script.selection().add( script["Camera"] )
script.setFocus( script["Camera"] )
__delay( 0.1 )
viewer.view()["grid"]["visible"].setValue( False )
paths = IECore.PathMatcher( [ "/camera" ] )
GafferSceneUI.ContextAlgo.expand( script.context(), paths )
GafferSceneUI.ContextAlgo.setSelectedPaths( script.context(), paths )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/interfaceCameraVisualizer.png" )
script.selection().clear()

# Illustration: the camera overlay in the Viewer
# script["Cube"] = GafferScene.Cube()
# script["Parent"] = GafferScene.Parent()
# script["Camera"]["transform"]["translate"].setValue( imath.V3f( 0, 0, 10 ) )
script["Camera"]["perspectiveMode"].setValue( 1 )
script["Camera"]["renderSettingOverrides"]["resolution"]["value"].setValue( imath.V2i( 1920, 1080 ) )
script["Camera"]["renderSettingOverrides"]["resolution"]["enabled"].setValue( True )
#script["Camera"]["renderSettingOverrides"]["cropWindow"]["value"].setValue( imath.Box2f( imath.V2f( 0.2, 0.2 ), imath.V2f( 0.8, 0.8 ) ) )
#script["Camera"]["renderSettingOverrides"]["cropWindow"]["enabled"].setValue( True )
# script["Parent"]["in"].setInput( script["Camera"]["out"] )
# script["Parent"]["parent"].setValue( '/' )
# script["Parent"]["child"].setInput( script["Cube"]["out"] )
# script["Cube"]["transform"]["rotate"].setValue( imath.V3f( 35.0, -40.0, -25.0 ) )
# viewer.view()["camera"]["lookThroughCamera"].setValue( "/camera" )
# viewer.view()["camera"]["lookThroughEnabled"].setValue( True )
# GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/illustrationFrameOverlay.png" )
# script.removeChild( script["Parent"] )
# script.removeChild( script["Cube"] )
## TODO: Automate `images/illustrationFrameOverlay.png` (the above) when these tools become available:
# - API method for resizing embedded editors
# - 2D curves with gradient colors

# Task: animation of selecting, translating, and rotating a camera in the Viewer
## TODO: Automate `images/taskSelectTranslateRotateCamera.gif` when these tools become available:
# - KB/M recording and simulated playback

# Task: animation of selecting look-through cameras (including the render camera) in the Viewer
# script["fileName"].setValue( os.path.abspath( "scripts/taskSelectingLookThroughCamera.gfr" ) )
## TODO: Automate `images/taskSelectingLookThroughCamera.gif` when these tools become available:
# - KB/M recording and simulated playback

# Task: animation of manipulating the camera with the Camera Tool and camera controls in the Viewer
# script["fileName"].setValue( os.path.abspath( "scripts/taskCameraToolLookThroughCamera.gfr" ) )
## TODO: Automate `images/taskCameraToolLookThroughCamera.gif` when these tools become available:
# - KB/M recording and simulated playback

# Task: animation of orbiting the look-through camera around an object in the Viewer
## TODO: Automate `images/taskOrbitLookThroughCamera.gif` when these tools become available:
# - KB/M recording and simulated playback

# Task: the Field of View projection mode in the Node Editor
__imageName = "taskCameraFOVPlugs"
__tempImagePath = __getTempFilePath( "{}.png".format( __imageName ) )
script["Camera"]["perspectiveMode"].setValue( 0 )
script["Camera"]["fieldOfView"].setValue( 40.0 )
script["Camera"]["apertureAspectRatio"].setValue( 1.778 )
__nodeEditorWindow = GafferUI.NodeEditor.acquire( script["Camera"], floating=True )
__nodeEditorWindow._qtWidget().setFocus()
GafferUI.WidgetAlgo.grab( widget = __nodeEditorWindow, imagePath = __tempImagePath )
__dispatchScript(
	script = "scripts/{}_edit.gfr".format( __imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader.fileName '\"{}\"'".format( __tempImagePath ),
		"-ImageWriter.fileName '\"{}\"'".format( __outputImagePath( __imageName ) )
	]
)

# Task: the Aperture and Focal Length projection mode in the Node Editor
__imageName = "taskCameraApertureFocalLengthPlugs"
__tempImagePath = __getTempFilePath( "{}.png".format( __imageName ) )
script["Camera"]["perspectiveMode"].setValue( 1 )
script["Camera"]["aperture"].setValue( imath.V2f( 36.0, 24.0 ) )
script["Camera"]["focalLength"].setValue( 50.0 )
GafferUI.WidgetAlgo.grab( widget = __nodeEditorWindow, imagePath = __tempImagePath )
__dispatchScript(
	script = "scripts/{}_edit.gfr".format( __imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader.fileName '\"{}\"'".format( __tempImagePath ),
		"-ImageWriter.fileName '\"{}\"'".format( __outputImagePath( __imageName ) )
	]
)

# Task: the Custom aperture mode and aperture.x and aperture.y plugs in the Node Editor
__imageName = "taskCameraCustomAperturePlugs"
__tempImagePath = __getTempFilePath( "{}.png".format( __imageName ) )
script["Camera"]["aperture"].setValue( imath.V2f( 40.96, 21.6 ) )
Gaffer.Metadata.registerValue( script["Camera"]["aperture"], 'presetsPlugValueWidget:isCustom', True )
GafferUI.WidgetAlgo.grab( widget = __nodeEditorWindow, imagePath = __tempImagePath )
__dispatchScript(
	script = "scripts/{}_edit.gfr".format( __imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader.fileName '\"{}\"'".format( __tempImagePath),
		"-ImageWriter.fileName '\"{}\"'".format( __outputImagePath( __imageName ) )
	]
)

# Task: animation of adjusting the Aperture Offset in the Node Editor, and the corresponding changes to the camera's frustrum in the Viewer
## TODO: Automate `images/taskApertureOffset.gif` when these tools become available:
# - KB/M recording and simulated playback

# Render: depth of field blur
#
__imageName = "renderDepthOfFieldBlur"
__dispatchScript(
	script = "scripts/{}.gfr".format( __imageName ),
	tasks = [ "Render" ],
	settings = [
		"-Outputs.outputs.output1.fileName '\"{}\"'".format( __outputImagePath( __imageName ) )
	]
)

# Task: the Depth of Field tab, with settings, in the Node Editor
script["Camera"]["focusDistance"].setValue( 22.0 )
script["Camera"]["fStop"].setValue( 2.8 )
GafferUI.PlugValueWidget.acquire( script["Camera"]["fStop"] )
__nodeEditorWindow._qtWidget().setFocus()
GafferUI.WidgetAlgo.grab( widget = __nodeEditorWindow, imagePath = "images/taskCameraDepthOfFieldPlugs.png" )

# Task: a StandardOptions node with the Depth of Field plug activated in the Node Editor
__imageName = "taskStandardOptionsDepthOfFieldPlug"
__tempImagePath = __getTempFilePath( "{}.png".format( __imageName ) )
script["StandardOptions"] = GafferScene.StandardOptions()
script["StandardOptions"]["options"]["renderCamera"]["value"].setValue( "/camera" )
script["StandardOptions"]["options"]["renderCamera"]["enabled"].setValue( True )
script["StandardOptions"]["options"]["depthOfField"]["value"].setValue( True )
script["StandardOptions"]["options"]["depthOfField"]["enabled"].setValue( True )
__nodeEditorWindow = GafferUI.NodeEditor.acquire( script["StandardOptions"], floating=True )
__nodeEditorWindow._qtWidget().setFocus()
__nodeEditorWindow.parent()._qtWidget().resize( 384, 484 )
GafferUI.PlugValueWidget.acquire( script["StandardOptions"]["options"]["depthOfField"] )
GafferUI.WidgetAlgo.grab( widget = __nodeEditorWindow, imagePath = __tempImagePath )
__dispatchScript(
	script = "scripts/{}_edit.gfr".format( __imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader.fileName '\"{}\"'".format( __tempImagePath ),
		"-ImageWriter.fileName '\"{}\"'".format( __outputImagePath( __imageName ) )
	]
)

# Task: a Camera node's Render Overrides tab in the Node Editor
script["Camera"]["renderSettingOverrides"]["resolution"]["value"].setValue( imath.V2i( 5120, 2160 ) )
script["Camera"]["renderSettingOverrides"]["resolution"]["enabled"].setValue( True )
__nodeEditorWindow.parent().close()
__delay( 0.5 )
__nodeEditorWindow = GafferUI.NodeEditor.acquire( script["Camera"], floating=True )
GafferUI.PlugValueWidget.acquire( script["Camera"]["renderSettingOverrides"] )
__nodeEditorWindow._qtWidget().setFocus()
__nodeEditorWindow.parent()._qtWidget().resize( 486, 425 )
GafferUI.WidgetAlgo.grab( widget = __nodeEditorWindow, imagePath = "images/taskCameraRenderOverridePlugs.png" )

# Task: a CameraTweaks node with 2 tweaks in the Node Editor
script["CameraTweaks"] = GafferScene.CameraTweaks()
script["CameraTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( "tweak_focalLength", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["CameraTweaks"]["tweaks"]["tweak_focalLength"].addChild( Gaffer.FloatPlug( "value", defaultValue = 35.0, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["CameraTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( "tweak_resolution", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["CameraTweaks"]["tweaks"]["tweak_resolution"].addChild( Gaffer.V2iPlug( "value", defaultValue = imath.V2i( 1024, 1024 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["CameraTweaks"]["tweaks"]["tweak_focalLength"]["name"].setValue( 'focalLength' )
script["CameraTweaks"]["tweaks"]["tweak_focalLength"]["value"].setValue( 85.0 )
script["CameraTweaks"]["tweaks"]["tweak_resolution"]["name"].setValue( 'resolution' )
script["CameraTweaks"]["tweaks"]["tweak_resolution"]["value"].setValue( imath.V2i( 5120, 2160 ) )
__nodeEditorWindow.parent().close()
__delay( 0.5 )
__nodeEditorWindow = GafferUI.NodeEditor.acquire( script["CameraTweaks"], floating=True )
__nodeEditorWindow._qtWidget().setFocus()
GafferUI.WidgetAlgo.grab( widget = __nodeEditorWindow, imagePath = "images/taskCameraTweaksTweaks.png" )
__nodeEditorWindow.parent().close()

# Example: Anamorphic Camera Setup
__dispatchScript(
	script = pathlib.Path( "../../../examples/rendering/anamorphicCameraSetup.gfr" ).absolute().as_posix(),
	tasks = [ "Render" ],
	settings = [
		"-StandardOptions.options.renderResolution.value.x 240",
		"-StandardOptions.options.renderResolution.value.y 270",
		"-Outputs.outputs.output1.fileName '\"{}\"'".format( __outputImagePath( "exampleAnamorphicCameraSetup" ) ),
		"-Outputs.outputs.output1.type '\"png\"'"
	]
)

# Example: Spherical Camera Setup in Arnold
# __dispatchScript(
#	script = "../../../examples/rendering/sphericalCameraSetupArnold.gfr",
#	tasks = [ "Render" ],
#	settings = [
#		"-StandardOptions.options.renderResolution.value.x '480'",
#		"-StandardOptions.options.renderResolution.value.y '270'",
#		"-Outputs.outputs.output1.fileName '\"{}\"'".format( os.path.abspath( "images/exampleSphericalCameraSetupArnold.png" ) ),
#		"-Outputs.outputs.output1.type '\"png\"'"
#		]
#	)
## TODO: Automate `images/exampleSphericalCameraSetupArnold.png` (the above) when these tools become available:
# - Support for spherical cameras in Appleseed

# Task: the tweaks for a spherical Arnold camera in the Node Editor
# Since we can't assume the build environment has Arnold, we need to recreate the tweaks
script.removeChild( script["CameraTweaks"] )
script["CameraTweaks"] = GafferScene.CameraTweaks()
script["CameraTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( "tweak_projection", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["CameraTweaks"]["tweaks"]["tweak_projection"].addChild( Gaffer.StringPlug( "value", defaultValue = 'perspective', flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["CameraTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( "tweak_aperture", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["CameraTweaks"]["tweaks"]["tweak_aperture"].addChild( Gaffer.V2fPlug( "value", defaultValue = imath.V2f( 36, 24 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["CameraTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( "tweak_filmFit", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["CameraTweaks"]["tweaks"]["tweak_filmFit"].addChild( Gaffer.IntPlug( "value", defaultValue = 0, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["CameraTweaks"]["tweaks"]["tweak_projection"]["name"].setValue( 'projection' )
script["CameraTweaks"]["tweaks"]["tweak_projection"]["value"].setValue( 'spherical_camera' )
script["CameraTweaks"]["tweaks"]["tweak_aperture"]["name"].setValue( 'aperture' )
script["CameraTweaks"]["tweaks"]["tweak_aperture"]["value"].setValue( imath.V2f( 2, 2 ) )
script["CameraTweaks"]["tweaks"]["tweak_filmFit"]["name"].setValue( 'filmFit' )
Gaffer.Metadata.registerValue( script["CameraTweaks"]["tweaks"]["tweak_projection"]["value"], 'presetsPlugValueWidget:isCustom', True )
Gaffer.Metadata.registerValue( script["CameraTweaks"]["tweaks"]["tweak_aperture"]["value"], 'presetsPlugValueWidget:isCustom', True )
__nodeEditorWindow = GafferUI.NodeEditor.acquire( script["CameraTweaks"], floating=True )
__nodeEditorWindow.parent()._qtWidget().resize( 500, 250 )
__nodeEditorWindow._qtWidget().setFocus()
GafferUI.WidgetAlgo.grab( widget = __nodeEditorWindow, imagePath = "images/exampleSphericalCameraSetupArnoldTweaks.png" )

del __nodeEditorWindow
