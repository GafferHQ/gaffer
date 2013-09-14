import IECore
import GafferUI
import GafferScene
import GafferSceneUI
import os
scriptNode = script
scriptWindow = GafferUI.ScriptWindow.acquire( script )
layout = eval( "GafferUI.CompoundEditor( scriptNode, children = ( GafferUI.SplitContainer.Orientation.Horizontal, 0.495974, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.529083, ( {'tabs': (GafferUI.Viewer( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False]}, ( GafferUI.SplitContainer.Orientation.Vertical, 0.918072, ( {'tabs': (GafferUI.NodeGraph( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [None]}, {'tabs': (GafferUI.Timeline( scriptNode ),), 'tabsVisible': False, 'currentTab': 0, 'pinned': [None]} ) ) ) ), ( GafferUI.SplitContainer.Orientation.Horizontal, 0.494105, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.651007, ( {'tabs': (GafferUI.NodeEditor( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False]}, {'tabs': (GafferSceneUI.SceneInspector( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False]} ) ), {'tabs': (GafferSceneUI.SceneHierarchy( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False]} ) ) ) ) )" )
scriptWindow.setLayout( layout )
scriptWindow._Widget__qtWidget.resize(995,500)
for nodeName in ['Group5']:
	script.selection().add( script.descendant( nodeName ) )
script.context()["ui:scene:expandedPaths"] = GafferScene.PathMatcherData( GafferScene.PathMatcher( ['/', '/group', '/group/group', '/group/group/plane', '/group/group/sphere', '/group/group1', '/group/group1/group', '/group/group1/group/plane', '/group/group1/group/sphere', '/group/group1/group1', '/group/group1/group1/group', '/group/group1/group1/text', '/group/group2', '/group/group2/group', '/group/group2/group/plane', '/group/group2/group/sphere'] ) )
script.context()["ui:scene:selectedPaths"] = IECore.StringVectorData( [ "/group/group2/group/sphere" ] )
##############################################################
## IMAGE SPECIFIC COMMANDS BELOW #############################
