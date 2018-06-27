# BuildTarget: images/scriptEditor.png

import Gaffer
import GafferScene

import GafferUI

scriptWindow = GafferUI.ScriptWindow.acquire( script )
scriptEditor = scriptWindow.getLayout().editors( GafferUI.ScriptEditor )[0]
scriptEditor.inputWidget().setText( 'print "Hello World!", script' )
scriptEditor.inputWidget()._qtWidget().selectAll()
scriptEditor.execute()
scriptEditor.reveal()
GafferUI.WidgetAlgo.grab( widget = scriptEditor.parent(), imagePath = "images/scriptEditor.png" )

script["Node"] = Gaffer.Node( "Node" )
script["Node"]["firstPlug"] = Gaffer.IntPlug( defaultValue = 0 )
script["Node"]["secondPlug"] = Gaffer.FloatPlug( defaultValue = 0 )
GafferUI.WidgetAlgo.grab( widget = GafferUI.NodeEditor.acquire( script["Node"], floating=True ), imagePath = "images/nodeEditor.png" )
del script["Node"]

script["Sphere"] = GafferScene.Sphere()
scriptEditor.inputWidget().setText( 'script["Sphere"]["radius"].getValue()' )
scriptEditor.inputWidget()._qtWidget().selectAll()
scriptEditor.outputWidget().setText( '' )
scriptEditor.execute()
scriptEditor.reveal()
GafferUI.WidgetAlgo.grab( widget = scriptEditor.parent(), imagePath = "images/scriptEditorGetValue.png" )

script["Sphere"]["radius"].setValue( 10.5 )
script["MeshToPoints"] = GafferScene.MeshToPoints( "MeshToPoints" )
script["MeshToPoints"]["type"].setValue( "sphere" )
script["MeshToPoints"]["in"].setInput( script["Sphere"]["out"] )
script.selection().add( script["MeshToPoints"] )
viewer = scriptWindow.getLayout().editors( GafferUI.Viewer )[0]
# delay so it can redraw
GafferUI.EventLoop.waitForIdle()
viewer.view().viewportGadget().frame( script["MeshToPoints"]["out"].bound( "/sphere" ) )
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/meshToPointsViewer.png" )

graph = scriptWindow.getLayout().editors( GafferUI.NodeGraph )[0]
graph.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graph, imagePath = "images/meshToPointsNodeGraph.png" )

script["Camera"] = GafferScene.Camera()
script["Group"] = GafferScene.Group()
script["Group"]["in"][0].setInput( script["MeshToPoints"]["out"] )
script["Group"]["in"][1].setInput( script["Camera"]["out"] )
script.selection().clear()
script.selection().add( script["Group"] )
graph.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graph, imagePath = "images/group.png" )
