##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

from __future__ import with_statement

import Gaffer
import GafferUI

def appendDefinitions( menuDefinition, prefix="" ) :

	## \todo Grey out options when they won't work.
	menuDefinition.append( prefix + "/Undo", { "command" : undo } )
	menuDefinition.append( prefix + "/Redo", { "command" : redo } )
	menuDefinition.append( prefix + "/UndoDivider", { "divider" : True } )
	
	menuDefinition.append( prefix + "/Cut", { "command" : cut } )
	menuDefinition.append( prefix + "/Copy", { "command" : copy } )
	menuDefinition.append( prefix + "/Paste", { "command" : paste } )
	menuDefinition.append( prefix + "/Delete", { "command" : delete } )
	menuDefinition.append( prefix + "/CutCopyPasteDeleteDivider", { "divider" : True } )

	menuDefinition.append( prefix + "/Select All", { "command" : selectAll } )

## A function suitable as the command for an Edit/Undo menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def undo( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.getScript()
	script.undo()
	
## A function suitable as the command for an Edit/Redo menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def redo( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.getScript()
	script.redo()

## A function suitable as the command for an Edit/Cut menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def cut( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.getScript()

	with Gaffer.UndoContext( script ) :
		script.cut( script.selection() )

## A function suitable as the command for an Edit/Copy menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def copy( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.getScript()
	script.copy( script.selection() )

## A function suitable as the command for an Edit/Paste menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def paste( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.getScript()
	
	with Gaffer.UndoContext( script ) :
	
		script.paste()
	
## A function suitable as the command for an Edit/Delete menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def delete( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.getScript()
	
	with Gaffer.UndoContext( script ) :
		
		script.deleteNodes( script.selection() )
	
## A function suitable as the command for an Edit/Select All menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def selectAll( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.getScript()
	
	for c in script.children() :
		if c.isInstanceOf( Gaffer.Node.staticTypeId() ) :
			script.selection().add( c )	
