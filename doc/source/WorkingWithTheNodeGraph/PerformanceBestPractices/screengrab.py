# BuildTarget: images/graphEditorGroupFirst.png

import os

import Gaffer
import GafferScene

import GafferUI

scriptWindow = GafferUI.ScriptWindow.acquire( script )
graphEditor = scriptWindow.getLayout().editors( GafferUI.GraphEditor )[0]

# First sample node graph in Graph Editor
script["fileName"].setValue( os.path.abspath( "scripts/groupFirst.gfr" ) )
script.load()
graphEditor.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorGroupFirst.png" )

# Second sample node graph in Graph Editor
script["fileName"].setValue( os.path.abspath( "scripts/groupSecond.gfr" ) )
script.load()
graphEditor.frame( script.children( Gaffer.Node ) )
GafferUI.WidgetAlgo.grab( widget = graphEditor, imagePath = "images/graphEditorGroupSecond.png" )
