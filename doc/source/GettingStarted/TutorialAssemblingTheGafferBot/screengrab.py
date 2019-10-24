# BuildTarget: images/mainDefaultLayout.png

import datetime
import os
import sys
import time

def debug( message ) :
	sys.stderr.write( "%s : %s\n" % ( datetime.datetime.now(), message ) )

debug( "import imath" )
import imath

debug( "import IECore" )
import IECore

debug( "import Gaffer" )
import Gaffer
debug( "import GafferScene" )
import GafferScene

debug( "import GafferUI" )
import GafferUI
debug( "import GafferSceneUI" )
import GafferSceneUI

origGrab = GafferUI.WidgetAlgo.grab
def debugGrab( *args, **kwargs ) :
	p = kwargs.get( "imagePath", "unknown" )
	w = kwargs.get( "widget", None )
	debug( "Grabbing %s@%s to %s" % ( type(w), id(w), p ) )
	r = origGrab( *args, **kwargs )
	debug( "     ....done" )
	return r
GafferUI.WidgetAlgo.grab = debugGrab

debug( "Start" )
scriptWindow = GafferUI.ScriptWindow.acquire( script )
viewer = scriptWindow.getLayout().editors( GafferUI.Viewer )[0]
graphEditor = scriptWindow.getLayout().editors( GafferUI.GraphEditor )[0]
hierarchyView = scriptWindow.getLayout().editors( GafferSceneUI.HierarchyView )[0]

debug( "Layout created" )

# Delay for x seconds
def __delay( delay ) :
	endtime = time.time() + delay
	while time.time() < endtime :
		GafferUI.EventLoop.waitForIdle( 1 )

# Default layout in main window
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/mainDefaultLayout.png" )

# Empty SceneReader node in main window
debug( "Adding SceneReader" )
script["SceneReader"] = GafferScene.SceneReader()
readerNode = script["SceneReader"]
script.selection().add( readerNode )
__delay( 0.1 )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/mainSceneReaderNode.png" )


debug( "Configuring cache" )
script["SceneReader"]["fileName"].setValue( "${GAFFER_ROOT}/resources/gafferBot/caches/gafferBot.scc" )
viewer.view().viewportGadget().frame( script["SceneReader"]["out"].bound( "/" ) )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/sceneReaderBound.png" )

debug( "Framing view" )
# GafferBot bounding box in Viewer
readerNode["fileName"].setValue( "${GAFFER_ROOT}/resources/gafferBot/caches/gafferBot.scc" )
viewer.view().viewportGadget().frame( readerNode["out"].bound( "/" ) )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/viewerSceneReaderBounding.png" )

debug( "Exapanding hierarchy" )
# GafferBot torso in Hierarchy View
GafferSceneUI.ContextAlgo.setExpandedPaths( script.context(), IECore.PathMatcher( [ "/GAFFERBOT", "/GAFFERBOT/C_torso_GRP" ] ) )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = hierarchyView, imagePath = "images/hierarchyViewExpandedTwoLevels.png" )

debug( "Expanding head/right leg" )
# GafferBot head and left leg in main window
paths = IECore.PathMatcher( [ "/GAFFERBOT/C_torso_GRP/C_head_GRP", "/GAFFERBOT/C_torso_GRP/R_legUpper_GRP" ] )
GafferSceneUI.ContextAlgo.expand( script.context(), paths )
GafferSceneUI.ContextAlgo.expandDescendants( script.context(), paths, script["SceneReader"]["out"] )
GafferSceneUI.ContextAlgo.expandDescendants( script.context(), paths, readerNode["out"] )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/mainHeadAndLeftLegExpanded.png" )

debug( "Expanding other leg" )
# GafferBot head and both legs in Viewer
paths = IECore.PathMatcher( [ "/GAFFERBOT/C_torso_GRP/L_legUpper_GRP" ] )
GafferSceneUI.ContextAlgo.expand( script.context(), paths )
GafferSceneUI.ContextAlgo.expandDescendants( script.context(), paths, readerNode["out"] )
GafferSceneUI.ContextAlgo.setSelectedPaths( script.context(), paths )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerHeadAndLegsExpanded.png" )

debug( "Creating camera" )
# Camera and SceneReader node in main window
script["Camera"] = GafferScene.Camera()
cameraNode = script["Camera"]
script.selection().clear()
script.selection().add( script["Camera"] )
script.selection().add( cameraNode )
# Approximate the default viewport position
viewer.view().viewportGadget().frame( imath.Box3f( imath.V3f( 0, -1.75, 0 ), imath.V3f( 5, 5, 5 ) ) )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/mainCameraNode.png" )

debug( "Grouping" )
# Grouped nodes in Gaffer
script["Group"] = GafferScene.Group()
groupNode = script["Group"]
groupNode["in"][0].setInput( readerNode["out"] )
groupNode["in"][1].setInput( cameraNode["out"] )
script.selection().clear()
script.selection().add( groupNode )
viewer.view()["minimumExpansionDepth"].setValue( 999 )
GafferSceneUI.ContextAlgo.clearExpansion( script.context() )
GafferSceneUI.ContextAlgo.expand( script.context(), IECore.PathMatcher( [ "/group" ] ) )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/mainGroupNode.png" )

debug( "Moving camera + setting translate tool" )
# Camera repositioned, with translate tool on, in Viewer
cameraNode["transform"]["translate"].setValue( imath.V3f( 16, 13, 31 ) )
viewer.view().viewportGadget().frame( groupNode["out"].bound( "/group" ) )
GafferSceneUI.ContextAlgo.setSelectedPaths( script.context(), IECore.PathMatcher( [ "/group/camera" ] ) )
for i in viewer._Viewer__toolChooser.tools():
	if type( i ) == GafferSceneUI.TranslateTool:
		translateTool = i
translateTool["active"].setValue( True )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerCameraRepositioned.png" )

debug( "Rotating camera + Setting rotate tool" )
# Camera rotated, with rotate tool on, in Viewer
translateTool["active"].setValue( False )
cameraNode["transform"]["rotate"].setValue( imath.V3f( 0, 30, 0 ) )
for i in viewer._Viewer__toolChooser.tools():
	if type( i ) == GafferSceneUI.RotateTool:
		rotateTool = i
rotateTool["active"].setValue( True )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerCameraRotated.png" )

debug( "Camera Node Editor" )
# Camera node in Node Editor window
nodeEditorWindow = GafferUI.NodeEditor.acquire( cameraNode, floating=True )
nodeEditorWindow._qtWidget().setFocus()
GafferUI.PlugValueWidget.acquire( cameraNode["transform"] )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/nodeEditorWindowCameraTransform.png" )

debug( "Deleting un-needed objects" )
del nodeEditorWindow
del readerNode
del groupNode
del cameraNode


debug( "Loading scripts/renderSettings.gfr" )
# Render settings graph in Graph Editor
script["fileName"].setValue( os.path.abspath( "scripts/renderSettings.gfr" ) )
script.load()
script.selection().clear()
script.selection().add( script["Catalogue"] )
graphEditor.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorRenderSettings.png" )

# GafferBot render without lighting in main window
def __renderAndGrab( script, widget, imagePath, delay = 15 ) :

	debug( "Rendering and grabbing %s %s to %s" % ( type(widget), id(widget), imagePath ) )

	script["variables"]["imageCataloguePort"]["value"].setValue( script["Catalogue"].displayDriverServer().portNumber() )
	debug( "   ...starting render" )
	script["InteractiveAppleseedRender"]["state"].setValue( script["InteractiveAppleseedRender"].State.Running )
	debug( "   ...waiting for %s" % delay )
	__delay( delay )

	viewport = scriptWindow.getLayout().editors( GafferUI.Viewer )[0].view().viewportGadget()
	debug( "   ...framing viewport" )
	viewport.frame( viewport.getPrimaryChild().bound() )
	debug( "   ...waiting for idle" )
	GafferUI.EventLoop.waitForIdle()

	GafferUI.WidgetAlgo.grab( widget = widget, imagePath = imagePath )
	debug( "   ...stopping render" )
	script["InteractiveAppleseedRender"]["state"].setValue( script["InteractiveAppleseedRender"].State.Stopped )
	debug( "   done" )

__renderAndGrab( script, scriptWindow, "images/mainRenderGrey.png", delay = 1 )

debug( "loading scripts/renderSettingsWithGap.gfr" )
# Render settings with gap in main window
script["fileName"].setValue( os.path.abspath( "scripts/renderSettingsWithGap.gfr" ) )
script.load()
script.selection().add( [ script["StandardOptions"], script["AppleseedOptions"], script["Outputs"], script["InteractiveAppleseedRender"], script["Catalogue"] ] )
graphEditor.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/mainRenderSettingsWithGap.png" )

debug( "loading scripts/firstShaderAssignment.gfr" )
# First shader assignment in Graph Editor
script["fileName"].setValue( os.path.abspath( "scripts/firstShaderAssignment.gfr" ) )
script.load()
script.selection().add( script["ShaderAssignment"] )
graphEditor.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorFirstShaderNodes.png" )

debug( "loading scripts/firstLight.gfr" )
# Environment light in Graph Editor
script["fileName"].setValue( os.path.abspath( "scripts/firstLight.gfr" ) )
script.load()
script.selection().add( script["hosek_environment_edf"] )
graphEditor.frame( Gaffer.StandardSet( [ script["Group"], script["hosek_environment_edf"] ] ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorEnvironmentLightNode.png" )

debug( "selecting catalogue" )
# GafferBot render with lighting in Viewer
script.selection().clear()
script.selection().add( script["Catalogue"] )
__renderAndGrab( script, viewer, "images/viewerRenderOneShader.png" )

debug( "loading scripts/textures.gfr" )
# GafferBot render with lighting and textures in Viewer
script["fileName"].setValue( os.path.abspath( "scripts/textures.gfr" ) )
script.load()
script.selection().add( script["Catalogue"] )
__renderAndGrab( script, viewer, "images/viewerRenderTextures.png" )

debug( "loading scripts/secondShaderAssignment.gfr")
# Second shader assignment in Graph Editor
script["fileName"].setValue( os.path.abspath( "scripts/secondShaderAssignment.gfr" ) )
script.load()
script.selection().add( script["ShaderAssignment1"] )
graphEditor.frame( Gaffer.StandardSet( [ script["as_disney_material"], script["as_disney_material1"], script["ShaderAssignment"], script["ShaderAssignment1"] ] ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorSecondShaderNodes.png" )

debug( "reframing graph" )
# GafferBot render with second shader assignment in main window
script.selection().clear()
script.selection().add( script["Catalogue"] )
graphEditor.frame( script.children( Gaffer.Node ) )
__renderAndGrab( script, scriptWindow, "images/mainRenderTwoShaders.png" )


debug( "reframing shader assignemnt path filter" )
# PathFilter node in Graph Editor
script["fileName"].setValue( os.path.abspath( "scripts/secondShaderAssignmentFiltered.gfr" ) )
script.load()
script.selection().add( script["PathFilter"] )
graphEditor.frame( Gaffer.StandardSet( [ script["PathFilter"], script["ShaderAssignment1"] ] ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorPathFilterNode.png" )

debug( "Adjusting script selection and reframing view" )
# GafferBot node and mouth selection in Viewer
script.selection().clear()
script.selection().add( script["ShaderAssignment1"] )
paths = IECore.PathMatcher( [ "/group/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT/C_browNose001_REN", "/group/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT/C_mouthGrill001_REN" ] )
GafferSceneUI.ContextAlgo.setSelectedPaths( script.context(), paths )
debug( "   ..waiting for idle" )
GafferUI.EventLoop.waitForIdle()
paths = IECore.PathMatcher( [ "/group/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT" ] )
viewer.view().frame( paths, direction = imath.V3f( -0.2, -0.2, -1 ) )
__delay( 0.1 )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerSelectionFace.png" )

debug( "final render" )
# GafferBot final render in Viewer
script.selection().clear()
script.selection().add( script["Catalogue"] )
__renderAndGrab( script, viewer, "images/viewerRenderFinal.png" )
