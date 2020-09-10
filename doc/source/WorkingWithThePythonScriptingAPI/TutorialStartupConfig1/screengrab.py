# BuildTarget: images/tutorialSettingsWindowDefaultContextVariables.png
# BuildTarget: images/tutorialSettingsWindowCustomContextVariable.png
# BuildTarget: images/tutorialVariableSubstitutionInStringPlug.png
# BuildTarget: images/tutorialVariableSubstitutionExpression.png
# BuildTarget: images/tutorialVariableSubstitutionTest.png

import os
import subprocess32 as subprocess
import tempfile
import time

import IECore
import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

scriptWindow = GafferUI.ScriptWindow.acquire( script )
viewer = scriptWindow.getLayout().editors( GafferUI.Viewer )[0]
graphEditor = scriptWindow.getLayout().editors( GafferUI.GraphEditor )[0]
hierarchyView = scriptWindow.getLayout().editors( GafferSceneUI.HierarchyView )[0]

# Delay for x seconds
def __delay( delay ) :
	endtime = time.time() + delay
	while time.time() < endtime :
		GafferUI.EventLoop.waitForIdle( 1 )

# Create a random directory in `/tmp` for the dispatcher's `jobsDirectory`, so we don't clutter the user's `~gaffer` directory
__temporaryDirectory = tempfile.mkdtemp( prefix = "gafferDocs" )

def __getTempFilePath( fileName, directory = __temporaryDirectory ) :
	filePath = "/".join( ( directory, fileName ) )
	
	return filePath

def __dispatchScript( script, tasks, settings ) :
	command = "gaffer dispatch -script {} -tasks {} -dispatcher Local -settings {} -dispatcher.jobsDirectory '\"{}/dispatcher/local\"'".format(
		script,
		" ".join( tasks ),
		" ".join( settings ),
		__temporaryDirectory
		)
	subprocess.check_call( command, shell=True )

# Illustration: a `tree` command run on a custom startup config
# TODO: Automate `images/illustrationStartupConfigDirectoryTree.png` when these tools become available:
# - Launching/controlling/screengrabbing other applications

# Interface: the default context variables in the Settings window
GafferUI.FileMenu.showSettings( scriptWindow.getLayout() )
__settingsWindow = scriptWindow.childWindows()[0]
__settingsWindow.getChild().plugValueWidget( script["variables"] ).reveal()
__settingsWindow.setVisible( True )
GafferUI.WidgetAlgo.grab( widget = __settingsWindow, imagePath = "images/tutorialSettingsWindowDefaultContextVariables.png" )
__settingsWindow.setVisible( False )

# Tutorial: a custom context variable in the Settings window
script["variables"].addMember( "project:resources", "${GAFFER_ROOT}/resources/", "projectResources" )
Gaffer.MetadataAlgo.setReadOnly( script["variables"]["projectResources"]["name"], True )
GafferUI.FileMenu.showSettings( scriptWindow.getLayout() )
__settingsWindow = scriptWindow.childWindows()[0]
__settingsWindow.getChild().plugValueWidget( script["variables"] ).reveal()
__settingsWindow.setVisible( True )
GafferUI.WidgetAlgo.grab( widget = __settingsWindow, imagePath = "images/tutorialSettingsWindowCustomContextVariable.png" )
__settingsWindow.setVisible( False )

# Tutorial: variable substitution in a string plug
__imageName = "tutorialVariableSubstitutionInStringPlug"
__tempImagePath = __getTempFilePath( "{}.png".format( __imageName ) )
script["SceneReader"] = GafferScene.SceneReader()
script["SceneReader"]["fileName"].setValue( "${project:resources}/gafferBot/caches/gafferBot.scc" )
script.selection().add( script["SceneReader"] )
with GafferUI.Window( "Node Editor : SceneReader" ) as __nodeEditorWindow :

	nodeEditor = GafferUI.NodeEditor( script )

__nodeEditorWindow._qtWidget().resize( 512, 256 )
__nodeEditorWindow._qtWidget().setFocus()
__nodeEditorWindow.setVisible( True )
GafferUI.WidgetAlgo.grab( widget = __nodeEditorWindow, imagePath = __tempImagePath )
__dispatchScript(
	script = "scripts/{}_edit.gfr".format( __imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader.fileName '\"{}\"'".format( __tempImagePath ),
		"-ImageWriter.fileName '\"{}\"'".format( os.path.abspath( "images/{}.png".format( __imageName ) ) )
		]
	)
script.selection().clear()
__nodeEditorWindow.setVisible( False )

# Tutorial: testing the variable substitution in main window
# TODO: Automate the right window pane to be wider
script.selection().add( script["SceneReader"] )
__delay(1)
with script.context():
	viewer.view().viewportGadget().frame( script["SceneReader"]["out"].bound( "/" ) )
	viewer.view().viewportGadget().getPrimaryChild().waitForCompletion()
	paths = IECore.PathMatcher( [ "/" ] )
	GafferSceneUI.ContextAlgo.expand( script.context(), paths )
	GafferSceneUI.ContextAlgo.expandDescendants( script.context(), paths, script["SceneReader"]["out"] )
GafferUI.WidgetAlgo.grab( widget = scriptWindow, imagePath = "images/tutorialVariableSubstitutionTest.png" )
