import IECore
import GafferUI
import GafferScene
import GafferSceneUI
import os
scriptNode = script
scriptWindow = GafferUI.ScriptWindow.acquire( script )
layout = eval( "GafferUI.CompoundEditor( scriptNode, children = ( GafferUI.SplitContainer.Orientation.Vertical, 0.955145, ( ( GafferUI.SplitContainer.Orientation.Horizontal, 0.55, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.5, ( {'tabs': (GafferUI.Viewer( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [True]}, {'tabs': (GafferUI.NodeGraph( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [None]} ) ), ( GafferUI.SplitContainer.Orientation.Vertical, 0.538997, ( {'tabs': (GafferUI.NodeEditor( scriptNode ), GafferSceneUI.SceneInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False, False]}, {'tabs': (GafferSceneUI.SceneHierarchy( scriptNode ), GafferUI.ScriptEditor( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False, None]} ) ) ) ), {'tabs': (GafferUI.Timeline( scriptNode ),), 'tabsVisible': False, 'currentTab': 0, 'pinned': [None]} ) ) )" )
scriptWindow.setLayout( layout )
scriptWindow._Widget__qtWidget.resize(900,800)
for nodeName in ['demoLight']:
	script.selection().add( script.descendant( nodeName ) )
script.context()["ui:scene:expandedPaths"] = GafferScene.PathMatcherData( GafferScene.PathMatcher( ['/'] ) )
script.context()["ui:scene:selectedPaths"] = IECore.StringVectorData( [  ] )
##############################################################
## IMAGE SPECIFIC COMMANDS BELOW #############################

# add little nugget to load the AimConstraint node into the pinned editor
v = scriptWindow.getLayout().editors(GafferUI.Viewer)[0]
v.getNodeSet().add(script['Display'])

# do a render
script['RenderManRender'].execute( [script.context()] )