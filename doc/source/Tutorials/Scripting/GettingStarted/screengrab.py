# BuildTarget: images/scriptEditorEmpty.png

import IECore
import imath
import time

import Gaffer
import GafferScene

import GafferUI
import GafferSceneUI

mainWindow = GafferUI.ScriptWindow.acquire( script )
scriptEditor = mainWindow.getLayout().editors( GafferUI.ScriptEditor )[0]
graphEditor = mainWindow.getLayout().editors( GafferUI.GraphEditor )[0]
nodeEditor = mainWindow.getLayout().editors( GafferUI.NodeEditor )[0]
viewer = mainWindow.getLayout().editors( GafferUI.Viewer )[0]
hierarchyView = mainWindow.getLayout().editors( GafferSceneUI.HierarchyView )[0]

# Delay script for x seconds
def __delay( delay ) :
	endTime = time.time() + delay
	while time.time() < endTime :
		GafferUI.EventLoop.waitForIdle( 1 )

# Empty Script Editor
scriptEditor.reveal()
GafferUI.WidgetAlgo.grab( widget = scriptEditor.parent(), imagePath = "images/scriptEditorEmpty.png" )

# "Hello World" in Script Editor
scriptEditor.inputWidget().setText( 'print "Hello World!"' )
scriptEditor.execute()
scriptEditor.inputWidget().setText( 'print "Hello World!"' )
GafferUI.WidgetAlgo.grab( widget = scriptEditor.parent(), imagePath = "images/scriptEditorHello.png" )

# Generic node in Graph Editor
script["Node"] = Gaffer.Node( "Node" )
genericNode = script["Node"]
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorGenericNode.png" )

# Generic node renamed in Graph Editor
genericNode.setName( "MyVeryFirstNode" )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorGenericNodeRenamed.png" )

# Generic node with two plugs in Graph Editor
genericNode["IntPlug"] = Gaffer.IntPlug( defaultValue = 0 )
genericNode["FloatPlug"] = Gaffer.FloatPlug( defaultValue = 0 )
graphEditor.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorGenericNodeTwoPlugs.png" )

# Generic node with two plugs in Node Editor
nodeEditorWindow = GafferUI.NodeEditor.acquire( genericNode, floating=True )
nodeEditorWindow._qtWidget().setFocus()
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/nodeEditorGenericNode.png" )
# nodeEditorWindow.parent().close()
del nodeEditorWindow

# Generic node with one plug in Graph Editor
genericNode.removeChild( genericNode["IntPlug"] )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorGenericNodeOnePlug.png" )
# script.removeChild( genericNode )
del genericNode

# Sphere in Script Editor
script["Sphere"] = GafferScene.Sphere()
sphereNode = script["Sphere"]
script.selection().clear()
script.selection().add( sphereNode )
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerSphere.png" )

# Viewport only exists after a selection was made
viewport = viewer.view().viewportGadget()
viewportCamDefaultPos = viewport.getCameraTransform()

# Sphere plugs in Viewer
sphereNode["radius"].setValue( 3 )
sphereNode["thetaMax"].setValue( 180 )
sphereNode["name"].setValue( "mySphere" )
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerSpherePlugs.png" )

# Sphere plugs in Script Editor
nodeEditorWindow = GafferUI.NodeEditor.acquire( sphereNode, floating=True )
nodeEditorWindow._qtWidget().setFocus()
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/nodeEditorSpherePlugs.png" )
nodeEditorWindow.parent().close()
del nodeEditorWindow

# Sphere with more divisions in Viewer
sphereNode["divisions"].setValue( imath.V2i( 80, 160 ) )
path = IECore.PathMatcher( [ "/mySphere" ] )
GafferSceneUI.ContextAlgo.setSelectedPaths( script.context(), path )
#viewport.setCameraTransform( imath.M44f((0.707106769, 0, -0.707106769, 0), (-0.298836261, 0.906307817, -0.298836261, 0), (0.640856385, 0.4226183, 0.640856385, 0), (2.1569376, 1.42241168, 2.1569376, 1))) # TODO: Do this without magic numbers
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerSphereDivisions.png" )

# Sphere with transform in Viewer
viewport.setCameraTransform( viewportCamDefaultPos )
sphereNode["transform"]["translate"].setValue( imath.V3f( 2, 0, 2 ) )
path = IECore.PathMatcher()
GafferSceneUI.ContextAlgo.setSelectedPaths( script.context(), path )
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerSphereTransform.png" )

# Mesh node in Viewer
script["MeshToPoints"] = GafferScene.MeshToPoints( "MeshToPoints" )
meshNode = script["MeshToPoints"]
meshNode["type"].setValue( "sphere" )
meshNode["in"].setInput( sphereNode["out"] )
script.selection().clear()
script.selection().add( meshNode )
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerMeshToPoints.png" )

# Mesh node in Graph Editor
graphEditor.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorMeshToPoints.png" )

# Camera and Group nodes in the Graph Editor
script["Camera"] = GafferScene.Camera()
cameraNode = script["Camera"]
script["Group"] = GafferScene.Group()
groupNode = script["Group"]
groupNode["in"][0].setInput( meshNode["out"] )
groupNode["in"][1].setInput( cameraNode["out"] )
script.selection().clear()
__delay( 1 )
graphEditor.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorGroup.png" )
