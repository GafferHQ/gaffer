##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import GafferUI

__namedLayouts = {}

## Serialises the passed Editor and stores it using the given name. This
# layout can then be recreated using the create() method below.
def add( name, editor ) :

	if not isinstance( editor, basestring ) :
		editor = repr( editor )
		
	__namedLayouts[name] = editor

## Removes a layout previously stored with add().
def remove( name ) :

	del __namedLayouts[name]

## Returns a list of the names of currently defined layouts
def names() :

	return __namedLayouts.keys()

## Recreates a previously stored layout, returning it in the form of a CompoundEditor.
def create( name ) :

	layout = __namedLayouts[name]
		
	# first try to import the modules the layout needs
	contextDict = {}
	imported = set()
	classNameRegex = re.compile( "Gaffer[^(,]*\(" )
	for className in classNameRegex.findall( layout ) :
		moduleName = className.partition( "." )[0]
		if moduleName not in imported :
			exec( "import %s" % moduleName, contextDict, contextDict )
			imported.add( moduleName )

	return eval( layout, contextDict, contextDict )

## Saves all layouts whose name matches the optional regular expression into the file object
# specified. If the file is later evaluated it will reregister the layouts with this module.
def save( fileObject, nameRegex = None ) :

	# decide what to write
	namesToWrite = []
	for name in names() :
		if nameRegex.match( name ) or nameRegex is None :
			namesToWrite.append( name )
	
	# write the necessary import statement
	fileObject.write( "import GafferUI\n\n" )
	
	# finally write out the layouts
	for name in namesToWrite :
		fileObject.write( "GafferUI.Layouts.add( \"%s\", \"%s\" )\n\n" % ( name, __namedLayouts[name] ) )
	
