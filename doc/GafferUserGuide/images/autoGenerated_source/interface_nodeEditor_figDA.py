import IECore
import GafferUI
import GafferScene
import GafferSceneUI
import os
scriptNode = script
scriptWindow = GafferUI.ScriptWindow.acquire( script )
layout = eval( "GafferUI.CompoundEditor( scriptNode, children = {'tabs': (GafferUI.NodeEditor( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False]} )" )
scriptWindow.setLayout( layout )
scriptWindow._Widget__qtWidget.resize(519,593)
for nodeName in ['RenderManAttributes']:
	script.selection().add( script.descendant( nodeName ) )
script.context()["ui:scene:expandedPaths"] = GafferScene.PathMatcherData( GafferScene.PathMatcher( ['/'] ) )
script.context()["ui:scene:selectedPaths"] = IECore.StringVectorData( [  ] )
##############################################################
## IMAGE SPECIFIC COMMANDS BELOW #############################

nodeEditor = layout.editors(GafferUI.NodeEditor)[0]
#open the Shading group
plugWidget = nodeEditor.nodeUI().plugValueWidget(script['RenderManAttributes']['attributes']['shadingRate'])
collapsible = plugWidget.ancestor(GafferUI.Collapsible)
collapsible.setCollapsible(False)
#open the Visibility group
plugWidget = nodeEditor.nodeUI().plugValueWidget(script['RenderManAttributes']['attributes']['cameraVisibility'])
collapsible = plugWidget.ancestor(GafferUI.Collapsible)
collapsible.setCollapsible(False)
