import IECore
import GafferUI
import GafferScene
import GafferSceneUI
import os
scriptNode = script
scriptWindow = GafferUI.ScriptWindow.acquire( script )
layout = eval( "GafferUI.CompoundEditor( scriptNode, children = ( GafferUI.SplitContainer.Orientation.Vertical, 0.972603, ( ( GafferUI.SplitContainer.Orientation.Horizontal, 0.586498, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.477541, ( {'tabs': (GafferUI.Viewer( scriptNode ),), 'tabsVisible': True, 'currentTab': 0}, {'tabs': (GafferUI.NodeGraph( scriptNode ),), 'tabsVisible': True, 'currentTab': 0} ) ), ( GafferUI.SplitContainer.Orientation.Vertical, 0.543735, ( {'tabs': (GafferUI.NodeEditor( scriptNode ), GafferSceneUI.SceneInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0}, {'tabs': (GafferSceneUI.SceneHierarchy( scriptNode ), GafferUI.ScriptEditor( scriptNode )), 'tabsVisible': True, 'currentTab': 0} ) ) ) ), {'tabs': (GafferUI.Timeline( scriptNode ),), 'tabsVisible': False, 'currentTab': 0} ) ) )" )
scriptWindow.setLayout( layout )
scriptWindow._Widget__qtWidget.resize(900,720)
for nodeName in ['Group']:
	script.selection().add( script.descendant( nodeName ) )
script.context()["ui:scene:selectedPaths"] = IECore.StringVectorData( [ "/geoGroup/sphereA" ] )
script.context()["ui:scene:expandedPaths"] = GafferScene.PathMatcherData( GafferScene.PathMatcher( ['/', '/geoGroup', '/geoGroup/sphereA'] ) )

##############################################################
## IMAGE SPECIFIC COMMANDS BELOW #############################
