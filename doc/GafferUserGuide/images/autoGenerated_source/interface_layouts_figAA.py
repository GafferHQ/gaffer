import IECore
import GafferUI
import GafferScene
import os
scriptNode = script
scriptWindow = GafferUI.ScriptWindow.acquire( script )
layout = eval( "GafferUI.CompoundEditor( scriptNode, children = ( GafferUI.SplitContainer.Orientation.Horizontal, 0.495437, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.528027, ( {'tabs': (GafferUI.Viewer( scriptNode ),), 'currentTab': 0}, ( GafferUI.SplitContainer.Orientation.Vertical, 0.840964, ( {'tabs': (GafferUI.NodeGraph( scriptNode ),), 'currentTab': 0}, {'tabs': (GafferUI.Timeline( scriptNode ),), 'currentTab': 0} ) ) ) ), ( GafferUI.SplitContainer.Orientation.Horizontal, 0.494647, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.651345, ( {'tabs': (GafferUI.NodeEditor( scriptNode ),), 'currentTab': 0}, {'tabs': (GafferSceneUI.SceneInspector( scriptNode ),), 'currentTab': 0} ) ), {'tabs': (GafferSceneUI.SceneHierarchy( scriptNode ),), 'currentTab': 0} ) ) ) ) )" )
scriptWindow.setLayout( layout )
scriptWindow._Widget__qtWidget.resize(1869,923)
for nodeName in ['Group5']:
	script.selection().add( script.descendant( nodeName ) )
script.context()["ui:scene:expandedPaths"] = GafferScene.PathMatcherData( GafferScene.PathMatcher( ['/', '/group', '/group/group', '/group/group/plane', '/group/group/sphere', '/group/group1', '/group/group1/group', '/group/group1/group/plane', '/group/group1/group/sphere', '/group/group1/group1', '/group/group1/group1/group', '/group/group1/group1/text', '/group/group2', '/group/group2/group'] ) )
script.context()["ui:scene:selectedPaths"] = IECore.StringVectorData( [ "/group/group1/group1/text" ] )
##############################################################
## IMAGE SPECIFIC COMMANDS BELOW #############################
