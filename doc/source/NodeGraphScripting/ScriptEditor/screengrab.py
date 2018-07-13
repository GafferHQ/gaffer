# BuildTarget: images/scriptEditorBlank.png

import IECore

import Gaffer

import GafferUI

mainWindow = GafferUI.ScriptWindow.acquire( script )
scriptEditor = mainWindow.getLayout().editors( GafferUI.ScriptEditor )[0]

# Empty Script Editor
scriptEditor.reveal()
GafferUI.WidgetAlgo.grab( widget = scriptEditor.parent(), imagePath = "images/scriptEditorBlank.png" )

# Script Editor with error
scriptEditor.inputWidget().setText( "This will be an error." )
scriptEditor.execute()
GafferUI.WidgetAlgo.grab( widget = scriptEditor.parent(), imagePath = "images/scriptEditorError.png" )
