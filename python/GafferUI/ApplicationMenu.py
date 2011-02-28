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

import os
import IECore
import Gaffer
import GafferUI

def appendDefinitions( menuDefinition, prefix ) :

	menuDefinition.append( prefix + "/About Gaffer...", { "command" : about } )
	menuDefinition.append( prefix + "/Preferences...", { } )
	menuDefinition.append( prefix + "/Documentation...", { "command" : IECore.curry( GafferUI.showURL, os.path.expandvars( "$GAFFER_ROOT/doc/gaffer/html/index.html" ) ) } )
	menuDefinition.append( prefix + "/Quit", { "command" : quit } )
		
def quit( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	application = scriptWindow.getScript().ancestor( Gaffer.ApplicationRoot.staticTypeId() )

	## \todo Check scripts aren't modified
	for script in application["scripts"].children() :
		application["scripts"].removeChild( script )

__aboutWindow = None
def about( menu ) :

	global __aboutWindow
	if __aboutWindow is None :
		
		__aboutWindow = GafferUI.AboutWindow( Gaffer.About )
		
	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	scriptWindow.addChildWindow( __aboutWindow )
	__aboutWindow.show()
