# BuildTarget: images/interfacePythonEditorOutput.png
# BuildTarget: images/interfacePythonEditorError.png

import IECore

import Gaffer
import GafferUI

mainWindow = GafferUI.ScriptWindow.acquire( script )
pythonEditor = mainWindow.getLayout().editors( GafferUI.ScriptEditor )[0]

# Interface: Python Editor with output
pythonEditor.reveal()
pythonEditor.inputWidget().setText( 'print( "Hello, world!" )' )
pythonEditor.execute()
pythonEditor.inputWidget().setText( 'print( "Hello, world!" )' )
GafferUI.WidgetAlgo.grab( widget = pythonEditor.parent(), imagePath = "images/interfacePythonEditorOutput.png" )

# Interface: Python Editor with error
pythonEditor.inputWidget().setText( "This will be an error." )
pythonEditor.execute()
GafferUI.WidgetAlgo.grab( widget = pythonEditor.parent(), imagePath = "images/interfacePythonEditorError.png" )
