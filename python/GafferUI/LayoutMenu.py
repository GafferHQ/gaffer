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

import functools

import IECore

import GafferUI

## Appends a submenu of the given name to the specified IECore.MenuDefinition. The submenu
# contains commands to facilitate the administration of different UI layouts.
def appendDefinitions( menuDefinition, name="" ) :

	menuDefinition.append( name, { "subMenu" : layoutMenuCallable } )

## A function suitable as the command for a Layout/Name menu item which restores a named layout.
# It must be invoked from a menu which has a ScriptWindow in its ancestry.
def restore( menu, name ) :

	scriptWindow, layouts = __scriptWindowAndLayouts( menu )
	layout = layouts.create( name, scriptWindow.scriptNode() )

	scriptWindow.setLayout( layout )

	if not GafferUI.Widget.currentModifiers() & GafferUI.ModifiableEvent.Modifiers.Alt :
		layout.restoreWindowState()

## A function suitable as the command for a 'Layout/Save...' menu item. It must be invoked from
# a menu which has a ScriptWindow in its ancestry.
def save( menu ) :

	scriptWindow, layouts = __scriptWindowAndLayouts( menu )

	layoutNames = layouts.names()
	i = 1
	while True :
		layoutName = "Layout " + str( i )
		i += 1
		if layoutName not in layoutNames :
			break

	d = GafferUI.TextInputDialogue( initialText=layoutName, title="Save Layout", confirmLabel="Save" )
	t = d.waitForText( parentWindow = scriptWindow )
	d.setVisible( False )

	if not t :
		return

	saveAs( t, menu )

## A function suitable as the command for a 'Layout/Save As <name>' menu item where the name
# is already known. It must be invoked from a menu which has a ScriptWindow in its ancestry.
def saveAs( name, menu ) :

	scriptWindow, layouts = __scriptWindowAndLayouts( menu )

	layout = scriptWindow.getLayout()
	layouts.add( name, layout, persistent = True )

def fullScreen( menu, checkBox ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	scriptWindow.setFullScreen( checkBox )

def fullScreenCheckBox( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	return scriptWindow.getFullScreen()

## The callable used to generate the submenu created by appendDefinitions().
# This is exposed publicly so it can be called by alternative submenus and
# the result edited before being given to a Menu.
def layoutMenuCallable( menu ) :

	scriptWindow, layouts = __scriptWindowAndLayouts( menu )

	menuDefinition = IECore.MenuDefinition()

	# Menu items to set layout

	layoutNames = sorted( layouts.names() )
	for name in layoutNames :
		menuDefinition.append(
			"/restore:" + name,
			{
				"command" : functools.partial( restore, name = name ),
				"label" : name
			}
		)
	if layoutNames :
		menuDefinition.append( "/SetDivider", { "divider" : True } )

	# Menu items to choose default

	def __setDefault( layouts, name, *unused ) :

		layouts.setDefault( name, persistent = True )

	for name in layoutNames :
		menuDefinition.append(
			"/Default/" + name,
			{
				"command" : functools.partial( __setDefault, layouts, name ),
				"checkBox" : layouts.getDefault() == name
			}
		)
	if layoutNames :
		menuDefinition.append( "/DefaultDivider", { "divider" : True } )

	# Menu items to save layout

	persistentLayoutNames = sorted( layouts.names( persistent = True ) )
	for name in persistentLayoutNames :
		menuDefinition.append(
			"/Save As/saveAs:" + name,
			{
				"command" : functools.partial( saveAs, name ),
				"label" : name
			}
		)
	if persistentLayoutNames :
		menuDefinition.append( "/Save As/Divider", { "divider" : True } )

	menuDefinition.append( "/Save As/New Layout...", { "command" : save } )

	# Menu items to delete layouts

	if persistentLayoutNames :
		for name in persistentLayoutNames :
			menuDefinition.append( "/Delete/" + name, { "command" : functools.partial( layouts.remove, name = name ) } )

	menuDefinition.append( "/SaveDeleteDivider", { "divider" : True } )

	# Other menu items

	menuDefinition.append( "/Full Screen", { "command" : fullScreen, "checkBox" : fullScreenCheckBox, "shortCut" : "F11" } )

	return menuDefinition

def __scriptWindowAndLayouts( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	layouts = GafferUI.Layouts.acquire( scriptWindow.scriptNode().applicationRoot() )

	return scriptWindow, layouts
