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
	menuDefinition.append( prefix + "/Settings...", { "command" : showSettings } )

## A function suitable as the command for a File/New menu item. It must be invoked from a menu which
# has a ScriptWindow in its ancestry.
def new( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	application = scriptWindow.scriptNode().ancestor( Gaffer.ApplicationRoot.staticTypeId() )

	newScript = Gaffer.ScriptNode( "script" )
	application["scripts"].addChild( newScript )

## A function suitable as the command for a File/Open menu item. It must be invoked from a menu which
# has a ScriptWindow in its ancestry.
def open( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	currentScript = scriptWindow.scriptNode()
	currentFileName = currentScript["fileName"].getValue()
	
	if currentFileName :
		path = Gaffer.FileSystemPath( os.path.dirname( os.path.abspath( currentFileName ) ) )		
	else :
		path = Gaffer.FileSystemPath( os.getcwd() )
	
	path.setFilter( __scriptPathFilter() )

	dialogue = GafferUI.PathChooserDialogue( path, title="Open script", confirmLabel="Open" )
	path = dialogue.waitForPath( parentWindow = scriptWindow )

	if not path :
		return

	__open( currentScript, str( path ) )
	
def __open( currentScript, fileName ) :

	application = currentScript.ancestor( Gaffer.ApplicationRoot.staticTypeId() )
		
	script = Gaffer.ScriptNode()
	script["fileName"].setValue( fileName )
	script.load()

	application["scripts"].addChild( script )
	
	addRecentFile( application, fileName )

	if not currentScript["fileName"].getValue() and not currentScript["unsavedChanges"].getValue() :
		# the current script is empty - the user will think of the operation as loading
		# the new script into the current window, rather than adding a new window. so make it
		# look like that.
		currentWindow = GafferUI.ScriptWindow.acquire( currentScript )
		newWindow = GafferUI.ScriptWindow.acquire( script )
		## \todo We probably want a way of querying and setting geometry in the public API
		newWindow._qtWidget().restoreGeometry( currentWindow._qtWidget().saveGeometry() )
		
		application["scripts"].removeChild( currentScript )

## A function suitable as the submenu callable for a File/OpenRecent menu item. It must be invoked
# from a menu which has a ScriptWindow in its ancestry.
def openRecent( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	currentScript = scriptWindow.scriptNode()
	applicationRoot = currentScript.ancestor( Gaffer.ApplicationRoot.staticTypeId() )
	
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
# has a ScriptWindow in its ancestry.
def save( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	if script["fileName"].getValue() :
		with GafferUI.ErrorDialogue.ExceptionHandler( title = "Error Saving File", parentWindow = scriptWindow ) :
			script.save()
	else :
		saveAs( menu )

## A function suitable as the command for a File/Save As menu item. It must be invoked from a menu which
# has a ScriptWindow in its ancestry.
def saveAs( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	currentFileName = script["fileName"].getValue()
	
	if currentFileName :
		path = Gaffer.FileSystemPath( currentFileName )		
	else :
		path = Gaffer.FileSystemPath( os.getcwd() )

	path.setFilter( __scriptPathFilter() )
	
	dialogue = GafferUI.PathChooserDialogue( path, title="Save script", confirmLabel="Save" )
	path = dialogue.waitForPath( parentWindow = scriptWindow )

	if not path :
		return
	
	path = str( path )
	if not path.endswith( ".gfr" ) :
		path += ".gfr"

	script["fileName"].setValue( path )
	with GafferUI.ErrorDialogue.ExceptionHandler( title = "Error Saving File", parentWindow = scriptWindow ) :
		script.save()
	
	application = script.ancestor( Gaffer.ApplicationRoot.staticTypeId() )
	addRecentFile( application, path )

## A function suitable as the command for a File/Revert To Saved menu item. It must be invoked from a menu which
# has a ScriptWindow in its ancestry.
def revertToSaved( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()

	script.load()
	
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
	
	selection = script.selection()
	parent = selection[0].parent()
	for node in selection :
		if not parent.isAncestorOf( node ) :
			assert( node.parent().isAncestorOf( parent ) )
			parent = node.parent()
	
	path = Gaffer.FileSystemPath( os.getcwd() )
	path.setFilter( __scriptPathFilter() )
	
	dialogue = GafferUI.PathChooserDialogue( path, title="Export selection", confirmLabel="Export" )
	path = dialogue.waitForPath( parentWindow = scriptWindow )

	if not path :
		return
	
	path = str( path )
	if not path.endswith( ".gfr" ) :
		path += ".gfr"		
	
	script.serialiseToFile( path, parent, script.selection() )
	
## A function suitable as the command for a File/Import File... menu item. It must be invoked from a menu which
# has a ScriptWindow in its ancestry.
def importFile( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	
	path = Gaffer.FileSystemPath( os.getcwd() )
	path.setFilter( __scriptPathFilter() )

	dialogue = GafferUI.PathChooserDialogue( path, title="Import script", confirmLabel="Import" )
	path = dialogue.waitForPath( parentWindow = scriptWindow )

	newNodes = []
	c = script.childAddedSignal().connect( lambda parent, child : newNodes.append( child ) )
	with Gaffer.UndoContext( script ) :
		## \todo We need to prevent the ScriptNode plugs themselves getting clobbered
		# when importing an entire script.
		script.executeFile( str( path ) )
	
	script.selection().clear()
	for n in newNodes :
		script.selection().add( n )
		
	## \todo Position the nodes somewhere sensible if there's a Node Graph available

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
	
def __scriptPathFilter() :

	return Gaffer.FileSystemPath.createStandardFilter( [ "gfr" ] )
	
def __selectionAvailable( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	return True if scriptWindow.scriptNode().selection().size() else False
