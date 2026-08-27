# BuildTarget: images/nodeEditorWindowPerformanceMonitor.png

import Gaffer
import GafferScene

import GafferUI

scriptWindow = GafferUI.ScriptWindow.acquire( script )

# StandardOptions in Node Editor window
script["StandardOptions"] = GafferScene.StandardOptions( "StandardOptions" )
optionsNode = script["StandardOptions"]
optionsNode["options"]["render:performanceMonitor"]["value"].setValue( True )
optionsNode["options"]["render:performanceMonitor"]["enabled"].setValue( True )
nodeEditorWindow = GafferUI.NodeEditor.acquire( optionsNode, floating=True )
GafferUI.PlugValueWidget.acquire( optionsNode["options"]["render:performanceMonitor"] )
nodeEditorWindow._qtWidget().setFocus()
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/nodeEditorWindowPerformanceMonitor.png" )
