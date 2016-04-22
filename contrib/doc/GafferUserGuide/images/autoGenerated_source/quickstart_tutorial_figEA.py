import IECore
import GafferUI
import GafferScene
import GafferSceneUI
import os
scriptNode = script
scriptWindow = GafferUI.ScriptWindow.acquire( script )
scriptWindow._Widget__qtWidget.resize(900,720)
for nodeName in ['Group']:
	script.selection().add( script.descendant( nodeName ) )
script.context()["ui:scene:expandedPaths"] = GafferScene.PathMatcherData( GafferScene.PathMatcher( ['/'] ) )
script.context()["ui:scene:selectedPaths"] = IECore.StringVectorData( [  ] )
##############################################################
## IMAGE SPECIFIC COMMANDS BELOW #############################
