##########################################################################
#
#  Copyright (c) 2019, John Haddon. All rights reserved.
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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
import collections
import IECore

import Gaffer
import GafferUI

__examples = collections.OrderedDict()

def registerExample( key, absFilePath, description = "", notableNodes = None ) :

	__examples[ key ] = {
		"filePath" : absFilePath,
		"description" : description,
		"notableNodes" : notableNodes or []
	}

def deregisterExample( key ) :

	if key in __examples:
		del __examples[ key ]

def registeredExamples( node = None ) :

	if node :
		filtered = collections.OrderedDict()
		for k, e in __examples.items() :
			if node in e['notableNodes'] :
				filtered[ k ] = e
		return filtered

	else :
		return collections.OrderedDict( __examples )

def appendExamplesSubmenuDefinition( menuDefinition, root, forNode = None ) :

	callback = functools.partial( __buildExamplesMenu, forNode )
	menuDefinition.append( root,  { "subMenu" : callback } )

def __buildExamplesMenu( nodeOrNone, menu ) :

	result = IECore.MenuDefinition()

	examples = GafferUI.Examples.registeredExamples( node = nodeOrNone )
	if examples :

		for menuPath, data in examples.items() :
			filePath = os.path.expandvars( data['filePath'] )
			result.append(
				"/%s" % menuPath,
				{
					"command" : functools.partial( __openGafferScript, filePath ),
					"description" : data['description'] or None,
					"active" : os.path.isfile( filePath )
				}
			)
	else:
		result.append( "/No Examples Available", { "active" : False } )

	return result

def __openGafferScript( path, menu ) :
	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	app = scriptWindow.scriptNode().ancestor( Gaffer.ApplicationRoot )
	GafferUI.FileMenu.addScript( app, path, asNew = True )
