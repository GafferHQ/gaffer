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

import re
import os

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
	menuDefinition.append( prefix + "/Close Script", { "command" : close, "shortCut" : "Ctrl+F4" } )
	menuDefinition.append( prefix + "/CloseDivider", { "divider" : True } )
	menuDefinition.append( prefix + "/Settings...", { "command" : showSettings } )

## A function suitable as the command for a File/New menu item. It must be invoked from a menu which
# has a ScriptWidget in its ancestry.
def new( menu ) :
	scriptWidget = GafferUI.ScriptWidget.acquire( menu )
	application = scriptWidget.scriptNode().ancestor( Gaffer.ApplicationRoot )

	newScript = Gaffer.ScriptNode()
	Gaffer.NodeAlgo.applyUserDefaults( newScript )
	application["scripts"].addChild( newScript )

## A function suitable as the command for a File/Open menu item. It must be invoked from a menu which
# has a ScriptWidget in its ancestry.
def open( menu ) :

	scriptWidget = GafferUI.ScriptWidget.acquire( menu )
	applicationWindow = scriptWidget.ancestor( GafferUI.ApplicationWindow )

	path, bookmarks = __pathAndBookmarks( scriptWidget )

	dialogue = GafferUI.PathChooserDialogue( path, title="Open script", confirmLabel="Open", valid=True, leaf=True, bookmarks=bookmarks )
	path = dialogue.waitForPath( parentWindow = applicationWindow )

	if not path :
		return

	__open( scriptWidget.scriptNode(), str( path ) )

def __open( currentScript, fileName ) :

	application = currentScript.ancestor( Gaffer.ApplicationRoot )

	script = Gaffer.ScriptNode()
	script["fileName"].setValue( fileName )

	applicationWindow = GafferUI.ScriptWidget.acquire( currentScript ).ancestor( GafferUI.ApplicationWindow )

	with GafferUI.ErrorDialogue.ErrorHandler(
		title = "Errors Occurred During Loading",
		closeLabel = "Oy vey",
		parentWindow = applicationWindow
	) :
		script.load( continueOnError = True )

	application["scripts"].addChild( script )

	addRecentFile( application, fileName )

	removeCurrentScript = False
	if not currentScript["fileName"].getValue() and not currentScript["unsavedChanges"].getValue() :
		# the current script is empty - the user will think of the operation as loading
		# the new script into the current window, rather than adding a new window. so make it
		# look like that.
		currentWindow = GafferUI.ScriptWidget.acquire( currentScript )
		newWindow = GafferUI.ScriptWidget.acquire( script )
		## \todo We probably want a way of querying and setting geometry in the public API
		newWindow._qtWidget().restoreGeometry( currentWindow._qtWidget().saveGeometry() )
		currentWindow.setVisible( False )
		removeCurrentScript = True

	# We must defer the removal of the old script because otherwise we trigger a crash bug
	# in PySide - I think this is because the menu item that invokes us is a child of
	# currentWindow, and that will get deleted immediately when the script is removed.
	if removeCurrentScript :
		GafferUI.EventLoop.addIdleCallback( IECore.curry( __removeScript, application, currentScript ) )

def __removeScript( application, script ) :

	application["scripts"].removeChild( script )
	return False # remove idle callback

## A function suitable as the submenu callable for a File/OpenRecent menu item. It must be invoked
# from a menu which has a ScriptWidget in its ancestry.
def openRecent( menu ) :

	scriptWidget = GafferUI.ScriptWidget.acquire( menu )
	applicationWindow = scriptWidget.ancestor( GafferUI.ApplicationWindow )
	applicationRoot = applicationWindow.applicationRoot
	currentScript = scriptWidget.scriptNode()

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
					"command" : IECore.curry( __open, currentScript, fileName ),
					"description" : fileName,
					"active" : os.path.isfile( fileName )
				}
			)
	else :
		result.append( "/None Available", { "active" : False } )

	return result

## This function adds a file to the list shown in the File/OpenRecent menu, and saves a recentFiles.py
# in the application's user startup folder so the settings will persist.
def addRecentFile( application, fileName ) :

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
	del applicationRoot.__recentFiles[6:]

	f = file( os.path.join( applicationRoot.preferencesLocation(), "recentFiles.py" ), "w" )
	f.write( "# This file was automatically generated by Gaffer.\n" )
	f.write( "# Do not edit this file - it will be overwritten.\n\n" )

	f.write( "import GafferUI\n" )
	for fileName in reversed( applicationRoot.__recentFiles ) :
		f.write( "GafferUI.FileMenu.addRecentFile( application, \"%s\" )\n" % fileName )

## A function suitable as the command for a File/Save menu item. It must be invoked from a menu which
# has a ScriptWidget in its ancestry.
def save( menu ) :

	scriptWidget = GafferUI.ScriptWidget.acquire( menu )
	applicationWindow = scriptWidget.ancestor( GafferUI.ApplicationWindow )

	script = scriptWidget.scriptNode()
	if script["fileName"].getValue() :
		with GafferUI.ErrorDialogue.ErrorHandler( title = "Error Saving File", parentWindow = applicationWindow ) :
			script.save()
	else :
		saveAs( menu )

## A function suitable as the command for a File/Save As menu item. It must be invoked from a menu which
# has a ScriptWidget in its ancestry.
def saveAs( menu ) :

	scriptWidget = GafferUI.ScriptWidget.acquire( menu )
	applicationWindow = scriptWidget.ancestor( GafferUI.ApplicationWindow )

	script = scriptWidget.scriptNode()
	path, bookmarks = __pathAndBookmarks( applicationWindow )

	dialogue = GafferUI.PathChooserDialogue( path, title="Save script", confirmLabel="Save", leaf=True, bookmarks=bookmarks )
	path = dialogue.waitForPath( parentWindow = applicationWindow )

	if not path :
		return

	path = str( path )
	if not path.endswith( ".gfr" ) :
		path += ".gfr"

	script["fileName"].setValue( path )
	with GafferUI.ErrorDialogue.ErrorHandler( title = "Error Saving File", parentWindow = applicationWindow ) :
		script.save()

	application = script.ancestor( Gaffer.ApplicationRoot )
	addRecentFile( application, path )

## A function suitable as the command for a File/Revert To Saved menu item. It must be invoked from a menu which
# has a ScriptWidget in its ancestry.
def revertToSaved( menu ) :

	scriptWidget = GafferUI.ScriptWidget.acquire( menu )
	script = scriptWidget.scriptNode()

	script.load()

def __revertToSavedAvailable( menu ) :

	scriptWidget = GafferUI.ScriptWidget.acquire( menu )
	script = scriptWidget.scriptNode()

	if script["fileName"].getValue() and script["unsavedChanges"].getValue() :
		return True

	return False

## A function suitable as the command for a File/Export Selection... menu item. It must be invoked from a menu which
# has a ScriptWidget in its ancestry.
def exportSelection( menu ) :

	scriptWidget = GafferUI.ScriptWidget.acquire( menu )
	applicationWindow = scriptWidget.ancestor( GafferUI.ApplicationWindow )
	script = scriptWidget.scriptNode()
	path, bookmarks = __pathAndBookmarks( applicationWindow )

	selection = script.selection()
	parent = selection[0].parent()
	for node in selection :
		if not parent.isAncestorOf( node ) :
			assert( node.parent().isAncestorOf( parent ) )
			parent = node.parent()

	dialogue = GafferUI.PathChooserDialogue( path, title="Export selection", confirmLabel="Export", leaf=True, bookmarks=bookmarks )
	path = dialogue.waitForPath( parentWindow = applicationWindow )

	if not path :
		return

	path = str( path )
	if not path.endswith( ".gfr" ) :
		path += ".gfr"

	script.serialiseToFile( path, parent, script.selection() )

## A function suitable as the command for a File/Import File... menu item. It must be invoked from a menu which
# has a ScriptWidget in its ancestry.
def importFile( menu ) :

	scriptWidget = GafferUI.ScriptWidget.acquire( menu )
	applicationWindow = scriptWidget.ancestor( GafferUI.ApplicationWindow )
	script = scriptWidget.scriptNode()
	path, bookmarks = __pathAndBookmarks( applicationWindow )

	dialogue = GafferUI.PathChooserDialogue( path, title="Import script", confirmLabel="Import", valid=True, leaf=True, bookmarks=bookmarks )
	path = dialogue.waitForPath( parentWindow = applicationWindow )

	if path is None :
		return

	newChildren = []
	c = script.childAddedSignal().connect( lambda parent, child : newChildren.append( child ) )
	with Gaffer.UndoScope( script ) :
		## \todo We need to prevent the ScriptNode plugs themselves getting clobbered
		# when importing an entire script.
		script.executeFile( str( path ) )

	newNodes = [ c for c in newChildren if isinstance( c, Gaffer.Node ) ]
	script.selection().clear()
	script.selection().add( newNodes )

	## \todo Position the nodes somewhere sensible if there's a Node Graph available

def close( menu ) :

	scriptWidget = GafferUI.ScriptWidget.acquire( menu )
	applicationWindow = scriptWidget.ancestor( GafferUI.ApplicationWindow )

	if applicationWindow.acceptsTabClose(scriptWidget):
		scriptNode = scriptWidget.scriptNode()
		scriptNode.parent().removeChild( scriptNode )

## A function suitable as the command for a File/Settings... menu item.
def showSettings( menu ) :

	scriptWidget = GafferUI.ScriptWidget.acquire( menu )
	applicationWindow = scriptWidget.ancestor( GafferUI.ApplicationWindow )

	settingsWindow = None
	for window in applicationWindow.childWindows() :
		if hasattr( window, "_settingsEditor" ) :
			settingsWindow = window
			break

	if settingsWindow is None :
		settingsWindow = GafferUI.Window( "Settings", borderWidth=8 )
		settingsWindow._settingsEditor = True
		settingsWindow.setChild( GafferUI.NodeUI.create( scriptWidget.scriptNode() ) )
		applicationWindow.addChildWindow( settingsWindow )

	settingsWindow.setVisible( True )

def __selectionAvailable( menu ) :

	scriptWidget = GafferUI.ScriptWidget.acquire( menu )
	return True if scriptWidget.scriptNode().selection().size() else False

def __pathAndBookmarks( scriptWidget ) :

	bookmarks = GafferUI.Bookmarks.acquire(
		scriptWidget,
		pathType = Gaffer.FileSystemPath,
		category = "script",
	)

	currentFileName = scriptWidget.scriptNode()["fileName"].getValue()
	if currentFileName :
		path = Gaffer.FileSystemPath( os.path.dirname( os.path.abspath( currentFileName ) ) )
	else :
		path = Gaffer.FileSystemPath( bookmarks.getDefault( scriptWidget ) )

	path.setFilter( Gaffer.FileSystemPath.createStandardFilter( [ "gfr" ] ) )

	return path, bookmarks
