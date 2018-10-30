# BuildTarget: images/pythonEditor.png

import Gaffer
import GafferScene

import GafferUI

scriptWindow = GafferUI.ScriptWindow.acquire( script )
pythonEditor = scriptWindow.getLayout().editors( GafferUI.PythonEditor )[0]
pythonEditor.inputWidget().setText( 'print "Hello World!", script' )
pythonEditor.inputWidget()._qtWidget().selectAll()
pythonEditor.execute()
pythonEditor.reveal()
GafferUI.WidgetAlgo.grab( widget = pythonEditor.parent(), imagePath = "images/pythonEditor.png" )

script["Node"] = Gaffer.Node( "Node" )
script["Node"]["firstPlug"] = Gaffer.IntPlug( defaultValue = 0 )
script["Node"]["secondPlug"] = Gaffer.FloatPlug( defaultValue = 0 )
GafferUI.WidgetAlgo.grab( widget = GafferUI.NodeEditor.acquire( script["Node"], floating=True ), imagePath = "images/nodeEditor.png" )
del script["Node"]

script["Sphere"] = GafferScene.Sphere()
pythonEditor.inputWidget().setText( 'script["Sphere"]["radius"].getValue()' )
pythonEditor.inputWidget()._qtWidget().selectAll()
pythonEditor.outputWidget().setText( '' )
pythonEditor.execute()
pythonEditor.reveal()
GafferUI.WidgetAlgo.grab( widget = pythonEditor.parent(), imagePath = "images/pythonEditorGetValue.png" )

script["Sphere"]["radius"].setValue( 10.5 )
script["MeshToPoints"] = GafferScene.MeshToPoints( "MeshToPoints" )
script["MeshToPoints"]["type"].setValue( "sphere" )
script["MeshToPoints"]["in"].setInput( script["Sphere"]["out"] )
script.selection().add( script["MeshToPoints"] )
viewer = scriptWindow.getLayout().editors( GafferUI.Viewer )[0]
# delay so it can redraw
GafferUI.EventLoop.waitForIdle()
viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
viewer.view().viewportGadget().frame( script["MeshToPoints"]["out"].bound( "/sphere" ) )
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/meshToPointsViewer.png" )

graph = scriptWindow.getLayout().editors( GafferUI.GraphEditor )[0]
graph.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graph, imagePath = "images/meshToPointsGraphEditor.png" )

script["Camera"] = GafferScene.Camera()
script["Group"] = GafferScene.Group()
script["Group"]["in"][0].setInput( script["MeshToPoints"]["out"] )
script["Group"]["in"][1].setInput( script["Camera"]["out"] )
script.selection().clear()
script.selection().add( script["Group"] )
graph.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graph, imagePath = "images/group.png" )
