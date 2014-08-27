##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferUI

## The Layouts class provides a registry of named layouts for use
# in the ScriptWindow. To allow different gaffer applications to
# coexist happily in the same process (for instance to run both
# an asset management app and a shading app inside maya), separate
# sets of layouts are maintained on a per-application basis. Access
# to the layouts for a specific application is provided by the
# Layouts.acquire() method.
class Layouts :

	## Typically acquire() should be used in preference
	# to this constructor.
	def __init__( self ) :

		self.__namedLayouts = {}
		self.__registeredEditors = []

	## Acquires the set of layouts for the specified application.
	@classmethod
	def acquire( cls, applicationOrApplicationRoot ) :

		if isinstance( applicationOrApplicationRoot, Gaffer.Application ) :
			applicationRoot = applicationOrApplicationRoot.root()
		else :
			assert( isinstance( applicationOrApplicationRoot, Gaffer.ApplicationRoot ) )
			applicationRoot = applicationOrApplicationRoot

		try :
			return applicationRoot.__layouts
		except AttributeError :
			pass

		applicationRoot.__layouts = Layouts()

		return applicationRoot.__layouts

	## Serialises the passed Editor and stores it using the given name. This
	# layout can then be recreated using the create() method below.
	def add( self, name, editor ) :

		if not isinstance( editor, basestring ) :
			editor = repr( editor )

		self.__namedLayouts[name] = editor

	## Removes a layout previously stored with add().
	def remove( self, name ) :

		del self.__namedLayouts[name]

	## Returns a list of the names of currently defined layouts
	def names( self ) :

		return self.__namedLayouts.keys()

	## Recreates a previously stored layout for the specified script,
	# returning it in the form of a CompoundEditor.
	def create( self, name, scriptNode ) :

		layout = self.__namedLayouts[name]

		# first try to import the modules the layout needs
		contextDict = { "scriptNode" : scriptNode }
		imported = set()
		classNameRegex = re.compile( "[a-zA-Z]*Gaffer[^(,]*\(" )
		for className in classNameRegex.findall( layout ) :
			moduleName = className.partition( "." )[0]
			if moduleName not in imported :
				exec( "import %s" % moduleName, contextDict, contextDict )
				imported.add( moduleName )

		return eval( layout, contextDict, contextDict )

	## Saves all layouts whose name matches the optional regular expression into the file object
	# specified. If the file is later evaluated during application startup, it will reregister
	# the layouts with the application.
	## \todo Remove this method and follow the model in Bookmarks.py, where user bookmarks
	# are saved automatically. This wasn't possible when Layouts.py was first introduced,
	# because at that point in time, the Layouts class didn't have access to an application.
	def save( self, fileObject, nameRegex = None ) :

		# decide what to write
		namesToWrite = []
		for name in self.names() :
			if nameRegex.match( name ) or nameRegex is None :
				namesToWrite.append( name )

		# write the necessary import statement and acquire the layouts
		fileObject.write( "import GafferUI\n\n" )
		fileObject.write( "layouts = GafferUI.Layouts.acquire( application )\n\n" )

		# finally write out the layouts
		for name in namesToWrite :
			fileObject.write( "layouts.add( \"%s\", \"%s\" )\n\n" % ( name, self.__namedLayouts[name] ) )

		# tidy up by deleting the temporary variable, keeping the namespace clean for
		# subsequently executed config files.
		fileObject.write( "del layouts\n" )

	## The EditorWidget factory provides access to every single registered subclass of
	# editor, but specific applications may wish to only provide a subset of those
	# editors to the user. This method is used from config files to define the subset
	# of editors to use in the application.
	def registerEditor( self, editorName ) :

		if editorName not in self.__registeredEditors :
			self.__registeredEditors.append( editorName )

	## Deregisters a previously registered editor, this makes it unavailable to the
	# user when creating new layouts.
	def deregisterEditor( self, editorName ) :

		self.__registeredEditors.remove( editorName )

	## Returns the names of all currently registered editors.
	def registeredEditors( self ) :

		return self.__registeredEditors
