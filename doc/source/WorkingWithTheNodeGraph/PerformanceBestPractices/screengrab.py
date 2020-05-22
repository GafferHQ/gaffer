# BuildTarget: images/graphEditorGroupFirst.png images/graphEditorGroupSecond.png images/conceptPerformanceBestPracticesContextsViewer.png images/conceptPerformanceBestPracticesContextsGraphEditor.png images/conceptPerformanceBestPracticesContextsStats.png images/conceptPerformanceBestPracticesContextsImprovedStats.png

import os
import time
import subprocess32 as subprocess

import imath
import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

# Delay for x seconds
def __delay( delay ) :
	endtime = time.time() + delay
	while time.time() < endtime :
		GafferUI.EventLoop.waitForIdle( 1 )

mainWindow = GafferUI.ScriptWindow.acquire( script )
viewer = mainWindow.getLayout().editors( GafferUI.Viewer )[0]
graphEditor = mainWindow.getLayout().editors( GafferUI.GraphEditor )[0]

# First sample node graph in Graph Editor
script["fileName"].setValue( os.path.abspath( "scripts/groupFirst.gfr" ) )
script.load()
graphEditor.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorGroupFirst.png" )

# Second sample node graph in Graph Editor
script["fileName"].setValue( os.path.abspath( "scripts/groupSecond.gfr" ) )
script.load()
graphEditor.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorGroupSecond.png" )

# Concept: Context performance in Viewer
script["fileName"].setValue( os.path.abspath( "scripts/conceptPerformanceBestPracticesContexts.gfr" ) )
script.load()
script.selection().add( Gaffer.StandardSet( [ script["CollectScenes"] ] ) )
__delay( 0.1 )
viewport = viewer.view().viewportGadget()
viewport.frame( viewport.getPrimaryChild().bound() )
viewer.view()["minimumExpansionDepth"].setValue( 100 )
__delay( 0.5 )
# Side-on look at scene
cameraTransform = imath.M44f(
	( 1, 0, 0, 0 ),
	( 0, 1, 0, 0 ),
	( 0, 0, 1, 0 ),
	( 60, 5, 200, 1 )
	)
viewport.setCameraTransform( cameraTransform )
GafferUI.WidgetAlgo.grab( widget = viewer, imagePath = "images/conceptPerformanceBestPracticesContextsViewer.png" )

# Concept: Context performance network in Graph Editor
graphEditor.frame( script.children( Gaffer.Node ) )
with GafferUI.Window() as window :
	graphEditorWindow = GafferUI.GraphEditor( script )
graphEditorWindow.parent().reveal()
graphEditorWindow.parent()._qtWidget().resize( 800, 520 )
__delay( 0.01 )
graphEditorWindow.frame( script.children( Gaffer.Node ) )
__delay( 0.01 )
GafferUI.WidgetAlgo.grab( widget = graphEditorWindow, imagePath = "images/conceptPerformanceBestPracticesContextsGraphEditor.png" )
graphEditorWindow.parent().close()
del graphEditorWindow

# Concept: Context performance network with stats
name = "conceptPerformanceBestPracticesContexts"
nameImproved = name + "Improved"
inputScript = os.path.abspath( "scripts/{name}.gfr".format( name = name ) )
outputScript = os.path.abspath( "scripts/{name}.gfr".format( name = name + "Stats" ) )
improvedScript = os.path.abspath( "scripts/{name}.gfr".format( name = nameImproved ) )
command = "gaffer stats {inputScript} -scene {node} -contextMonitor -annotatedScript {outputScript}".format(
	inputScript = inputScript,
	node = "CollectScenes",
	outputScript = outputScript
	)
process = subprocess.Popen( command, shell=True, stderr = subprocess.PIPE )
process.wait()
script["fileName"].setValue( outputScript )
script.load()
with GafferUI.Window() as window :
	graphEditorWindow = GafferUI.GraphEditor( script )
graphEditorWindow.parent().reveal()
graphEditorWindow.parent()._qtWidget().resize( 800, 520 )
__delay( 0.01 )
GafferUI.WidgetAlgo.grab( widget = graphEditorWindow, imagePath = "images/{imageName}.png".format( imageName = name + "Stats" ) )
graphEditorWindow.parent().close()
del graphEditorWindow
script.addChild( Gaffer.DeleteContextVariables() )
script["DeleteContextVariables"].setup( GafferScene.ScenePlug( "in", ) )
script["DeleteContextVariables"].addChild( Gaffer.V2fPlug( "__uiPosition", defaultValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["DeleteContextVariables"]["variables"].setValue( 'collect:rootName' )
script["DeleteContextVariables"]["in"].setInput( script["Group"]["out"] )
script["Transform"]["in"].setInput( script["DeleteContextVariables"]["out"] )
script["DeleteContextVariables"]["__uiPosition"].setValue( imath.V2f( -3.0, 4.75 ) )
script["fileName"].setValue( improvedScript )
script.save()

# Concept: Context performance network with improved stats
outputScript = os.path.abspath( "scripts/{name}.gfr".format( name = nameImproved + "Stats" ) )
command = "gaffer stats {inputScript} -scene {node} -contextMonitor -annotatedScript {outputScript}".format(
	inputScript = improvedScript,
	node = "CollectScenes",
	outputScript = outputScript
	)
process = subprocess.Popen( command, shell=True, stderr = subprocess.PIPE )
process.wait()
script["fileName"].setValue( outputScript )
script.load()
with GafferUI.Window() as window :
	graphEditorWindow = GafferUI.GraphEditor( script )
graphEditorWindow.parent().reveal()
graphEditorWindow.parent()._qtWidget().resize( 800, 520 )
__delay( 0.01 )
GafferUI.WidgetAlgo.grab( widget = graphEditorWindow, imagePath = "images/{imageName}.png".format( imageName = nameImproved + "Stats" ) )
graphEditorWindow.parent().close()
del graphEditorWindow