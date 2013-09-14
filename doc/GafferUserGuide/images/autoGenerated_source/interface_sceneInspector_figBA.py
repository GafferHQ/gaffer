import IECore
import GafferUI
import GafferScene
import os
scriptNode = script
scriptWindow = GafferUI.ScriptWindow.acquire( script )
layout = eval( "GafferUI.CompoundEditor( scriptNode, children = {'tabs': (GafferUI.Viewer( scriptNode ),), 'currentTab': 0} )" )
scriptWindow.setLayout( layout )
scriptWindow._Widget__qtWidget.resize(845,550)
for nodeName in ['Display']:
	script.selection().add( script.descendant( nodeName ) )
##############################################################
## IMAGE SPECIFIC COMMANDS BELOW #############################
# do a render
script['RenderManRender'].execute( [script.context()] )