# BuildTarget: images/conceptContextsContextVariablesInExpressions.png
# BuildTarget: images/conceptContextsContextVariablesInExpressionsNodeEditor.png
# BuildTarget: images/conceptContextsEditorFocus.png
# BuildTarget: images/conceptContextsInParallelBranches.png
# BuildTarget: images/conceptContextsInParallelBranchesDownstream.png
# BuildTarget: images/conceptContextsInParallelBranchesDownstreamNodeEditor.png
# BuildTarget: images/conceptContextsInParallelBranchesNodeEditor.png
# BuildTarget: images/conceptContextsQueryingResults.png
# BuildTarget: images/conceptContextsQueryingResultsFixedPythonEditor.png
# BuildTarget: images/conceptContextsQueryingResultsPythonEditor.png
# BuildTarget: images/conceptContextsQueryingResultsSceneInspector.png
# BuildTarget: images/conceptContextsRandomNode1.png
# BuildTarget: images/conceptContextsRandomNode2.png
# BuildTarget: images/conceptContextsRandomNode2NodeEditor.png
# BuildTarget: images/conceptContextsReadingContextVariable.png

import os
import time

import imath
import IECore
import Gaffer
import GafferScene
import GafferUI
import GafferSceneUI

# Delay for x seconds
def __delay( delay ) :
	endtime = time.time() + delay
	while time.time() < endtime :
		GafferUI.EventLoop.waitForIdle( 1 )

mainWindow = GafferUI.ScriptWindow.acquire( script )
viewer = mainWindow.getLayout().editors( GafferUI.Viewer )[0]
graphEditor = mainWindow.getLayout().editors( GafferUI.GraphEditor )[0]
nodeEditor = mainWindow.getLayout().editors( GafferUI.NodeEditor )[0]
sceneInspector = mainWindow.getLayout().editors( GafferSceneUI.SceneInspector )[0]
hierarchyView = mainWindow.getLayout().editors( GafferSceneUI.HierarchyView )[0]
pythonEditor = mainWindow.getLayout().editors( GafferUI.PythonEditor )[0]

# Concept: Reading a Context Variable
textNode = GafferScene.Text()
contextVariablesNode = Gaffer.ContextVariables()
contextVariablesNode.setup( GafferScene.ScenePlug( "in", ) )
contextVariablesNode["variables"].addChild( Gaffer.NameValuePlug( "", Gaffer.StringPlug( "value", defaultValue = '', flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ), True, "member1", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
textNode["text"].setValue( '${message}' )
contextVariablesNode["variables"]["member1"]["name"].setValue( 'message' )
contextVariablesNode["variables"]["member1"]["value"].setValue( 'received' )
contextVariablesNode["in"].setInput( textNode["out"] )
script.addChild( textNode )
script.addChild( contextVariablesNode )
script.selection().add( script["ContextVariables"] )
script.setFocus( script["ContextVariables"] )
graphEditor.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = mainWindow, imagePath = "images/conceptContextsReadingContextVariable.png" )

# Concept: Editor focus
script.selection().clear()
script.selection().add( script["Text"] )
script.setFocus( script["Text"] )
GafferUI.WidgetAlgo.grab( widget = mainWindow, imagePath = "images/conceptContextsEditorFocus.png" )

# Concept: Context Variables in expressions
script["fileName"].setValue( "scripts/conceptContextsContextVariablesInExpressions.gfr" )
script.load()
script.selection().add( Gaffer.StandardSet( [ script["Cube"] ] ) )
script.setFocus( script["Cube"] )
graphEditor.frame( Gaffer.StandardSet( [ script["Expression"], script["Cube"] ] ) )
GafferUI.PlugValueWidget.acquire( script["Cube"]["transform"] )
GafferUI.WidgetAlgo.grab( widget = mainWindow, imagePath = "images/conceptContextsContextVariablesInExpressions.png" )

# Concept: Context Variables in expressions (Node Editor)
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["Expression"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
nodeEditorWindow.parent()._qtWidget().resize( 408, 400 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/conceptContextsContextVariablesInExpressionsNodeEditor.png" )
nodeEditorWindow.parent().close()
del nodeEditorWindow
__delay( 0.1 )

# Concept: Contexts and the Random node
script["Cube"].setName( "Cube_old" )
script["Cube1"].setName( "Cube" )
script.selection().clear()
script.selection().add( Gaffer.StandardSet( [ script["Transform"] ] ) )
script.setFocus( script["Transform"] )
graphEditor.frame( Gaffer.StandardSet( [ script["Cube"], script["Duplicate"], script["Transform"] ] ) )
GafferUI.WidgetAlgo.grab( widget = mainWindow, imagePath = "images/conceptContextsRandomNode1.png" )

# Concept: Context and the Random node 2
script["Random"] = Gaffer.Random()
script.addChild( script["Random"] )
script["Random"].addChild( Gaffer.V2fPlug( "__uiPosition", defaultValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["Transform"]["transform"]["translate"]["y"].setInput( script["Random"]["outFloat"] )
script["Random"]["seedVariable"].setValue( "scene:path" )
script["Random"]["floatRange"].setValue( imath.V2f( -1, 1 ) )
script["Random"]["__uiPosition"].setValue( imath.V2f( 123.21, -2.25 ) )
GafferUI.WidgetAlgo.grab( widget = mainWindow, imagePath = "images/conceptContextsRandomNode2.png" )

# Concept: Context and the Random node 2 (Node Editor)
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["Random"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/conceptContextsRandomNode2NodeEditor.png" )
nodeEditorWindow.parent().close()
del nodeEditorWindow
__delay( 0.1 )

# Concept: Querying results
GafferSceneUI.ContextAlgo.setSelectedPaths( script.context(), IECore.PathMatcher( [ "/cube2" ] ) )
#sceneInspector.reveal()
# Expand the "Transform" section
#sceneInspector._SceneInspector__sections[2]._Section__collapsible.setCollapsed( False )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = mainWindow, imagePath = "images/conceptContextsQueryingResults.png" )

# Concept: Querying results (Python Editor)
with GafferUI.Window() as tempWindow :
	tempPythonEditor = GafferUI.PythonEditor( script )
tempWindow._qtWidget().resize( 512, 384 )
tempWindow.setVisible( True )
text = 'print( root["Transform"]["transform"]["translate"]["y"].getValue() )'
tempPythonEditor.inputWidget().setText( text )
tempPythonEditor.execute()
tempPythonEditor.inputWidget().setText( text )
GafferUI.WidgetAlgo.grab( widget = tempPythonEditor.outputWidget(), imagePath = "images/conceptContextsQueryingResultsPythonEditor.png" )

# Concept: Querying results fixed
tempPythonEditor.outputWidget().setText( "" )
text = 'context = Gaffer.Context( root.context() )\ncontext["scene:path"] = IECore.InternedStringVectorData( ["cube2"] )\nwith context:\n    print( root["Transform"]["transform"]["translate"]["y"].getValue() )'
tempPythonEditor.inputWidget().setText( text )
tempPythonEditor.execute()
tempPythonEditor.inputWidget().setText( text )
GafferUI.WidgetAlgo.grab( widget = tempPythonEditor.outputWidget(), imagePath = "images/conceptContextsQueryingResultsFixedPythonEditor.png" )
tempWindow.close()
del tempWindow
del tempPythonEditor
__delay( 0.1 )

# Concept: Querying results (Scene Inspector)
with GafferUI.Window() as tempWindow :
	tempSceneInspector = GafferSceneUI.SceneInspector( script )
tempSceneInspector._SceneInspector__sections[2]._Section__collapsible.setCollapsed( False )
tempWindow._qtWidget().resize( 512, 400 )
tempWindow.setVisible( True )
GafferUI.WidgetAlgo.grab( widget = tempSceneInspector, imagePath = "images/conceptContextsQueryingResultsSceneInspector.png" )
tempWindow.close()
del tempWindow
del tempSceneInspector
__delay( 0.1 )

# Concept: Contexts in parallel branches (Node Editor)
script["fileName"].setValue( os.path.abspath( "scripts/conceptContextsInParallelBranches.gfr" ) )
script.load()
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["Expression"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
nodeEditorWindow.parent()._qtWidget().resize( 408, 400 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/conceptContextsInParallelBranchesNodeEditor.png" )
nodeEditorWindow.parent().close()
del nodeEditorWindow
__delay( 0.1 )

# Concept: Contexts in parallel branches
script.selection().add( Gaffer.StandardSet( [ script["Merge"] ] ) )
script.setFocus( script["Merge"] )
# Layout: Graph Editor, 1 Viewer
layouts = GafferUI.Layouts.acquire( mainWindow.scriptNode().applicationRoot() )
layouts.add( 'graphAndViewer', "GafferUI.CompoundEditor( scriptNode, _state={ 'children' : ( GafferUI.SplitContainer.Orientation.Vertical, 0.960419, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.5, ( {'tabs': (GafferUI.Viewer( scriptNode ), GafferSceneUI.UVInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0}, {'tabs': (GafferUI.GraphEditor( scriptNode ), GafferUI.AnimationEditor( scriptNode ), GafferSceneUI.PrimitiveInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0} ) ), {'tabs': (GafferUI.Timeline( scriptNode ),), 'tabsVisible': False, 'currentTab': 0} ) ), 'detachedPanels' : (), 'windowState' : { 'fullScreen' : False, 'screen' : -1, 'bound' : imath.Box2f( imath.V2f( 0.046875, 0.109625667 ), imath.V2f( 0.78125, 0.9073084 ) ), 'maximized' : False } } )", persistent = False )
layout = layouts.create( "graphAndViewer", mainWindow.scriptNode() )
mainWindow.setLayout( layout )
viewer = mainWindow.getLayout().editors( GafferUI.Viewer )[0]
graphEditor = mainWindow.getLayout().editors( GafferUI.GraphEditor )[0]
viewport = viewer.view().viewportGadget()
viewport.frame( viewport.getPrimaryChild().bound() )
__delay( 0.5 )
graphEditor.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = mainWindow, imagePath = "images/conceptContextsInParallelBranches.png" )

# Concept: Contexts in downstream parallel branches
script["fileName"].setValue( os.path.abspath( "scripts/conceptContextsInParallelBranchesDownstream.gfr" ) )
script.load()
# Layout: Graph Editor, 2 Viewers
layouts.add( 'graphAndViewers', "GafferUI.CompoundEditor( scriptNode, _state={ 'children' : ( GafferUI.SplitContainer.Orientation.Vertical, 0.960419, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.5, ( ( GafferUI.SplitContainer.Orientation.Horizontal, 0.5, ( {'tabs': (GafferUI.Viewer( scriptNode ), GafferSceneUI.UVInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0}, {'tabs': (GafferUI.Viewer( scriptNode ),), 'tabsVisible': True, 'currentTab': 0} ) ), {'tabs': (GafferUI.GraphEditor( scriptNode ), GafferUI.AnimationEditor( scriptNode ), GafferSceneUI.PrimitiveInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0} ) ), {'tabs': (GafferUI.Timeline( scriptNode ),), 'tabsVisible': False, 'currentTab': 0} ) ), 'detachedPanels' : (), 'windowState' : { 'fullScreen' : False, 'screen' : -1, 'bound' : imath.Box2f( imath.V2f( 0.046875, 0.111408196 ), imath.V2f( 0.78125, 0.909090936 ) ), 'maximized' : False } } )", persistent = False )
layout = layouts.create( "graphAndViewers", mainWindow.scriptNode() )
mainWindow.setLayout( layout )
viewer = mainWindow.getLayout().editors( GafferUI.Viewer )[0]
viewer2 = mainWindow.getLayout().editors( GafferUI.Viewer )[1]
graphEditor = mainWindow.getLayout().editors( GafferUI.GraphEditor )[0]
viewer.setNodeSet( Gaffer.StandardSet( [ script["ImageWriter_Daily" ] ] ) )
viewer2.setNodeSet( Gaffer.StandardSet( [ script["ImageWriter_FilmOut" ] ] ) )
__delay( 0.1 )
viewport = viewer.view().viewportGadget()
viewport2 = viewer2.view().viewportGadget()
viewport.frame( viewport.getPrimaryChild().bound() )
viewport2.frame( viewport2.getPrimaryChild().bound() )
graphEditor.frame( script.children( Gaffer.Node ) )
__delay( 0.5 )
GafferUI.WidgetAlgo.grab( widget = mainWindow, imagePath = "images/conceptContextsInParallelBranchesDownstream.png" )

# Concept: Contexts in downstream parallel branches (Node Editor)
script["fileName"].setValue( os.path.abspath( "scripts/conceptContextsInParallelBranchesDownstream.gfr" ) )
script.load()
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["Expression"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
nodeEditorWindow.parent()._qtWidget().resize( 408, 400 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/conceptContextsInParallelBranchesDownstreamNodeEditor.png" )
nodeEditorWindow.parent().close()
del nodeEditorWindow
__delay( 0.1 )
