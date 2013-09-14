import IECore
import GafferUI
import GafferScene
import GafferSceneUI
import os
scriptNode = script
scriptWindow = GafferUI.ScriptWindow.acquire( script )
layout = eval( "GafferUI.CompoundEditor( scriptNode, children = {'tabs': (GafferUI.NodeGraph( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [None]} )" )
scriptWindow.setLayout( layout )
scriptWindow._Widget__qtWidget.resize(450,250)
for nodeName in ['Plane']:
	script.selection().add( script.descendant( nodeName ) )
script.context()["ui:scene:selectedPaths"] = IECore.StringVectorData( [  ] )
##############################################################
## IMAGE SPECIFIC COMMANDS BELOW #############################
