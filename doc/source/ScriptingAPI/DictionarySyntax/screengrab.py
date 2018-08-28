# BuildTarget: images/graphEditorSample.png

import IECore

import Gaffer
import GafferScene

import GafferUI
import GafferSceneUI

scriptWindow = GafferUI.ScriptWindow.acquire( script )
viewer = scriptWindow.getLayout().editors( GafferUI.Viewer )[0]
graphEditor = scriptWindow.getLayout().editors( GafferUI.NodeGraph )[0]
hierarchyView = scriptWindow.getLayout().editors( GafferSceneUI.SceneHierarchy )[0]


readerNode = GafferScene.SceneReader()
script.addChild( readerNode )
assignmentNode = GafferScene.ShaderAssignment()
script.addChild( assignmentNode )
assignmentNode["in"].setInput( readerNode["out"] )
groupNode = GafferScene.Group()
script.addChild( groupNode )
groupNode["in"][0].setInput( assignmentNode["out"] )

GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorSample.png" )

del readerNode
del assignmentNode
del groupNode
