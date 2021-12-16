# BuildTarget: images/exampleMultiShotRenderSpreadsheet.png
# BuildTarget: images/examplePerLocationLightTweakSpreadsheet.png
# BuildTarget: images/examplePerLocationTransformSpreadsheet.png
# BuildTarget: images/interfaceSpreadsheetNode.png
# BuildTarget: images/interfaceSpreadsheetNodeAuxiliaryConnections.png
# BuildTarget: images/interfaceSpreadsheetNodeBreakdown.png
# BuildTarget: images/interfaceSpreadsheetNodeColumnSections.png
# BuildTarget: images/interfaceSpreadsheetNodeCompoundEnabledSwitch.png
# BuildTarget: images/interfaceSpreadsheetNodeDisabledCell.png
# BuildTarget: images/interfaceSpreadsheetNodeFullName.png
# BuildTarget: images/interfaceSpreadsheetNodeInterface.png
# BuildTarget: images/interfaceSpreadsheetNodePatternWidths.png
# BuildTarget: images/interfaceSpreadsheetNodeRenderNetwork.png
# BuildTarget: images/taskSpreadsheetNodeAddPlugBasic.png
# BuildTarget: images/taskSpreadsheetNodeAddPlugCompound.png
# BuildTarget: images/taskSpreadsheetNodeAddPlugTweak.png
# BuildTarget: images/taskSpreadsheetNodeAddPlugVectorSingle.png
# BuildTarget: images/taskSpreadsheetNodeAddPlugVectorWhole.png
# BuildTarget: images/taskSpreadsheetNodeReorderColumn.png
# BuildTarget: images/taskSpreadsheetNodeReorderSection.png
# BuildTarget: images/taskSpreadsheetNodeResizeColumnAutomatic.png
# BuildTarget: images/taskSpreadsheetNodeResizeColumnManual.png

import sys
import os
import subprocess32 as subprocess
import tempfile
import time

import six

import Qt
from Qt import QtCore, QtWidgets

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

# Create a random directory in `/tmp` for the dispatcher's `jobsDirectory`, so we don't clutter the user's `~gaffer` directory
temporaryDirectory = tempfile.mkdtemp( prefix = "gafferDocs" )

def __getTempFilePath( fileName, directory = temporaryDirectory ) :
	filePath = "/".join( ( directory, fileName ) )

	return filePath

def __dispatchScript( script, tasks, settings ) :
	command = "gaffer dispatch -script {} -tasks {} -dispatcher Local -settings {} -dispatcher.jobsDirectory '\"{}/dispatcher/local\"'".format(
		script,
		" ".join( tasks ),
		" ".join( settings ),
		temporaryDirectory
		)
	subprocess.check_call( command, shell = True )

# Create a plug context menu from a Node Editor
def __spawnPlugContextMenu( nodeEditor, plugWidget ) :
	plugWidget._PlugValueWidget__contextMenu()
	plugWidget._PlugValueWidget__popupMenu.setVisible( False )
	contextMenuWidget = plugWidget._PlugValueWidget__popupMenu._qtWidget()
	contextMenuWidget.popup(
			QtCore.QPoint(
				mainWindow._qtWidget().geometry().x(),
				mainWindow._qtWidget().geometry().y()
			)
		)

	return contextMenuWidget

# Find a target action in a plug context menu and highlight it
def __selectPlugContextMenuAction( contextMenuWidget, targetActionName ) :
	actions = contextMenuWidget.actions()
	targetActionName = targetActionName
	targetAction = None
	for action in actions :
		text = action.text()
		if text == targetActionName :
			targetAction = action
	contextMenuWidget.setActiveAction( targetAction )
	__delay(0.1)
	actionWidget = targetAction.parent()

	return actionWidget

# Screengrab a plug context menu and submenu
def __grabPlugContextSubmenu( plugWidget, contextMenuWidget, submenuWidget, menuPath, submenuPath ) :
	screen = QtWidgets.QApplication.primaryScreen()
	windowHandle = plugWidget._qtWidget().windowHandle()
	if windowHandle :
		screen = windowHandle.screen()

	qtVersion = [ int( x ) for x in Qt.__qt_version__.split( "." ) ]
	if qtVersion >= [ 5, 12 ] or six.PY3 :
		pixmapMain = screen.grabWindow( mainWindow._qtWidget().winId() )
	else :
		pixmapMain = screen.grabWindow( long( mainWindow._qtWidget().winId() ) )

	## Screengrab the context menu. The frame dimensions are too big by
	# one pixel on each axis.
	menuScreenPos = QtCore.QPoint( 0, 0 )
	if sys.platform == "darwin" :
		menuScreenPos = QtCore.QPoint(
			mainWindow._qtWidget().geometry().x(),
			mainWindow._qtWidget().geometry().y()
		)
	menuSize = QtCore.QSize(
		contextMenuWidget.frameGeometry().width() - 1,
		contextMenuWidget.frameGeometry().height() - 1
		)
	menuRect = QtCore.QRect( menuScreenPos, menuSize )
	pixmap = pixmapMain.copy( menuRect )
	pixmap.save( menuPath )

	## Screengrab the sub-menu
	submenuScreenPos = submenuWidget.pos()
	if sys.platform != "darwin" :
		submenuScreenPos = submenuScreenPos - contextMenuWidget.pos()
	submenuSize = QtCore.QSize(
		submenuWidget.frameGeometry().width() - 1,
		submenuWidget.frameGeometry().height() - 1
		)
	submenuRect = QtCore.QRect( submenuScreenPos, submenuSize )

	pixmap = pixmapMain.copy( submenuRect )
	pixmap.save( submenuPath )

# Default layout's editors
mainWindow = GafferUI.ScriptWindow.acquire( script )
viewer = mainWindow.getLayout().editors( GafferUI.Viewer )[0]
graphEditor = mainWindow.getLayout().editors( GafferUI.GraphEditor )[0]
nodeEditor = mainWindow.getLayout().editors( GafferUI.NodeEditor )[0]
sceneInspector = mainWindow.getLayout().editors( GafferSceneUI.SceneInspector )[0]
hierarchyView = mainWindow.getLayout().editors( GafferSceneUI.HierarchyView )[0]
pythonEditor = mainWindow.getLayout().editors( GafferUI.PythonEditor )[0]

# Interface: A Spreadsheet node in the Graph Editor
imageName = "interfaceSpreadsheetNode"
imagePath = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
script["Spreadsheet"] = Gaffer.Spreadsheet()
with GafferUI.Window() as window :
	graphEditorWindow = GafferUI.GraphEditor( script )
graphEditorWindow.parent().reveal()
graphEditorWindow.parent()._qtWidget().resize( 400, 100 )
__delay( 0.1 )
graphEditorWindow.frame( Gaffer.StandardSet( [ script["Spreadsheet"] ] ) )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = graphEditorWindow, imagePath = imagePath )
graphEditorWindow.parent().close()
del graphEditorWindow

# Interface: Spreadsheet node with full name in Graph Editor
imageName = "interfaceSpreadsheetNodeFullName"
imagePath = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
Gaffer.Metadata.registerValue( script["Spreadsheet"], 'nodeGadget:type', 'GafferUI::StandardNodeGadget' )
with GafferUI.Window() as window :
	graphEditorWindow = GafferUI.GraphEditor( script )
graphEditorWindow.parent().reveal()
graphEditorWindow.parent()._qtWidget().resize( 300, 100 )
__delay( 0.1 )
graphEditorWindow.frame( Gaffer.StandardSet( [ script["Spreadsheet"] ] ) )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = graphEditorWindow, imagePath = imagePath )
graphEditorWindow.parent().close()
del graphEditorWindow

# Interface: The Spreadsheet node's interface in a Node Editor
imageName = "interfaceSpreadsheetNodeInterface"
imagePathInterface = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
script["fileName"].setValue( os.path.abspath( "scripts/{scriptName}.gfr".format( scriptName = imageName ) ) )
script.load()
__delay( 0.1 )
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["Spreadsheet"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = imagePathInterface )
nodeEditorWindow.parent().close()
del nodeEditorWindow

# Interface: Render options network before and after Spreadsheet node
imageName = "interfaceSpreadsheetNodeRenderNetwork"
tempImagePath1 = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Before" ) )
tempImagePath2 = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "After" ) )
imagePath = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
script["fileName"].setValue( os.path.abspath( "scripts/{scriptName}.gfr".format( scriptName = imageName ) ) )
script.load()
__delay( 0.1 )
with GafferUI.Window() as window :
	graphEditorWindow = GafferUI.GraphEditor( script )
#graphEditorWindow.parent()._qtWidget().setWindowFlags( QtCore.Qt.WindowFlags( QtCore.Qt.WindowStaysOnTopHint ) )
graphEditorWindow.parent().reveal()
graphEditorWindow.parent()._qtWidget().resize( 800, 400 )
__delay( 0.1 )
graphEditorWindow.frame( Gaffer.StandardSet( [ script["Backdrop_OptionsBefore"] ] ) )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = graphEditorWindow, imagePath = tempImagePath1 )
graphEditorWindow.frame( Gaffer.StandardSet( [ script["Backdrop_OptionsAfter"] ] ) )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = graphEditorWindow, imagePath = tempImagePath2 )
__dispatchScript(
	script = "scripts/{scriptName}_edit.gfr".format( scriptName = imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader_Before.fileName '\"{tempPath}\"'".format( tempPath = tempImagePath1 ),
		"-ImageReader_After.fileName '\"{tempPath}\"'".format( tempPath = tempImagePath2 ),
		"-ImageWriter.fileName '\"{imagePath}\"'".format( imagePath = imagePath )
		]
	)

# Interface: Breakdown of the Spreadsheet node's interface in a Node Editor
imageName = "interfaceSpreadsheetNodeBreakdown"
tempImagePath = imagePathInterface
imagePath = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
__dispatchScript(
	script = "scripts/{scriptName}_edit.gfr".format( scriptName = imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader.fileName '\"{imagePath}\"'".format( imagePath = tempImagePath ),
		"-ImageWriter.fileName '\"{imagePath}\"'".format( imagePath = imagePath )
		]
	)

# Interface: Spreadsheet node's auxiliary connections
imageName = "interfaceSpreadsheetNodeAuxiliaryConnections"
imagePath = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
script["fileName"].setValue( os.path.abspath( "scripts/{scriptName}.gfr".format( scriptName = imageName ) ) )
script.load()
__delay( 0.1 )
with GafferUI.Window() as window :
	graphEditorWindow = GafferUI.GraphEditor( script )
graphEditorWindow.parent().reveal()
graphEditorWindow.parent()._qtWidget().resize( 300, 200 )
__delay( 0.1 )
graphEditorWindow.frame( Gaffer.StandardSet( [ script["Dot"] ] ) )
script.removeChild( script["Dot"] )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = graphEditorWindow, imagePath = imagePath )
graphEditorWindow.parent().close()
del graphEditorWindow

# Task: Add a basic plug
imageName = "taskSpreadsheetNodeAddPlugBasic"
tempImagePathEditor = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Editor" ) )
tempImagePathMenu = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Menu" ) )
tempImagePathSubmenu = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Submenu" ) )
imagePath = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
script["Sphere"] = GafferScene.Sphere()
script["Spreadsheet"] = Gaffer.Spreadsheet()
# Screengrab the Node Editor
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["Sphere"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
plugWidget = GafferUI.PlugValueWidget.acquire( script["Sphere"]["radius"] )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = tempImagePathEditor )
# Spawn the context menu
contextMenuWidget = __spawnPlugContextMenu(
	nodeEditor = nodeEditorWindow,
	plugWidget = plugWidget
	)
# Find the target action in the menu and highlight it
actionWidget = __selectPlugContextMenuAction(
	contextMenuWidget = contextMenuWidget,
	targetActionName = "Add to Spreadsheet"
	)
# Screengrab the menu and submenu, get submenu position
submenuOrigin = __grabPlugContextSubmenu(
	plugWidget = plugWidget,
	contextMenuWidget = contextMenuWidget,
	submenuWidget = actionWidget,
	menuPath = tempImagePathMenu,
	submenuPath = tempImagePathSubmenu
	)
contextMenuWidget.close()
nodeEditorWindow.parent().close()
del nodeEditorWindow
__dispatchScript(
	script = "scripts/{scriptName}_edit.gfr".format( scriptName = imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader_Editor.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathEditor ),
		"-ImageReader_Menu.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathMenu ),
		"-ImageReader_Submenu.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathSubmenu ),
		"-ImageWriter.fileName '\"{imagePath}\"'".format( imagePath = imagePath )
		]
	)

# Task: Add a vector plug (whole)
imageName = "taskSpreadsheetNodeAddPlugVectorWhole"
tempImagePathEditor = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Editor" ) )
tempImagePathMenu = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Menu" ) )
tempImagePathSubmenu = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Submenu" ) )
imagePath = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
# Screengrab the Node Editor
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["Sphere"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
plugWidget = GafferUI.PlugValueWidget.acquire( script["Sphere"]["transform"]["rotate"] )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = tempImagePathEditor )
# Spawn the context menu
contextMenuWidget = __spawnPlugContextMenu(
	nodeEditor = nodeEditorWindow,
	plugWidget = plugWidget
	)
# Find the target action in the menu and highlight it
actionWidget = __selectPlugContextMenuAction(
	contextMenuWidget = contextMenuWidget,
	targetActionName = "Add to Spreadsheet"
	)
# Screengrab the menu and submenu, get submenu position
submenuOrigin = __grabPlugContextSubmenu(
	plugWidget = plugWidget,
	contextMenuWidget = contextMenuWidget,
	submenuWidget = actionWidget,
	menuPath = tempImagePathMenu,
	submenuPath = tempImagePathSubmenu
	)
contextMenuWidget.close()
nodeEditorWindow.parent().close()
del nodeEditorWindow
__dispatchScript(
	script = "scripts/{scriptName}_edit.gfr".format( scriptName = imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader_Editor.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathEditor ),
		"-ImageReader_Menu.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathMenu ),
		"-ImageReader_Submenu.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathSubmenu ),
		"-ImageWriter.fileName '\"{imagePath}\"'".format( imagePath = imagePath )
		]
	)

# Task: Add a vector plug (single element)
imageName = "taskSpreadsheetNodeAddPlugVectorSingle"
tempImagePathEditor = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Editor" ) )
tempImagePathMenu = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Menu" ) )
tempImagePathSubmenu = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Submenu" ) )
imagePath = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
# Screengrab the Node Editor
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["Sphere"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
plugWidget = GafferUI.PlugValueWidget.acquire( script["Sphere"]["transform"]["rotate"] )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = tempImagePathEditor )
# Spawn the context menu
contextMenuWidget = __spawnPlugContextMenu(
	nodeEditor = nodeEditorWindow,
	plugWidget = plugWidget
	)
# Find the target action in the menu and highlight it
actionWidget = __selectPlugContextMenuAction(
	contextMenuWidget = contextMenuWidget,
	targetActionName = "Add to Spreadsheet"
	)
# Screengrab the menu and submenu, get submenu position
submenuOrigin = __grabPlugContextSubmenu(
	plugWidget = plugWidget,
	contextMenuWidget = contextMenuWidget,
	submenuWidget = actionWidget,
	menuPath = tempImagePathMenu,
	submenuPath = tempImagePathSubmenu
	)
contextMenuWidget.close()
nodeEditorWindow.parent().close()
del nodeEditorWindow
__dispatchScript(
	script = "scripts/{scriptName}_edit.gfr".format( scriptName = imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader_Editor.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathEditor ),
		"-ImageReader_Menu.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathMenu ),
		"-ImageReader_Submenu.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathSubmenu ),
		"-ImageWriter.fileName '\"{imagePath}\"'".format( imagePath = imagePath )
		]
	)

# Task: Add a compound plug
imageName = "taskSpreadsheetNodeAddPlugCompound"
tempImagePathEditor = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Editor" ) )
tempImagePathMenu = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Menu" ) )
tempImagePathSubmenu = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Submenu" ) )
imagePath = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
# Screengrab the Node Editor
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["Sphere"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
plugWidget = GafferUI.PlugValueWidget.acquire( script["Sphere"]["transform"]["rotate"] )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = tempImagePathEditor )
# Spawn the context menu
contextMenuWidget = __spawnPlugContextMenu(
	nodeEditor = nodeEditorWindow,
	plugWidget = plugWidget
	)
# Find the target action in the menu and highlight it
actionWidget = __selectPlugContextMenuAction(
	contextMenuWidget = contextMenuWidget,
	targetActionName = "Add to Spreadsheet (Transform)"
	)
# Screengrab the menu and submenu, get submenu position
submenuOrigin = __grabPlugContextSubmenu(
	plugWidget = plugWidget,
	contextMenuWidget = contextMenuWidget,
	submenuWidget = actionWidget,
	menuPath = tempImagePathMenu,
	submenuPath = tempImagePathSubmenu
	)
contextMenuWidget.close()
nodeEditorWindow.parent().close()
del nodeEditorWindow
script.removeChild( script["Sphere"] )
__dispatchScript(
	script = "scripts/{scriptName}_edit.gfr".format( scriptName = imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader_Editor.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathEditor ),
		"-ImageReader_Menu.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathMenu ),
		"-ImageReader_Submenu.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathSubmenu ),
		"-ImageWriter.fileName '\"{imagePath}\"'".format( imagePath = imagePath )
		]
	)

# Interface: Compound plug with enabled switch
imageName = "interfaceSpreadsheetNodeCompoundEnabledSwitch"
tempImagePathSpreadsheet = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Spreadsheet" ) )
tempImagePathOptions = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Options" ) )
imagePath = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
script["fileName"].setValue( os.path.abspath( "scripts/{scriptName}.gfr".format( scriptName = imageName ) ) )
script.load()
# Screengrab the Node Editor (Spreadsheet node)
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["Spreadsheet"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = tempImagePathSpreadsheet )
nodeEditorWindow.parent().close()
del nodeEditorWindow
# Screengrab the Node Editor (StandardOptions node)
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["StandardOptions"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
GafferUI.PlugValueWidget.acquire( script["StandardOptions"]["options"]["renderCamera"] )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = tempImagePathOptions )
nodeEditorWindow.parent().close()
del nodeEditorWindow
__dispatchScript(
	script = "scripts/{scriptName}_edit.gfr".format( scriptName = imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader_Spreadsheet.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathSpreadsheet ),
		"-ImageReader_Options.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathOptions ),
		"-ImageWriter.fileName '\"{imagePath}\"'".format( imagePath = imagePath )
		]
	)

# Interface: Disabled cell
imageName = "interfaceSpreadsheetNodeDisabledCell"
tempImagePathEditor = tempImagePathSpreadsheet
imagePath = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
__dispatchScript(
	script = "scripts/{scriptName}_edit.gfr".format( scriptName = imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader_Editor.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathSpreadsheet ),
		"-ImageWriter.fileName '\"{imagePath}\"'".format( imagePath = imagePath )
		]
	)

# Task: Add a tweak plug
imageName = "taskSpreadsheetNodeAddPlugTweak"
tempImagePathEditor = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Editor" ) )
tempImagePathMenu = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Menu" ) )
tempImagePathSubmenu = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Submenu" ) )
imagePath = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
script["CameraTweaks"] = GafferScene.CameraTweaks()
script["CameraTweaks"]["tweaks"].addChild( GafferScene.TweakPlug( Gaffer.V2iPlug( "value", defaultValue = imath.V2i( 1920, 1050 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ), "resolution", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
script["CameraTweaks"]["tweaks"]["resolution"]["name"].setValue( 'resolution' )
# Screengrab the Node Editor
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["CameraTweaks"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = tempImagePathEditor )
# Spawn the context menu
plugWidget = GafferUI.PlugValueWidget.acquire( script["CameraTweaks"]["tweaks"]["resolution"]["value"] )
contextMenuWidget = __spawnPlugContextMenu(
	nodeEditor = nodeEditorWindow,
	plugWidget = plugWidget
	)
# Find the target action in the menu and highlight it
actionWidget = __selectPlugContextMenuAction(
	contextMenuWidget = contextMenuWidget,
	targetActionName = "Add to Spreadsheet (Tweak)"
	)
# Screengrab the menu and submenu, get submenu position
submenuOrigin = __grabPlugContextSubmenu(
	plugWidget = plugWidget,
	contextMenuWidget = contextMenuWidget,
	submenuWidget = actionWidget,
	menuPath = tempImagePathMenu,
	submenuPath = tempImagePathSubmenu
	)
contextMenuWidget.close()
nodeEditorWindow.parent().close()
del nodeEditorWindow
script.removeChild( script["CameraTweaks"] )
__dispatchScript(
	script = "scripts/{scriptName}_edit.gfr".format( scriptName = imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader_Editor.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathEditor ),
		"-ImageReader_Menu.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathMenu ),
		"-ImageReader_Submenu.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathSubmenu ),
		"-ImageWriter.fileName '\"{imagePath}\"'".format( imagePath = imagePath )
		]
	)

# Interface: Column sections in the Node Editor
imageName = "interfaceSpreadsheetNodeColumnSections"
tempImagePathColumns = __getTempFilePath( "{imageName}.png".format( imageName = imageName ) )
imagePath = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
script["fileName"].setValue( os.path.abspath( "scripts/{scriptName}.gfr".format( scriptName = imageName ) ) )
script.load()
__delay( 0.1 )
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["Spreadsheet"], floating = True )
nodeEditorWindow.parent()._qtWidget().resize( 600, 350 )
nodeEditorWindow._qtWidget().setFocus()
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = tempImagePathColumns )
nodeEditorWindow.parent().close()
del nodeEditorWindow
__dispatchScript(
	script = "scripts/{scriptName}_edit.gfr".format( scriptName = imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader_Editor.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathColumns ),
		"-ImageWriter.fileName '\"{imagePath}\"'".format( imagePath = imagePath )
		]
	)

# Task: Reordering a section
imageName = "taskSpreadsheetNodeReorderSection"
tempImagePath = tempImagePathColumns
imagePath = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
__dispatchScript(
	script = "scripts/{scriptName}_edit.gfr".format( scriptName = imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader_Editor.fileName '\"{imagePath}\"'".format( imagePath = tempImagePath ),
		"-ImageWriter.fileName '\"{imagePath}\"'".format( imagePath = imagePath )
		]
	)

# Task: Reordering a column
imageName = "taskSpreadsheetNodeReorderColumn"
tempImagePath = tempImagePathColumns
imagePath = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
__dispatchScript(
	script = "scripts/{scriptName}_edit.gfr".format( scriptName = imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader_Editor.fileName '\"{imagePath}\"'".format( imagePath = tempImagePath ),
		"-ImageWriter.fileName '\"{imagePath}\"'".format( imagePath = imagePath )
		]
	)

# Task: Automatically resizing a column
imageName = "taskSpreadsheetNodeResizeColumnAutomatic"
tempImagePath = tempImagePathColumns
imagePath = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
__dispatchScript(
	script = "scripts/{scriptName}_edit.gfr".format( scriptName = imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader_Editor.fileName '\"{imagePath}\"'".format( imagePath = tempImagePath ),
		"-ImageWriter.fileName '\"{imagePath}\"'".format( imagePath = imagePath )
		]
	)

# Task: Manually resizing a column
imageName = "taskSpreadsheetNodeResizeColumnManual"
tempImagePath = tempImagePathColumns
imagePath = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
__dispatchScript(
	script = "scripts/{scriptName}_edit.gfr".format( scriptName = imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader_Editor.fileName '\"{imagePath}\"'".format( imagePath = tempImagePath ),
		"-ImageWriter.fileName '\"{imagePath}\"'".format( imagePath = imagePath )
		]
	)

# Interface: Pattern widths
imageName = "interfaceSpreadsheetNodePatternWidths"
tempImagePathHalf = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Half" ) )
tempImagePathSingle = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Single" ) )
tempImagePathDouble = __getTempFilePath( "{tempName}.png".format( tempName = imageName + "Double" ) )
imagePath = os.path.abspath( "images/{imageName}.png".format( imageName = imageName ) )
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["Spreadsheet"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = tempImagePathSingle )
Gaffer.Metadata.registerValue( script["Spreadsheet"]["rows"][0], 'spreadsheet:rowNameWidth', 75.0 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = tempImagePathHalf )
Gaffer.Metadata.registerValue( script["Spreadsheet"]["rows"][0], 'spreadsheet:rowNameWidth', 300.0 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = tempImagePathDouble )
nodeEditorWindow.parent().close()
del nodeEditorWindow
__dispatchScript(
	script = "scripts/{scriptName}_edit.gfr".format( scriptName = imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader_Half.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathHalf ),
		"-ImageReader_Single.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathSingle ),
		"-ImageReader_Double.fileName '\"{imagePath}\"'".format( imagePath = tempImagePathDouble ),
		"-ImageWriter.fileName '\"{imagePath}\"'".format( imagePath = imagePath )
		]
	)

# Example: Per-location Transform Spreadsheet
exampleName = "PerLocationTransformSpreadsheet"
script["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/resources/examples/sceneProcessing/perLocationTransformSpreadsheet.gfr" ) )
script.load()
viewerWindow = GafferUI.Viewer.acquire( script["Transform"], floating = True )
viewerWindow._qtWidget().setFocus()
viewerWindow.parent().reveal()
viewerWindow.parent()._qtWidget().resize( 696, 300 )
viewerWindow.view()["minimumExpansionDepth"].setValue( 999 )
__delay( 0.1 )
viewerWindow.view().viewportGadget().frame( script["Transform"]["out"].bound( "/" ) )
GafferUI.WidgetAlgo.grab( widget = viewerWindow, imagePath = "images/example{exampleName}.png".format( exampleName = exampleName ) )
viewerWindow.parent().close()
del viewerWindow

# Example: Per-location Transform Spreadsheet
exampleName = "PerLocationLightTweakSpreadsheet"
script["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/resources/examples/rendering/perLocationLightTweakSpreadsheet.gfr" ) )
script.load()
viewerWindow = GafferUI.Viewer.acquire( script["ShaderTweaks"], floating = True )
viewerWindow._qtWidget().setFocus()
viewerWindow.parent().reveal()
viewerWindow.parent()._qtWidget().resize( 696, 300 )
viewerWindow.view()["minimumExpansionDepth"].setValue( 999 )
__delay( 0.1 )
viewerWindow.view().viewportGadget().frame( script["ShaderTweaks"]["out"].bound( "/" ) )
GafferUI.WidgetAlgo.grab( widget = viewerWindow, imagePath = "images/example{exampleName}.png".format( exampleName = exampleName ) )
viewerWindow.parent().close()
del viewerWindow

# Example: Multi-shot Render Spreadsheet
exampleName = "MultiShotRenderSpreadsheet"
script["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/resources/examples/rendering/multiShotRenderSpreadsheet.gfr" ) )
script.load()
nodeEditorWindow = GafferUI.NodeEditor.acquire( script["Spreadsheet_RenderOptions"], floating = True )
nodeEditorWindow._qtWidget().setFocus()
nodeEditorWindow._qtWidget().parent().resize( 696, 325 )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( widget = nodeEditorWindow, imagePath = "images/example{exampleName}.png".format( exampleName = exampleName ) )
nodeEditorWindow.parent().close()
del nodeEditorWindow
