# BuildTarget: images/groupFirst.png

import os

import Gaffer
import GafferScene

import GafferUI

scriptWindow = GafferUI.ScriptWindow.acquire( script )

script["fileName"].setValue( os.path.abspath( "scripts/groupFirst.gfr" ) )
script.load()
graph = scriptWindow.getLayout().editors( GafferUI.GraphEditor )[0]
graph.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graph, imagePath = "images/groupFirst.png" )

script["fileName"].setValue( os.path.abspath( "scripts/groupSecond.gfr" ) )
script.load()
graph.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graph, imagePath = "images/groupSecond.png" )

script["StandardOptions"] = GafferScene.StandardOptions( "StandardOptions" )
script["StandardOptions"]["options"]["performanceMonitor"]["value"].setValue( True )
script["StandardOptions"]["options"]["performanceMonitor"]["enabled"].setValue( True )
editor = GafferUI.NodeEditor.acquire( script["StandardOptions"], floating=True )
GafferUI.PlugValueWidget.acquire( script["StandardOptions"]["options"]["performanceMonitor"] )
GafferUI.WidgetAlgo.grab( widget = editor, imagePath = "images/performanceMonitor.png" )
