import IECore
import GafferUI
import GafferScene
import GafferSceneUI
import os
scriptNode = script
scriptWindow = GafferUI.ScriptWindow.acquire( script )
layout = eval( "GafferUI.CompoundEditor( scriptNode, children = ( GafferUI.SplitContainer.Orientation.Vertical, 0.958937, ( ( GafferUI.SplitContainer.Orientation.Horizontal, 0.699719, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.479695, ( {'tabs': (GafferUI.Viewer( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [True]}, {'tabs': (GafferUI.NodeGraph( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [None]} ) ), ( GafferUI.SplitContainer.Orientation.Vertical, 0.539340, ( {'tabs': (GafferUI.NodeEditor( scriptNode ), GafferSceneUI.SceneInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False, False]}, {'tabs': (GafferSceneUI.SceneHierarchy( scriptNode ), GafferUI.ScriptEditor( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False, None]} ) ) ) ), {'tabs': (GafferUI.Timeline( scriptNode ),), 'tabsVisible': False, 'currentTab': 0, 'pinned': [None]} ) ) )" )
scriptWindow.setLayout( layout )
scriptWindow._Widget__qtWidget.resize(900,720)
for nodeName in ['Camera']:
	script.selection().add( script.descendant( nodeName ) )
script.context()["ui:scene:expandedPaths"] = GafferScene.PathMatcherData( GafferScene.PathMatcher( ['/', '/rootGroup', '/rootGroup/camera', '/rootGroup/geoGroup'] ) )
script.context()["ui:scene:selectedPaths"] = IECore.StringVectorData( [ "/camera" ] )
##############################################################
## IMAGE SPECIFIC COMMANDS BELOW #############################

# add little nugget to load the AimConstraint node into the pinned editor
v = scriptWindow.getLayout().editors(GafferUI.Viewer)[0]
v.getNodeSet().add(script['AimConstraint'])
