# BuildTarget: images/mainDefaultLayout.png

import os
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

# Default layout in main window
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/mainDefaultLayout.png" )

# Empty SceneReader node in main window
script["SceneReader"] = GafferScene.SceneReader()
readerNode = script["SceneReader"]
script.selection().add( readerNode )
Gaffer.MetadataAlgo.setFocusNode( script, readerNode )
__delay( 0.1 )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/mainSceneReaderNode.png" )

script["SceneReader"]["fileName"].setValue( "${GAFFER_ROOT}/resources/gafferBot/caches/gafferBot.scc" )
viewer.view().viewportGadget().frame( script["SceneReader"]["out"].bound( "/" ) )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/sceneReaderBound.png" )

# GafferBot bounding box in Viewer
readerNode["fileName"].setValue( "${GAFFER_ROOT}/resources/gafferBot/caches/gafferBot.scc" )
viewer.view().viewportGadget().frame( readerNode["out"].bound( "/" ) )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/viewerSceneReaderBounding.png" )

# GafferBot torso in Hierarchy View
GafferSceneUI.ContextAlgo.setExpandedPaths( script.context(), IECore.PathMatcher( [ "/GAFFERBOT", "/GAFFERBOT/C_torso_GRP" ] ) )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = hierarchyView, imagePath = "images/hierarchyViewExpandedTwoLevels.png" )

# GafferBot head and left leg in main window
paths = IECore.PathMatcher( [ "/GAFFERBOT/C_torso_GRP/C_head_GRP", "/GAFFERBOT/C_torso_GRP/R_legUpper_GRP" ] )
GafferSceneUI.ContextAlgo.expand( script.context(), paths )
GafferSceneUI.ContextAlgo.expandDescendants( script.context(), paths, script["SceneReader"]["out"] )
GafferSceneUI.ContextAlgo.expandDescendants( script.context(), paths, readerNode["out"] )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/mainHeadAndLeftLegExpanded.png" )

# GafferBot head and both legs in Viewer
paths = IECore.PathMatcher( [ "/GAFFERBOT/C_torso_GRP/L_legUpper_GRP" ] )
GafferSceneUI.ContextAlgo.expand( script.context(), paths )
GafferSceneUI.ContextAlgo.expandDescendants( script.context(), paths, readerNode["out"] )
GafferSceneUI.ContextAlgo.setSelectedPaths( script.context(), paths )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerHeadAndLegsExpanded.png" )

# Camera and SceneReader node in main window
script["Camera"] = GafferScene.Camera()
cameraNode = script["Camera"]
script.selection().clear()
script.selection().add( cameraNode )
Gaffer.MetadataAlgo.setFocusNode( script, cameraNode )
# Approximate the default viewport position
viewer.view().viewportGadget().frame( imath.Box3f( imath.V3f( 0, -1.75, 0 ), imath.V3f( 5, 5, 5 ) ) )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/mainCameraNode.png" )

# Grouped nodes in Gaffer
script["Group"] = GafferScene.Group()
groupNode = script["Group"]
groupNode["in"][0].setInput( readerNode["out"] )
groupNode["in"][1].setInput( cameraNode["out"] )
script.selection().clear()
script.selection().add( groupNode )
Gaffer.MetadataAlgo.setFocusNode( script, groupNode )
viewer.view()["minimumExpansionDepth"].setValue( 999 )
GafferSceneUI.ContextAlgo.clearExpansion( script.context() )
GafferSceneUI.ContextAlgo.expand( script.context(), IECore.PathMatcher( [ "/group" ] ) )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/mainGroupNode.png" )

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

# Camera rotated, with rotate tool on, in Viewer
translateTool["active"].setValue( False )
cameraNode["transform"]["rotate"].setValue( imath.V3f( 0, 30, 0 ) )
for i in viewer._Viewer__toolChooser.tools():
	if type( i ) == GafferSceneUI.RotateTool:
		rotateTool = i
rotateTool["active"].setValue( True )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerCameraRotated.png" )

# Camera node in Node Editor window
nodeEditorWindow = GafferUI.NodeEditor.acquire( cameraNode, floating=True )
nodeEditorWindow._qtWidget().setFocus()
GafferUI.PlugValueWidget.acquire( cameraNode["transform"] )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/nodeEditorWindowCameraTransform.png" )

del nodeEditorWindow
del readerNode
del groupNode
del cameraNode

# Render settings graph in Graph Editor
script["fileName"].setValue( os.path.abspath( "scripts/renderSettings.gfr" ) )
script.load()
script.selection().clear()
script.selection().add( script["Catalogue"] )
Gaffer.MetadataAlgo.setFocusNode( script, script["Catalogue"] )
graphEditor.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorRenderSettings.png" )

# GafferBot render without lighting in main window
def __renderAndGrab( script, widget, imagePath, delay = 15 ) :

	script["variables"]["imageCataloguePort"]["value"].setValue( script["Catalogue"].displayDriverServer().portNumber() )
	script["InteractiveAppleseedRender"]["state"].setValue( script["InteractiveAppleseedRender"].State.Running )
	__delay( delay )

	viewport = scriptWindow.getLayout().editors( GafferUI.Viewer )[0].view().viewportGadget()
	viewport.frame( viewport.getPrimaryChild().bound() )
	GafferUI.EventLoop.waitForIdle()

	GafferUI.WidgetAlgo.grab( widget = widget, imagePath = imagePath )
	script["InteractiveAppleseedRender"]["state"].setValue( script["InteractiveAppleseedRender"].State.Stopped )

__renderAndGrab( script, scriptWindow, "images/mainRenderGrey.png", delay = 1 )

# Render settings with gap in main window
script["fileName"].setValue( os.path.abspath( "scripts/renderSettingsWithGap.gfr" ) )
script.load()
script.selection().add( [ script["StandardOptions"], script["AppleseedOptions"], script["Outputs"], script["InteractiveAppleseedRender"], script["Catalogue"] ] )
graphEditor.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/mainRenderSettingsWithGap.png" )

# First shader assignment in Graph Editor
script["fileName"].setValue( os.path.abspath( "scripts/firstShaderAssignment.gfr" ) )
script.load()
script.selection().add( script["ShaderAssignment"] )
Gaffer.MetadataAlgo.setFocusNode( script, script["ShaderAssignment"] )
graphEditor.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorFirstShaderNodes.png" )

# Environment light in Graph Editor
script["fileName"].setValue( os.path.abspath( "scripts/firstLight.gfr" ) )
script.load()
script.selection().add( script["hosek_environment_edf"] )
Gaffer.MetadataAlgo.setFocusNode( script, script["hosek_environment_edf"] )
graphEditor.frame( Gaffer.StandardSet( [ script["Group"], script["hosek_environment_edf"] ] ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorEnvironmentLightNode.png" )

# GafferBot render with lighting in Viewer
script.selection().clear()
script.selection().add( script["Catalogue"] )
Gaffer.MetadataAlgo.setFocusNode( script, script["Catalogue"] )
__renderAndGrab( script, viewer, "images/viewerRenderOneShader.png" )

# GafferBot render with lighting and textures in Viewer
script["fileName"].setValue( os.path.abspath( "scripts/textures.gfr" ) )
script.load()
script.selection().add( script["Catalogue"] )
Gaffer.MetadataAlgo.setFocusNode( script, script["Catalogue"] )
__renderAndGrab( script, viewer, "images/viewerRenderTextures.png" )

# Second shader assignment in Graph Editor
script["fileName"].setValue( os.path.abspath( "scripts/secondShaderAssignment.gfr" ) )
script.load()
script.selection().add( script["ShaderAssignment1"] )
Gaffer.MetadataAlgo.setFocusNode( script, script["ShaderAssignment"] )
graphEditor.frame( Gaffer.StandardSet( [ script["as_disney_material"], script["as_disney_material1"], script["ShaderAssignment"], script["ShaderAssignment1"] ] ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorSecondShaderNodes.png" )

# GafferBot render with second shader assignment in main window
script.selection().clear()
script.selection().add( script["Catalogue"] )
Gaffer.MetadataAlgo.setFocusNode( script, script["Catalogue"] )
graphEditor.frame( script.children( Gaffer.Node ) )
__renderAndGrab( script, scriptWindow, "images/mainRenderTwoShaders.png" )

# PathFilter node in Graph Editor
script["fileName"].setValue( os.path.abspath( "scripts/secondShaderAssignmentFiltered.gfr" ) )
script.load()
script.selection().add( script["PathFilter"] )
Gaffer.MetadataAlgo.setFocusNode( script, script["PathFilter"] )
graphEditor.frame( Gaffer.StandardSet( [ script["PathFilter"], script["ShaderAssignment1"] ] ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorPathFilterNode.png" )

# GafferBot node and mouth selection in Viewer
script.selection().clear()
script.selection().add( script["ShaderAssignment1"] )
Gaffer.MetadataAlgo.setFocusNode( script, script["ShaderAssignment1"] )

paths = IECore.PathMatcher( [ "/group/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT/C_browNose001_REN", "/group/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT/C_mouthGrill001_REN" ] )
GafferSceneUI.ContextAlgo.setSelectedPaths( script.context(), paths )
GafferUI.EventLoop.waitForIdle()
paths = IECore.PathMatcher( [ "/group/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT" ] )
viewer.view().frame( paths, direction = imath.V3f( -0.2, -0.2, -1 ) )
__delay( 0.1 )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerSelectionFace.png" )

# GafferBot final render in Viewer
script.selection().clear()
script.selection().add( script["Catalogue"] )
__renderAndGrab( script, viewer, "images/viewerRenderFinal.png" )
