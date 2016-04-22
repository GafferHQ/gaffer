import IECore
import GafferUI
import GafferScene
import GafferSceneUI
import os

for nodeName in ['CustomAttributes']:
	script.selection().add( script.descendant( nodeName ) )
script.context()["ui:scene:expandedPaths"] = GafferScene.PathMatcherData( GafferScene.PathMatcher( ['/', '/group', '/group/ballA', '/group/ballB', '/group/camera', '/group/light'] ) )
script.context()["ui:scene:selectedPaths"] = IECore.StringVectorData( [ "/group/ballA" ] )

scriptNode = script
scriptWindow = GafferUI.ScriptWindow.acquire( script )
layout = eval( "GafferUI.CompoundEditor( scriptNode, children = ( GafferUI.SplitContainer.Orientation.Horizontal, 0.65, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.500816, ( {'tabs': (GafferUI.Viewer( scriptNode ),), 'currentTab': 0}, {'tabs': (GafferUI.NodeGraph( scriptNode ),), 'currentTab': 0} ) ), {'tabs': (GafferSceneUI.SceneInspector( scriptNode ),), 'currentTab': 0} ) ) )" )
scriptWindow.setLayout( layout )
scriptWindow._Widget__qtWidget.resize(845,645)

##############################################################
## IMAGE SPECIFIC COMMANDS BELOW #############################
