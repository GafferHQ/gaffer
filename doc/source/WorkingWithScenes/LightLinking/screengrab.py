# BuildTarget: images/interfaceDefaultLightPlug.png
# BuildTarget: images/interfaceLightLinkSetupGraphEditor.png
# BuildTarget: images/interfaceLightSetGraphEditor.png
# BuildTarget: images/interfaceLightSetNodeEditor.png
# BuildTarget: images/interfaceLinkedLightsAttribute.png
# BuildTarget: images/interfaceLinkedLightsPlug.png
# BuildTarget: images/taskLightLinkingSetExpressionLocation.png
# BuildTarget: images/taskLightLinkingSetExpressionSet.png

import imath
import IECore
import Gaffer
import GafferScene
import GafferUI
import GafferSceneUI
import GafferCycles

scriptWindow = GafferUI.ScriptWindow.acquire( script )
viewer = scriptWindow.getLayout().editors( GafferUI.Viewer )[0]
graphEditor = scriptWindow.getLayout().editors( GafferUI.GraphEditor )[0]
hierarchyView = scriptWindow.getLayout().editors( GafferSceneUI.HierarchyView )[0]

# Base graph
script["Sphere"] = GafferScene.Sphere()
script["Group"] = GafferScene.Group()
script["Light"] = GafferCycles.CyclesLight()
script["Group"]["in"]["in0"].setInput( script["Sphere"]["out"] )
script["Group"]["in"]["in1"].setInput( script["Light"]["out"] )
script["PathFilter"] = GafferScene.PathFilter()
script["PathFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )
script["StandardAttributes"] = GafferScene.StandardAttributes()
script["StandardAttributes"]["in"].setInput( script["Group"]["out"] )
script["StandardAttributes"]["filter"].setInput( script["PathFilter"]["out"] )
script["StandardAttributes"]["attributes"]["linkedLights"]["enabled"].setValue( True )
script["StandardAttributes"]["attributes"]["linkedLights"]["value"].setValue( "/group/light" )
script.addChild( script["Sphere"] )
script.addChild( script["Light"] )
script.addChild( script["Group"] )
script.addChild( script["StandardAttributes"] )
script.addChild( script["PathFilter"] )

# Interface: the Default Light plug of a light node in the Node Editor
# TODO: "CyclesLight" label clearly visible; figure out a way to fake "ArnoldLight" label
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["Light"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
GafferUI.PlugValueWidget.acquire( script["Light"]["defaultLight"] )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/interfaceDefaultLightPlug.png" )
nodeEditorWindow.parent().close()
del nodeEditorWindow

# Interface: the linkedLights attribute in the Scene Inspector
script.selection().clear()
script.selection().add( script["StandardAttributes"] )
__path = "/group/sphere"
__paths = IECore.PathMatcher( [ __path ] )
GafferSceneUI.ContextAlgo.setSelectedPaths( script.context(), __paths )

from GafferSceneUI.SceneInspector import __AttributesSection

for imageName, sectionClass in [
	( "LinkedLightsAttribute.png", __AttributesSection )
] :

	section = sectionClass()
	section._Section__collapsible.setCollapsed( False )

	with GafferUI.Window( "Property" ) as window :

		sceneInspector = GafferSceneUI.SceneInspector( script, sections = [ section ] )
		sceneInspector.setNodeSet( Gaffer.StandardSet( [ script["StandardAttributes"] ] ) )
		sceneInspector.setTargetPaths( [ __path ] )

	window.resizeToFitChild()
	window.setVisible( True )

	GafferUI.WidgetAlgo.grab( widget = sceneInspector, imagePath = "images/interface" + imageName )

	window.close()
	del window

# Interface: a StandardAttributes node downstream of an object node
script.selection().clear()
graphEditor.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/interfaceLightLinkSetupGraphEditor.png" )

# Interface: the empty Linked Lights plug of a StandardAttributes node in the Node Editor
script["StandardAttributes"]["attributes"]["linkedLights"]["value"].setValue( "" )
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["StandardAttributes"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
GafferUI.PlugValueWidget.acquire( script["StandardAttributes"]["attributes"]["linkedLights"] )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/interfaceLinkedLightsPlug.png" )
nodeEditorWindow.parent().close()
del nodeEditorWindow

# Task: the light linking set expression with a location
script["StandardAttributes"]["attributes"]["linkedLights"]["value"].setValue( "/group/light" )
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["StandardAttributes"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/taskLightLinkingSetExpressionLocation.png" )
nodeEditorWindow.parent().close()
del nodeEditorWindow

# Task: a Set node in the Node Editor
script["Set"] = GafferScene.Set()
script["Set"]["in"].setInput( script["Light"]["out"] )
script["Set"]["name"].setValue( "myLights" )
script["Set"]["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )
script["Group"]["in"][1].setInput( script["Set"]["out"] )
script.addChild( script["Set"] )
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["Set"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/interfaceLightSetNodeEditor.png" )
nodeEditorWindow.parent().close()
del nodeEditorWindow

# Task: a Set node downstream of a light node in the Graph Editor
graphGadget = GafferUI.GraphGadget( script )
graphGadget.getLayout().layoutNodes( graphGadget )
graphEditor.frame( Gaffer.StandardSet( [ script["Set"] ] ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/interfaceLightSetGraphEditor.png" )

# Task: the light linking set expression with a set
script["StandardAttributes"]["attributes"]["linkedLights"]["value"].setValue( "myLights" )
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["StandardAttributes"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/taskLightLinkingSetExpressionSet.png" )
nodeEditorWindow.parent().close()
del nodeEditorWindow
