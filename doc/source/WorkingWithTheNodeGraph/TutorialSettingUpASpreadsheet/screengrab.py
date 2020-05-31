# BuildTarget: images/tutorialSettingUpASpreadsheetRow2Other.png images/tutorialSettingUpASpreadsheetRows2A2B.png images/tutorialSettingUpASpreadsheetOverscanValues.png images/tutorialSettingUpASpreadsheetFullName.png images/tutorialSettingUpASpreadsheetRow2.png images/tutorialSettingUpASpreadsheetCleanColumn.png images/tutorialSettingUpASpreadsheetDefaultCell.png images/tutorialSettingUpASpreadsheetRow1.png images/tutorialSettingUpASpreadsheetSelector.png images/tutorialSettingUpASpreadsheetNewSpreadsheet.png images/tutorialSettingUpASpreadsheetGlobalContextVariables.png images/tutorialSettingUpASpreadsheetAppleseedOptionsNode.png images/tutorialSettingUpASpreadsheetStandardOptionsNode.png

import os
import time

import imath
import IECore
import Gaffer
import GafferScene
import GafferUI
import GafferSceneUI

# Delay for x seconds
def __delay( delay ) :
	endtime = time.time() + delay
	while time.time() < endtime :
		GafferUI.EventLoop.waitForIdle( 1 )

# Default layout's editors
mainWindow = GafferUI.ScriptWindow.acquire( script )
viewer = mainWindow.getLayout().editors( GafferUI.Viewer )[0]
graphEditor = mainWindow.getLayout().editors( GafferUI.GraphEditor )[0]
nodeEditor = mainWindow.getLayout().editors( GafferUI.NodeEditor )[0]
sceneInspector = mainWindow.getLayout().editors( GafferSceneUI.SceneInspector )[0]
hierarchyView = mainWindow.getLayout().editors( GafferSceneUI.HierarchyView )[0]
pythonEditor = mainWindow.getLayout().editors( GafferUI.PythonEditor )[0]

# For simplicity, the screengrabs are generated in reverse order
script["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/resources/examples/rendering/multiShotRenderSpreadsheet.gfr" ) )
script.load()
script.removeChild( script["Backdrop"] )
script.removeChild( script["Backdrop1"] )
script.removeChild( script["Backdrop2"] )
sheet = script["Spreadsheet_RenderOptions"]
defaultRow = sheet["rows"]["default"]
row1 = sheet["rows"]["row1"]
row2A = sheet["rows"]["row2"]
row2B = sheet["rows"]["row3"]
row2Other = sheet["rows"]["row4"]

# Tutorial: Finished spreadsheet
nodeEditorWindow = GafferUI.NodeEditor.acquire( sheet, floating = True )
nodeEditorWindow._qtWidget().setFocus()
nodeEditorWindow.parent()._qtWidget().resize( 696, 325 )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/tutorialSettingUpASpreadsheetRow2Other.png" )

# Tutorial: Rows A and 2B
sheet["rows"].removeChild( row2Other )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/tutorialSettingUpASpreadsheetRows2A2B.png" )

# Tutorial: Overscan values
sheet["rows"].removeChild( row2B )
row2 = row2A
row2["name"].setValue( "2" )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/tutorialSettingUpASpreadsheetOverscanValues.png" )

# Tutorial: Spreadsheet name in Graph Editor
nodeEditorWindow.parent()._qtWidget().hide()
with GafferUI.Window() as window :
	graphEditorWindow = GafferUI.GraphEditor( script )
graphEditorWindow.parent().reveal()
graphEditorWindow.parent()._qtWidget().resize( 300, 200 )
__delay( 0.1 )
graphEditorWindow.frame( Gaffer.StandardSet( [ sheet ] ) )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = graphEditorWindow, imagePath = "images/tutorialSettingUpASpreadsheetFullName.png" )
graphEditorWindow.parent().close()
del graphEditorWindow

# Tutorial: Row 2
nodeEditorWindow.parent()._qtWidget().show()
__delay( 0.1 )
sheet["rows"].removeColumn( 5 )
sheet["rows"].removeColumn( 4 )
sheet["rows"].removeColumn( 3 )
sheet["rows"].removeColumn( 2 )
sheet["rows"].removeColumn( 1 )
row2["name"].setValue( "2" )
row2["cells"]["maxAASamples"].enabledPlug().setValue( True )
row2["cells"]["maxAASamples"]["value"]["value"].setValue( 36 )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/tutorialSettingUpASpreadsheetRow2.png" )

# Tutorial: Clean column
sheet["rows"].removeRow( row2 )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/tutorialSettingUpASpreadsheetCleanColumn.png" )

# Tutorial: Default cell
Gaffer.Metadata.registerValue( defaultRow["cells"]["maxAASamples"], 'spreadsheet:columnWidth', 100 )
Gaffer.Metadata.registerValue( defaultRow["cells"]["maxAASamples"], 'spreadsheet:columnLabel', 'Max AA Samples' )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/tutorialSettingUpASpreadsheetDefaultCell.png" )

# Tutorial: Filled row 1
defaultRow["cells"]["maxAASamples"].enabledPlug().setValue( False )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/tutorialSettingUpASpreadsheetRow1.png" )

# Tutorial: Selector plug
row1["name"].setValue( "" )
row1["cells"]["maxAASamples"]["value"]["value"].setValue( 32 )
row1["cells"]["maxAASamples"].enabledPlug().setValue( False )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/tutorialSettingUpASpreadsheetSelector.png" )

# Tutorial: New spreadsheet
sheet["selector"].setValue( "" )
script.selection().add( Gaffer.StandardSet( [ script["AppleseedOptions"] ] ) )
GafferUI.PlugValueWidget.acquire( script["AppleseedOptions"]["options"]["maxAASamples"] )
pos = nodeEditorWindow.parent()._qtWidget().pos()
pos.setX( pos.x() - 150 )
nodeEditorWindow.parent()._qtWidget().move( pos )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = mainWindow, imagePath = "images/tutorialSettingUpASpreadsheetNewSpreadsheet.png" )
script.selection().clear()

# Tutorial: Global Context Variables
nodeEditorWindow.parent().close()
del nodeEditorWindow
script.removeChild( sheet )
del sheet
GafferUI.FileMenu.showSettings( mainWindow.getLayout() )
settingsWindow = mainWindow.childWindows()[0]
settingsWindow.getChild().plugValueWidget( script["variables"] ).reveal()
settingsWindow.setVisible( True )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = settingsWindow, imagePath = "images/tutorialSettingUpASpreadsheetGlobalContextVariables.png" )
settingsWindow.close()
del settingsWindow

# Tutorial: AppleseedOptions node
with GafferUI.Window() as window :
	graphEditorWindow = GafferUI.GraphEditor( script )
graphEditorWindow.parent().reveal()
graphEditorWindow.parent()._qtWidget().resize( 300, 200 )
__delay( 0.1 )
graphEditorWindow.frame( script.children( Gaffer.Node ) )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = graphEditorWindow, imagePath = "images/tutorialSettingUpASpreadsheetAppleseedOptionsNode.png" )

# Tutorial: StandardOptions node
script.removeChild( script["AppleseedOptions"] )
graphEditorWindow.frame( script.children( Gaffer.Node ) )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = graphEditorWindow, imagePath = "images/tutorialSettingUpASpreadsheetStandardOptionsNode.png" )
