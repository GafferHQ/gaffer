# BuildTarget: images/defaultLayout.png

import os
import time

import imath

import IECore

import Gaffer
import GafferScene

import GafferUI
import GafferSceneUI

scriptWindow = GafferUI.ScriptWindow.acquire( script )
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/defaultLayout.png" )

script["SceneReader"] = GafferScene.SceneReader()
script.selection().add( script["SceneReader"] )
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/emptySceneReader.png" )

script["SceneReader"]["fileName"].setValue( "${GAFFER_ROOT}/resources/gafferBot/caches/gafferBot.scc" )
viewer = scriptWindow.getLayout().editors( GafferUI.Viewer )[0]
viewer.view().viewportGadget().frame( script["SceneReader"]["out"].bound( "/" ) )
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/sceneReaderBound.png" )

GafferSceneUI.ContextAlgo.setExpandedPaths( script.context(), IECore.PathMatcher( [ "/GAFFERBOT", "/GAFFERBOT/C_torso_GRP" ] ) )
hierarchy = scriptWindow.getLayout().editors( GafferSceneUI.SceneHierarchy )[0]
GafferUI.WidgetAlgo.grab( widget = hierarchy, imagePath = "images/sceneHierarchyExpandedTwoLevels.png" )

paths = IECore.PathMatcher( [ "/GAFFERBOT/C_torso_GRP/C_head_GRP", "/GAFFERBOT/C_torso_GRP/L_legUpper_GRP" ] )
GafferSceneUI.ContextAlgo.expand( script.context(), paths )
GafferSceneUI.ContextAlgo.expandDescendants( script.context(), paths, script["SceneReader"]["out"] )
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/headAndLegExpanded.png" )

paths = IECore.PathMatcher( [ "/GAFFERBOT/C_torso_GRP/R_legUpper_GRP" ] )
GafferSceneUI.ContextAlgo.expand( script.context(), paths )
GafferSceneUI.ContextAlgo.expandDescendants( script.context(), paths, script["SceneReader"]["out"] )
GafferSceneUI.ContextAlgo.setSelectedPaths( script.context(), paths )
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/headAndLegsExpanded.png" )

paths = IECore.PathMatcher( [ "/" ] )
GafferSceneUI.ContextAlgo.expand( script.context(), paths )
GafferSceneUI.ContextAlgo.expandDescendants( script.context(), paths, script["SceneReader"]["out"] )
GafferSceneUI.ContextAlgo.setSelectedPaths( script.context(), IECore.PathMatcher( [ "" ] ) )
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/fullyExpanded.png" )

script["Camera"] = GafferScene.Camera()
script.selection().clear()
script.selection().add( script["Camera"] )
## \todo: reset viewer bound to grid
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/camera.png" )

script["Group"] = GafferScene.Group()
script["Group"]["in"][0].setInput( script["SceneReader"]["out"] )
script["Group"]["in"][1].setInput( script["Camera"]["out"] )
script.selection().clear()
script.selection().add( script["Group"] )
viewer.view()["minimumExpansionDepth"].setValue( 999 )
GafferSceneUI.ContextAlgo.clearExpansion( script.context() )
paths = IECore.PathMatcher( [ "/group" ] )
GafferSceneUI.ContextAlgo.expand( script.context(), paths )
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/group.png" )

script['Camera']['transform']['translate'].setValue( imath.V3f( 19, 13, 31 ) )
script['Camera']['transform']['rotate'].setValue( imath.V3f( 0, 30, 0 ) )
cameraEditor = GafferUI.NodeEditor.acquire( script["Camera"], floating=True )
GafferUI.PlugValueWidget.acquire( script['Camera']['transform'] )
GafferUI.WidgetAlgo.grab( widget = cameraEditor, imagePath = "images/cameraTransform.png" )
del cameraEditor

script["fileName"].setValue( os.path.abspath( "scripts/renderSettings.gfr" ) )
script.load()
script.selection().add( script["Catalogue"] )
graph = scriptWindow.getLayout().editors( GafferUI.GraphEditor )[0]
graph.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graph, imagePath = "images/renderSettings.png" )

def __renderAndGrab( script, widget, imagePath, delay = 15 ) :

	script["variables"]["imageCataloguePort"]["value"].setValue( script["Catalogue"].displayDriverServer().portNumber() )
	script["InteractiveAppleseedRender"]["state"].setValue( script["InteractiveAppleseedRender"].State.Running )

	# delay so it can render
	t = time.time() + delay
	while time.time() < t :
		GafferUI.EventLoop.waitForIdle( 1 )

	viewport = scriptWindow.getLayout().editors( GafferUI.Viewer )[0].view().viewportGadget()
	viewport.frame( viewport.getPrimaryChild().bound() )
	GafferUI.EventLoop.waitForIdle()

	GafferUI.WidgetAlgo.grab( widget = widget, imagePath = imagePath )
	script["InteractiveAppleseedRender"]["state"].setValue( script["InteractiveAppleseedRender"].State.Stopped )

__renderAndGrab( script, scriptWindow, "images/firstRender.png", delay = 1 )

script["fileName"].setValue( os.path.abspath( "scripts/renderSettingsWithGap.gfr" ) )
script.load()
script.selection().add( [ script["StandardOptions"], script["AppleseedOptions"], script["Outputs"], script["InteractiveAppleseedRender"], script["Catalogue"] ] )
graph.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graph, imagePath = "images/renderSettingsWithGap.png" )

script["fileName"].setValue( os.path.abspath( "scripts/firstShaderAssignment.gfr" ) )
script.load()
script.selection().add( script["ShaderAssignment"] )
graph.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graph, imagePath = "images/firstShaderAssignment.png" )

script["fileName"].setValue( os.path.abspath( "scripts/firstLight.gfr" ) )
script.load()
script.selection().add( script["Parent"] )
graph.frame( Gaffer.StandardSet( [ script["Group"], script["Parent"], script["hosek_environment_edf"] ] ) )
GafferUI.WidgetAlgo.grab( widget = graph, imagePath = "images/parentingGraphEditor.png" )

paths = IECore.PathMatcher( [ "/", "/group" ] )
GafferSceneUI.ContextAlgo.expand( script.context(), paths )
GafferUI.WidgetAlgo.grab( widget = hierarchy, imagePath = "images/parentingSceneHierarchy.png" )

script.selection().clear()
script.selection().add( script["Catalogue"] )
__renderAndGrab( script, viewer, "images/firstLighting.png" )

script["fileName"].setValue( os.path.abspath( "scripts/textures.gfr" ) )
script.load()
script.selection().add( script["Catalogue"] )
__renderAndGrab( script, viewer, "images/textures.png" )

script["fileName"].setValue( os.path.abspath( "scripts/secondShaderAssignment.gfr" ) )
script.load()
script.selection().add( script["ShaderAssignment1"] )
graph.frame( Gaffer.StandardSet( [ script["as_disney_material"], script["as_disney_material1"], script["ShaderAssignment"], script["ShaderAssignment1"] ] ) )
GafferUI.WidgetAlgo.grab( widget = graph, imagePath = "images/secondShaderAssignment.png" )

script.selection().clear()
script.selection().add( script["Catalogue"] )
graph.frame( script.children( Gaffer.Node ) )
__renderAndGrab( script, scriptWindow, "images/secondShaderAssignmentRender.png" )

script["fileName"].setValue( os.path.abspath( "scripts/secondShaderAssignmentFiltered.gfr" ) )
script.load()
script.selection().add( script["PathFilter"] )
graph.frame( Gaffer.StandardSet( [ script["PathFilter"], script["ShaderAssignment1"] ] ) )
GafferUI.WidgetAlgo.grab( widget = graph, imagePath = "images/filterConnection.png" )

script.selection().clear()
script.selection().add( script["ShaderAssignment1"] )
paths = IECore.PathMatcher( [ "/group/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT/C_browNose001_REN", "/group/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT/C_mouthGrill001_REN" ] )
GafferSceneUI.ContextAlgo.setSelectedPaths( script.context(), paths )
GafferUI.EventLoop.waitForIdle()
paths = IECore.PathMatcher( [ "/group/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT" ] )
viewer.view().frame( paths, direction = imath.V3f( -0.2, -0.2, -1 ) )
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/faceSelection.png" )

script.selection().clear()
script.selection().add( script["Catalogue"] )
__renderAndGrab( script, viewer, "images/finalRender.png" )
