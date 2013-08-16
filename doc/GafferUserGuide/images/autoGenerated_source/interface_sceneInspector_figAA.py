import IECore
import GafferUI
import GafferScene
import os
scriptNode = script
scriptWindow = GafferUI.ScriptWindow.acquire( script )
layout = eval( "GafferUI.CompoundEditor( scriptNode, children = ( GafferUI.SplitContainer.Orientation.Vertical, 0.380375, ( {'tabs': (GafferUI.Viewer( scriptNode ),), 'currentTab': 0}, {'tabs': (GafferUI.NodeGraph( scriptNode ),), 'currentTab': 0} ) ) )" )
scriptWindow.setLayout( layout )
scriptWindow._Widget__qtWidget.resize(937,938)
for nodeName in ['Group']:
	script.selection().add( script.descendant( nodeName ) )
script.context()["ui:scene:expandedPaths"] = GafferScene.PathMatcherData( GafferScene.PathMatcher( ['/', '/group', '/group/ballA', '/group/ballB', '/group/camera', '/group/light'] ) )
script.context()["ui:scene:selectedPaths"] = IECore.StringVectorData( [ "/group/ballB" ] )
##############################################################
## IMAGE SPECIFIC COMMANDS BELOW #############################
