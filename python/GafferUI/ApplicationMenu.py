##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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
import weakref

import IECore
import Gaffer
import GafferUI

def appendDefinitions( menuDefinition, prefix ) :

	menuDefinition.append( prefix + "/About Gaffer...", { "command" : about } )
	menuDefinition.append( prefix + "/Preferences...", { "command" : preferences } )
	menuDefinition.append( prefix + "/Documentation...", { "command" : IECore.curry( GafferUI.showURL, os.path.expandvars( "$GAFFER_ROOT/doc/gaffer/html/index.html" ) ) } )
	menuDefinition.append( prefix + "/Quit", { "command" : quit, "shortCut" : "Ctrl+Q" } )
		
def quit( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	application = scriptWindow.scriptNode().ancestor( Gaffer.ApplicationRoot.staticTypeId() )

	unsavedNames = []
	for script in application["scripts"].children() :
		if script["unsavedChanges"].getValue() :
			f = script["fileName"].getValue()
			f = f.rpartition( "/" )[2] if f else "untitled"
			unsavedNames.append( f )

	if unsavedNames :
	
		dialogue = GafferUI.ConfirmationDialogue(
			"Discard Unsaved Changes?",
			"The following files have unsaved changes : \n\n" +
			"\n".join( [ " - " + n for n in unsavedNames ] ) +
			"\n\nDo you want to discard the changes and quit?",
			confirmLabel = "Discard and Quit"
		)
		
		if not dialogue.waitForConfirmation( parentWindow=scriptWindow ) :
			return
	
	for script in application["scripts"].children() :
		application["scripts"].removeChild( script )

__aboutWindow = None
def about( menu ) :

	global __aboutWindow
	if __aboutWindow is None :
		
		__aboutWindow = GafferUI.AboutWindow( Gaffer.About )
		
	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	scriptWindow.addChildWindow( __aboutWindow )
	__aboutWindow.setVisible( True )

__preferencesWindows = weakref.WeakKeyDictionary()
def preferences( menu ) :
	
	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	application = scriptWindow.scriptNode().ancestor( Gaffer.ApplicationRoot.staticTypeId() )

	global __preferencesWindows
	window = __preferencesWindows.get( application, None )
	if window is None :
	
		window = GafferUI.Dialogue( "Preferences" )
		closeButton = window._addButton( "Close" )
		window.__closeButtonConnection = closeButton.clickedSignal().connect( __closePreferences )
		saveButton = window._addButton( "Save" )
		window.__saveButtonConnection = saveButton.clickedSignal().connect( __savePreferences )
	
		nodeUI = GafferUI.NodeUI.create( application["preferences"] )
		window._setWidget( nodeUI )
	
		__preferencesWindows[application] = window
		
		scriptWindow.addChildWindow( window )
		
	window.setVisible( True )
	
def __closePreferences( button ) :

	button.ancestor( type=GafferUI.Window ).setVisible( False )

def __savePreferences( button ) :

	scriptWindow = button.ancestor( GafferUI.ScriptWindow )
	application = scriptWindow.scriptNode().ancestor( Gaffer.ApplicationRoot.staticTypeId() )
	application.savePreferences()
	button.ancestor( type=GafferUI.Window ).setVisible( False )
	
