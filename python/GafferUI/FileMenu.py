##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import os
import functools
import imath

import IECore

import Gaffer
import GafferUI

## Appends items to the IECore.MenuDefinition object passed to build a File menu containing
# standard open/save/revert/etc
def appendDefinitions( menuDefinition, prefix="" ) :

	menuDefinition.append( prefix + "/New", { "command" : new, "shortCut" : "Ctrl+N" } )
	menuDefinition.append( prefix + "/Open...", { "command" : open, "shortCut" : "Ctrl+O" } )
	menuDefinition.append( prefix + "/Open Recent", { "subMenu" : openRecent } )
	menuDefinition.append( prefix + "/OpenDivider", { "divider" : True } )
	menuDefinition.append( prefix + "/Save", { "command" : save, "shortCut" : "Ctrl+S" } )
	menuDefinition.append( prefix + "/Save As...", { "command" : saveAs, "shortCut" : "Shift+Ctrl+S" } )
	menuDefinition.append( prefix + "/Revert To Saved", { "command" : revertToSaved, "active" : __revertToSavedAvailable } )
	menuDefinition.append( prefix + "/SaveDivider", { "divider" : True } )
	menuDefinition.append( prefix + "/Export Selection...", { "command" : exportSelection, "active" : __selectionAvailable } )
	menuDefinition.append( prefix + "/Import...", { "command" : importFile } )
	menuDefinition.append( prefix + "/ImportExportDivider", { "divider" : True } )
	menuDefinition.append( prefix + "/Settings...", { "command" : showSettings } )

## A function suitable as the command for a File/New menu item. It must be invoked from a menu which
# has a ScriptWindow in its ancestry.
def new( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	application = scriptWindow.scriptNode().ancestor( Gaffer.ApplicationRoot )

	newScript = Gaffer.ScriptNode()
	Gaffer.NodeAlgo.applyUserDefaults( newScript )
	application["scripts"].addChild( newScript )

## A function suitable as the command for a File/Open menu item. It must be invoked from a menu which
# has a ScriptWindow in its ancestry.
def open( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	path, bookmarks = __pathAndBookmarks( scriptWindow )

	dialogue = GafferUI.PathChooserDialogue( path, title="Open script", confirmLabel="Open", valid=True, leaf=True, bookmarks=bookmarks )
	path = dialogue.waitForPath( parentWindow = scriptWindow )

	if not path :
		return

	__open( scriptWindow.scriptNode(), str( path ) )

## Opens a script and adds it to the application, as if the user
# had done so via the File Open dialogue.
#
# :param asNew When true, the scripts file name/dirty state will be reset
#    upon load. Effectively creating an untitled copy.
def addScript( application, fileName, asNew = False ) :

	return __addScript( application, fileName, asNew = asNew )

def __addScript( application, fileName, dialogueParentWindow = None, asNew = False ) :

	recoveryFileName = None
	backups = GafferUI.Backups.acquire( application, createIfNecessary = False )
	if backups is not None :
		recoveryFileName = backups.recoveryFile( fileName )
		if recoveryFileName :
			dialogue = GafferUI.ConfirmationDialogue(
				title = "Backup Available",
				message = "A more recent backup is available. Open backup instead?",
				confirmLabel = "Open Backup",
				cancelLabel = "Open",
			)
			useBackup = dialogue.waitForConfirmation( parentWindow = dialogueParentWindow )
			if useBackup is None :
				return
			elif not useBackup :
				recoveryFileName = None
			dialogue.setVisible( False )

	script = Gaffer.ScriptNode()
	script["fileName"].setValue( recoveryFileName or fileName )

	dialogue = GafferUI.BackgroundTaskDialogue( "Loading" )
	result = dialogue.waitForBackgroundTask( functools.partial( script.load, continueOnError = True, ), dialogueParentWindow )
	if isinstance( result, IECore.Cancelled ) :
		return

	if asNew or recoveryFileName :
		# If we loaded a backup (or as new), rename the script to the old
		# filename (or nothing) so the user can resave and continue as before.
		script["fileName"].setValue( "" if asNew else fileName )
		script["unsavedChanges"].setValue( True )

	application["scripts"].addChild( script )

	if not asNew:
		addRecentFile( application, fileName )

	return script

def __open( currentScript, fileName ) :

	application = currentScript.ancestor( Gaffer.ApplicationRoot )
	currentWindow = GafferUI.ScriptWindow.acquire( currentScript )

	script = __addScript( application, fileName, dialogueParentWindow = currentWindow )
	if not script :
		return

	if not currentScript["fileName"].getValue() and not currentScript["unsavedChanges"].getValue() :
		# the current script is empty - the user will think of the operation as loading
		# the new script into the current window, rather than adding a new window. so make it
		# look like that.
		newWindow = GafferUI.ScriptWindow.acquire( script )
		## \todo We probably want a way of querying and setting geometry in the public API
		newWindow._qtWidget().restoreGeometry( currentWindow._qtWidget().saveGeometry() )
		currentWindow.setVisible( False )
		application["scripts"].removeChild( currentScript )
		# Defer destruction of `currentWindow` to avoid Qt crash (because we are invoked from
		# a menu parented to it).
		GafferUI.WidgetAlgo.keepUntilIdle( currentWindow )

## A function suitable as the submenu callable for a File/OpenRecent menu item. It must be invoked
# from a menu which has a ScriptWindow in its ancestry.
def openRecent( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	currentScript = scriptWindow.scriptNode()
	applicationRoot = currentScript.ancestor( Gaffer.ApplicationRoot )

	recentFiles = []
	with IECore.IgnoredExceptions( AttributeError ) :
		recentFiles = applicationRoot.__recentFiles

	result = IECore.MenuDefinition()
	if recentFiles :
		for index, fileName in enumerate( recentFiles ) :
			result.append(
				"/" + str( index ),
				{
					"label": os.path.basename( fileName ),
					"command" : functools.partial( __open, currentScript, fileName ),
					"description" : fileName,
					"active" : os.path.isfile( fileName )
				}
			)
	else :
		result.append( "/None Available", { "active" : False } )

	return result

## This function adds a file to the list shown in the File/OpenRecent menu, and saves a recentFiles.py
# in the application's user startup folder so the settings will persist.
## \todo In a future major version, add a datetime argument and use it to
# split the recent files menu into sections to make it easier to read. The
# `_reserved` argument is a placeholder so that when we do this, older versions
# will be able to continue to load the `recentFiles.py` config.
def addRecentFile( application, fileName, *_reserved ) :

	if isinstance( application, Gaffer.Application ) :
		applicationRoot = application.root()
	else :
		applicationRoot = application

	try :
		applicationRoot.__recentFiles
	except AttributeError :
		applicationRoot.__recentFiles = []

	if fileName in applicationRoot.__recentFiles :
		applicationRoot.__recentFiles.remove( fileName )

	applicationRoot.__recentFiles.insert( 0, fileName )
	del applicationRoot.__recentFiles[25:]

	# Accessing via builtins to avoid shadowing by our own `open()` method above.
	with __builtins__["open"]( os.path.join( applicationRoot.preferencesLocation(), "recentFiles.py" ), "w" ) as f :

		f.write( "# This file was automatically generated by Gaffer.\n" )
		f.write( "# Do not edit this file - it will be overwritten.\n\n" )

		f.write( "import GafferUI\n" )
		for fileName in reversed( applicationRoot.__recentFiles ) :
			f.write( "GafferUI.FileMenu.addRecentFile( application, \"%s\" )\n" % fileName )

## A function suitable as the command for a File/Save menu item. It must be invoked from a menu which
# has a ScriptWindow in its ancestry.
def save( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	if script["fileName"].getValue() :
		dialogue = GafferUI.BackgroundTaskDialogue( "Saving File" )
		dialogue.waitForBackgroundTask( script.save, parentWindow = scriptWindow )
	else :
		saveAs( menu )

## A function suitable as the command for a File/Save As menu item. It must be invoked from a menu which
# has a ScriptWindow in its ancestry.
def saveAs( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	path, bookmarks = __pathAndBookmarks( scriptWindow )

	dialogue = GafferUI.PathChooserDialogue( path, title="Save script", confirmLabel="Save", leaf=True, bookmarks=bookmarks )
	path = dialogue.waitForPath( parentWindow = scriptWindow )

	if not path :
		return

	path = str( path )
	if not path.endswith( ".gfr" ) :
		path += ".gfr"

	dialogue = GafferUI.BackgroundTaskDialogue( "Saving File" )
	result = dialogue.waitForBackgroundTask( functools.partial( script.serialiseToFile, path ), parentWindow = scriptWindow )

	if not isinstance( result, Exception ) :
		script["fileName"].setValue( path )
		script["unsavedChanges"].setValue( False )
		application = script.ancestor( Gaffer.ApplicationRoot )
		addRecentFile( application, path )

## A function suitable as the command for a File/Revert To Saved menu item. It must be invoked from a menu which
# has a ScriptWindow in its ancestry.
def revertToSaved( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )

	dialogue = GafferUI.ConfirmationDialogue(
		title = "Discard Unsaved Changes?",
		message = "There are unsaved changes which will be lost."
			"Discard them and revert?",
		confirmLabel = "Revert",
		cancelLabel = "Cancel",
	)
	if not dialogue.waitForConfirmation( parentWindow = scriptWindow ) :
		return

	with GafferUI.ErrorDialogue.ErrorHandler(
		title = "Errors Occurred During Loading",
		closeLabel = "Oy vey",
		parentWindow = scriptWindow
	) :
		scriptWindow.scriptNode().load( continueOnError = True )

def __revertToSavedAvailable( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()

	if script["fileName"].getValue() and script["unsavedChanges"].getValue() :
		return True

	return False

## A function suitable as the command for a File/Export Selection... menu item. It must be invoked from a menu which
# has a ScriptWindow in its ancestry.
def exportSelection( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	path, bookmarks = __pathAndBookmarks( scriptWindow )

	selection = script.selection()
	parent = selection[0].parent()
	for node in selection :
		if not parent.isAncestorOf( node ) :
			assert( node.parent().isAncestorOf( parent ) )
			parent = node.parent()

	dialogue = GafferUI.PathChooserDialogue( path, title="Export selection", confirmLabel="Export", leaf=True, bookmarks=bookmarks )
	path = dialogue.waitForPath( parentWindow = scriptWindow )

	if not path :
		return

	path = str( path )
	if not path.endswith( ".gfr" ) :
		path += ".gfr"

	dialogue = GafferUI.BackgroundTaskDialogue( "Saving File" )
	dialogue.waitForBackgroundTask( functools.partial( script.serialiseToFile, path, parent, script.selection() ), parentWindow = scriptWindow )

## A function suitable as the command for a File/Import File... menu item. It must be invoked from a menu which
# has a ScriptWindow in its ancestry.
def importFile( menu ) :

	scope = GafferUI.EditMenu.scope( menu )
	path, bookmarks = __pathAndBookmarks( scope.scriptWindow )

	dialogue = GafferUI.PathChooserDialogue( path, title="Import script", confirmLabel="Import", valid=True, leaf=True, bookmarks=bookmarks )
	path = dialogue.waitForPath( parentWindow = scope.scriptWindow )

	if path is None :
		return

	errorHandler = GafferUI.ErrorDialogue.ErrorHandler(
		title = "Errors Occurred During Loading",
		closeLabel = "Oy vey",
		parentWindow = scope.scriptWindow
	)

	with Gaffer.UndoScope( scope.script ), errorHandler :

		newChildren = []
		c = scope.parent.childAddedSignal().connect( lambda parent, child : newChildren.append( child ) )

		scope.script.importFile( str( path ), parent = scope.parent, continueOnError = True )

		newNodes = [ c for c in newChildren if isinstance( c, Gaffer.Node ) ]
		scope.script.selection().clear()
		scope.script.selection().add( newNodes )

		if scope.graphEditor :

			fallbackPosition = scope.graphEditor.bound().size() / 2
			fallbackPosition = scope.graphEditor.graphGadgetWidget().getViewportGadget().rasterToGadgetSpace(
				imath.V2f( fallbackPosition.x, fallbackPosition.y ),
				gadget = scope.graphEditor.graphGadget()
			).p0
			fallbackPosition = imath.V2f( fallbackPosition.x, fallbackPosition.y )

			scope.graphEditor.graphGadget().getLayout().positionNodes(
				scope.graphEditor.graphGadget(), scope.script.selection(), fallbackPosition
			)

			scope.graphEditor.frame( scope.script.selection(), extend = True )

## A function suitable as the command for a File/Settings... menu item.
def showSettings( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )

	settingsWindow = None
	for window in scriptWindow.childWindows() :
		if hasattr( window, "_settingsEditor" ) :
			settingsWindow = window
			break

	if settingsWindow is None :
		settingsWindow = GafferUI.Window( "Settings", borderWidth=8 )
		settingsWindow._settingsEditor = True
		settingsWindow.setChild( GafferUI.NodeUI.create( scriptWindow.scriptNode() ) )
		scriptWindow.addChildWindow( settingsWindow )

	settingsWindow.setVisible( True )

def __selectionAvailable( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	return True if scriptWindow.scriptNode().selection().size() else False

def __pathAndBookmarks( scriptWindow ) :

	bookmarks = GafferUI.Bookmarks.acquire(
		scriptWindow,
		pathType = Gaffer.FileSystemPath,
		category = "script",
	)

	currentFileName = scriptWindow.scriptNode()["fileName"].getValue()
	if currentFileName :
		path = Gaffer.FileSystemPath( os.path.dirname( os.path.abspath( currentFileName ) ) )
	else :
		path = Gaffer.FileSystemPath( bookmarks.getDefault( scriptWindow ) )

	path.setFilter( Gaffer.FileSystemPath.createStandardFilter( [ "gfr" ] ) )

	return path, bookmarks
