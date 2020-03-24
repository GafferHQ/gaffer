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
import functools

import IECore
import Gaffer
import GafferUI

def appendDefinitions( menuDefinition, prefix ) :

	menuDefinition.append( prefix + "/About Gaffer...", { "command" : about } )
	menuDefinition.append( prefix + "/Preferences...", { "command" : preferences } )
	menuDefinition.append( prefix + "/Documentation...", { "command" : functools.partial( GafferUI.showURL, os.path.expandvars( "$GAFFER_ROOT/doc/gaffer/html/index.html" ) ) } )
	menuDefinition.append( prefix + "/Quit", { "command" : quit, "shortCut" : "Ctrl+Q" } )

def quit( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	application = scriptWindow.scriptNode().ancestor( Gaffer.ApplicationRoot )

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

	# Defer the actual removal of scripts till an idle event - removing all
	# the scripts will result in the removal of the window our menu item is
	# parented to, which would cause a crash as it's deleted away from over us.
	GafferUI.EventLoop.addIdleCallback( functools.partial( __removeAllScripts, application ) )

def __removeAllScripts( application ) :

	for script in application["scripts"].children() :
		application["scripts"].removeChild( script )

	return False # remove idle callback

__aboutWindow = None
def about( menu ) :

	global __aboutWindow

	if __aboutWindow is not None and __aboutWindow() :
		window = __aboutWindow()
	else :
		window = GafferUI.AboutWindow( Gaffer.About )
		__aboutWindow = weakref.ref( window )

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	scriptWindow.addChildWindow( window )
	window.setVisible( True )

__preferencesWindows = weakref.WeakKeyDictionary()
def preferences( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	application = scriptWindow.scriptNode().ancestor( Gaffer.ApplicationRoot )

	global __preferencesWindows
	window = __preferencesWindows.get( application, None )
	if window is not None and window() :
		window = window()
	else :
		window = GafferUI.Dialogue( "Preferences" )
		closeButton = window._addButton( "Close" )
		window.__closeButtonConnection = closeButton.clickedSignal().connect( __closePreferences )
		saveButton = window._addButton( "Save" )
		window.__saveButtonConnection = saveButton.clickedSignal().connect( __savePreferences )

		window._setWidget( GafferUI.NodeUI.create( application["preferences"] ) )

		__preferencesWindows[application] = weakref.ref( window )

		# The NodeUI builds lazily, so we force it to build now so we can
		# resize the window to fit. Since the plugs are configured per
		# application, we need to build them all.
		for plug in application["preferences"].children( Gaffer.Plug ) :
			window._getWidget().plugValueWidget( plug )
		window.resizeToFitChild()
		scriptWindow.addChildWindow( window )

	window.setVisible( True )

def __closePreferences( button ) :

	button.ancestor( type=GafferUI.Window ).setVisible( False )

def __savePreferences( button ) :

	scriptWindow = button.ancestor( GafferUI.ScriptWindow )
	application = scriptWindow.scriptNode().ancestor( Gaffer.ApplicationRoot )
	application.savePreferences()
	button.ancestor( type=GafferUI.Window ).setVisible( False )
