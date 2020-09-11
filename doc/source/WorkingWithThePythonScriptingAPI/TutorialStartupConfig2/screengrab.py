# BuildTarget: images/tutorialBookmarks.png
# BuildTarget: images/tutorialDefaultBookmark.png
# BuildTarget: images/tutorialDefaultImageNodeBookmark.png
# BuildTarget: images/tutorialDefaultImageNodePath.png

import os
import subprocess32 as subprocess
import tempfile
import time

import Gaffer
import GafferUI
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

# Tutorial: bookmarks in a file browser
__imageName = "tutorialBookmarks"
__tempImagePath = __getTempFilePath( "{}.png".format( __imageName ) )
__rootPath = Gaffer.FileSystemPath( os.path.expandvars( "$GAFFER_ROOT" ) )
__bookmarks = GafferUI.Bookmarks.acquire( application, Gaffer.FileSystemPath )
__fileBrowser = GafferUI.PathChooserDialogue( __rootPath, bookmarks = __bookmarks )
__fileBrowser.setVisible( True )
__delay( 0.1 )
__pathChooser = __fileBrowser.pathChooserWidget()
__button = __pathChooser._PathChooserWidget__bookmarksButton
__button._qtWidget().click()
GafferUI.WidgetAlgo.grab( widget = __fileBrowser, imagePath = __tempImagePath )
__dispatchScript(
	script = "scripts/{}_edit.gfr".format( __imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader.fileName '\"{}\"'".format( __tempImagePath ),
		"-ImageWriter.fileName '\"{}\"'".format( os.path.abspath( "images/{}.png".format( __imageName ) ) )
		]
	)
__fileBrowser.setVisible( False )

# Tutorial: default bookmark in file browser
__imageName = "tutorialDefaultBookmark"
__tempImagePath = __getTempFilePath( "{}.png".format( __imageName ) )
__bookmarks.add( "Resources", "/" )
__fileBrowser = GafferUI.PathChooserDialogue( __rootPath, bookmarks = __bookmarks )
__fileBrowser.setVisible( True )
__delay( 0.1 )
__pathChooser = __fileBrowser.pathChooserWidget()
__button = __pathChooser._PathChooserWidget__bookmarksButton
__button._qtWidget().click()
GafferUI.WidgetAlgo.grab( widget = __fileBrowser, imagePath = __tempImagePath )
__dispatchScript(
	script = "scripts/{}_edit.gfr".format( __imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader.fileName '\"{}\"'".format( __tempImagePath ),
		"-ImageWriter.fileName '\"{}\"'".format( os.path.abspath( "images/{}.png".format( __imageName ) ) )
		]
	)
__fileBrowser.setVisible( False )

# Tutorial: default bookmark in image node file browser
__imageName = "tutorialDefaultImageNodeBookmark"
__tempImagePath = __getTempFilePath( "{}.png".format( __imageName ) )
__bookmarks = GafferUI.Bookmarks.acquire( application, Gaffer.FileSystemPath, "image" )
__bookmarks.add( "Pictures", "/" )
__fileBrowser = GafferUI.PathChooserDialogue( __rootPath, bookmarks = __bookmarks )
__fileBrowser.setVisible( True )
__delay( 0.1 )
__pathChooser = __fileBrowser.pathChooserWidget()
__button = __pathChooser._PathChooserWidget__bookmarksButton
__button._qtWidget().click()
GafferUI.WidgetAlgo.grab( widget = __fileBrowser, imagePath = __tempImagePath )
__dispatchScript(
	script = "scripts/{}_edit.gfr".format( __imageName ),
	tasks = [ "ImageWriter" ],
	settings = [
		"-ImageReader.fileName '\"{}\"'".format( __tempImagePath ),
		"-ImageWriter.fileName '\"{}\"'".format( os.path.abspath( "images/{}.png".format( __imageName ) ) )
		]
	)
__fileBrowser.setVisible( False )

# Tutorial: default path in image node file browser
__rootPath = Gaffer.FileSystemPath( os.path.expandvars( "$HOME/Pictures" ) )
__bookmarks = GafferUI.Bookmarks.acquire( application, Gaffer.FileSystemPath, "image" )
__fileBrowser = GafferUI.PathChooserDialogue( __rootPath, bookmarks = __bookmarks )
__fileBrowser.setVisible( True )
__delay( 0.1 )
GafferUI.WidgetAlgo.grab( __fileBrowser, "images/tutorialDefaultImageNodePath.png" )
