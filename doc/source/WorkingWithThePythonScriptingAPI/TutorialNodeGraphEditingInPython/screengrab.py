# BuildTarget: images/graphEditorAllNodes.png
# BuildTarget: images/graphEditorGroupConnections.png
# BuildTarget: images/graphEditorRearrangedNodes.png
# BuildTarget: images/graphEditorShaderAssignmentConnections.png
# BuildTarget: images/mainWindowFinalScene.png
# BuildTarget: images/mainWindowSphereNode.png
# BuildTarget: images/nodeEditorOpenGLPlug.png
# BuildTarget: images/pythonEditorHelloWorld.png
# BuildTarget: images/pythonEditorNodeReference.png
# BuildTarget: images/pythonEditorPlugReference.png
# BuildTarget: images/pythonEditorPlugValueReference.png
# BuildTarget: images/viewerCameraPosition.png
# BuildTarget: images/viewerFinalScene.png
# BuildTarget: images/viewerSphereRadius.png

import os
import IECore
import imath
import time

import Gaffer
import GafferScene

import GafferUI
import GafferSceneUI

mainWindow = GafferUI.ScriptWindow.acquire( script )
pythonEditor = mainWindow.getLayout().editors( GafferUI.PythonEditor )[0]
graphEditor = mainWindow.getLayout().editors( GafferUI.GraphEditor )[0]
nodeEditor = mainWindow.getLayout().editors( GafferUI.NodeEditor )[0]
viewer = mainWindow.getLayout().editors( GafferUI.Viewer )[0]
hierarchyView = mainWindow.getLayout().editors( GafferSceneUI.HierarchyView )[0]

# Delay script for x seconds
def __delay( delay ) :
	endTime = time.time() + delay
	while time.time() < endTime :
		GafferUI.EventLoop.waitForIdle( 1 )

# "Hello World" in Python Editor
pythonEditor.reveal()
pythonEditor.inputWidget().setText( 'print( "Hello World!" )' )
pythonEditor.execute()
GafferUI.WidgetAlgo.grab( widget = pythonEditor.parent(), imagePath = "images/pythonEditorHelloWorld.png" )

# Sphere node added by the Python Editor in the main window
pythonEditor.inputWidget().setText( """import GafferScene
mySphere = GafferScene.Sphere()
root.addChild( mySphere )""" )
pythonEditor.execute()
GafferUI.WidgetAlgo.grab( widget = mainWindow, imagePath = "images/mainWindowSphereNode.png" )
pythonEditor.outputWidget().setText( "" )

# All nodes, unconnected, in Graph Editor
script.addChild( GafferScene.OpenGLShader() )
script.addChild( GafferScene.ShaderAssignment() )
script.addChild( GafferScene.PathFilter() )
script.addChild( GafferScene.Camera() )
script.addChild( GafferScene.Group() )
__delay( 0.1 )
graphEditor.frame( Gaffer.StandardSet( [ script["Sphere"], script["OpenGLShader"], script["ShaderAssignment"], script["PathFilter"], script["Camera"], script["Group"] ] ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorAllNodes.png" )

# Node reference in Python Editor
pythonEditor.inputWidget().setText( "root['Sphere']" )
pythonEditor.execute()
pythonEditor.inputWidget().setText( "\n\nmySphere" )
pythonEditor.execute()
GafferUI.WidgetAlgo.grab( widget = pythonEditor.parent(), imagePath = "images/pythonEditorNodeReference.png" )
pythonEditor.outputWidget().setText( "" )

# Plug reference in Python Editor
pythonEditor.inputWidget().setText( "root['Sphere']['radius']" )
pythonEditor.execute()
GafferUI.WidgetAlgo.grab( widget = pythonEditor.parent(), imagePath = "images/pythonEditorPlugReference.png" )
pythonEditor.outputWidget().setText( "" )

# Plug value reference in Python Editor
pythonEditor.inputWidget().setText( "Color3f(0, 0, 0)" )
GafferUI.WidgetAlgo.grab( widget = pythonEditor.parent(), imagePath = "images/pythonEditorPlugValueReference.png" )
pythonEditor.inputWidget().setText( "" )

# Sphere with increased radius in Viewer
pythonEditor.inputWidget().setText( "root['Sphere']['radius'].setValue( 4 )" )
pythonEditor.execute()
script.setFocus( script["Sphere"] )
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerSphereRadius.png" )
pythonEditor.outputWidget().setText( "" )

# OpenGL node with constant plug in Node Editor
script["OpenGLShader"].loadShader( "Constant" )
__delay( 0.1 )
script["OpenGLShader"]["parameters"]["Cs"].setValue( imath.Color3f( 0.25, 0.75, 0.25 ) )
script.selection().add( script["OpenGLShader"] )
GafferUI.WidgetAlgo.grab( widget = nodeEditor, imagePath = "images/nodeEditorOpenGLPlug.png" )

# Camera node with adjusted translate in Viewer
script["Camera"]["transform"]["translate"]["z"].setValue( 8 )
script.setFocus( script["Camera"] )
paths = IECore.PathMatcher( [ "/camera" ] )
GafferSceneUI.ContextAlgo.setSelectedPaths( script.context(), paths )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerCameraPosition.png" )

# ShaderAssignment node with connections in Graph Editor
script['ShaderAssignment']['in'].setInput( script['Sphere']['out'] )
script['ShaderAssignment']['shader'].setInput( script['OpenGLShader']['out'] )
script['ShaderAssignment']['filter'].setInput( script['PathFilter']['out'] )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorShaderAssignmentConnections.png" )

# Group node with connections in Graph Editor
script['Group']['in'][0].setInput( script['ShaderAssignment']['out'] )
script['Group']['in'][1].setInput( script['Camera']['out'] )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorGroupConnections.png" )

# Rearranged nodes in Graph Editor
script["fileName"].setValue( os.path.abspath( "scripts/tutorialPreview.gfr" ) )
script.load()
mainWindow = GafferUI.ScriptWindow.acquire( script )
graphEditor = mainWindow.getLayout().editors( GafferUI.GraphEditor )[0]
viewer = mainWindow.getLayout().editors( GafferUI.Viewer )[0]
graphEditor.frame( Gaffer.StandardSet( [ script["Sphere"], script["OpenGLShader"], script["ShaderAssignment"], script["PathFilter"], script["Camera"], script["Group"] ] ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorRearrangedNodes.png" )

# Final script in Viewer
script.setFocus( script["Group"] )
paths = IECore.PathMatcher( [ "/group" ] )
GafferSceneUI.ContextAlgo.setExpandedPaths( script.context(), paths )
GafferSceneUI.ContextAlgo.expandDescendants( script.context(), paths, script["Group"]["out"] )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/viewerFinalScene.png" )

# Final script in main window
GafferUI.WidgetAlgo.grab( widget = mainWindow, imagePath = "images/mainWindowFinalScene.png" )
