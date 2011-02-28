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
import GafferRI

## Returns a menu definition for the creation of SLO shader nodes.
# This contains entries for all shaders found on the shader searchpath
# defined by DL_SHADERS_PATH.
def definition() :

	if not len( __definition.items() ) :
	
		paths = os.environ.get( "DL_SHADERS_PATH", "" ).split( ":" )
		for path in paths :
			if path in ( ".", "./" ) :
				continue
			for root, dirs, files in os.walk( path ) :
				for f in files :
					s = os.path.splitext( f ) 
					if s[1]==".sdl" :
						shaderName = os.path.join( root[len(path):], s[0] )
						__definition.append( shaderName, { "command" : __createCommand( shaderName ) } )
					
	return __definition

__definition = IECore.MenuDefinition()

def __createCommand( shaderName ) : 
	
	def f( menu ) :
	
		scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
		script = scriptWindow.getScript()

		node = GafferRI.SLONode( name=os.path.split( shaderName )[-1] )
		node["name"].setValue( shaderName )

		with Gaffer.UndoContext( script ) :
			script.addChild( node )

	return f
