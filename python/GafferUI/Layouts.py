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

import collections
import os
import re
import six
import traceback
import weakref

import imath

import IECore

import Gaffer
import GafferUI

## The Layouts class provides a registry of named layouts for use
# in the ScriptWindow. To allow different gaffer applications to
# coexist happily in the same process (for instance to run both
# an asset management app and a shading app inside maya), separate
# sets of layouts are maintained on a per-application basis. Access
# to the layouts for a specific application is provided by the
# Layouts.acquire() method.
class Layouts( object ) :

	__Layout = collections.namedtuple( "__Layout", [ "repr", "persistent"] )

	## Use acquire() in preference to this constructor.
	def __init__( self, applicationRoot ) :

		self.__applicationRoot = weakref.ref( applicationRoot )
		self.__namedLayouts = collections.OrderedDict()
		self.__default = None
		self.__defaultPersistent = False
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
			applicationRoot.__layouts = Layouts( applicationRoot )

		return applicationRoot.__layouts

	## Serialises the passed Editor and stores it using the given name. This
	# layout can then be recreated using the create() method below. If
	# `persistent` is `True`, then the layout will be saved in the application
	# preferences and restored when the application next runs.
	def add( self, name, editor, persistent = False ) :

		if not isinstance( editor, six.string_types ) :
			editor = repr( editor )

		if name.startswith( "user:" ) :
			# Backwards compatibility with old persistent layouts, which
			# were differentiated by being prefixed with "user:".
			persistent = True
			name = name[5:]

		self.__namedLayouts[name] = self.__Layout( editor, persistent )

		if persistent :
			self.__save()

	## Removes a layout previously stored with add().
	def remove( self, name ) :

		l = self.__namedLayouts.pop( name )
		if l.persistent :
			self.__save()

	## Returns a list of the names of currently defined layouts
	def names( self, persistent = None ) :

		return [
			item[0] for item in self.__namedLayouts.items()
			if persistent is None or item[1].persistent == persistent
		]

	## Recreates a previously stored layout for the specified script,
	# returning it in the form of a CompoundEditor.
	def create( self, name, scriptNode ) :

		layout = self.__namedLayouts[name]

		# first try to import the modules the layout needs
		contextDict = { "scriptNode" : scriptNode, "imath" : imath }
		imported = set()
		classNameRegex = re.compile( "[a-zA-Z]*Gaffer[^(,]*\(" )
		for className in classNameRegex.findall( layout.repr ) :
			moduleName = className.partition( "." )[0]
			if moduleName not in imported :
				try :
					exec( "import %s" % moduleName, contextDict, contextDict )
				except( ImportError ) :
					IECore.msg( IECore.MessageHandler.Level.Error, "GafferUI.Layouts", "Failed to load \"{layout}\" layout. {module} is not available.".format( layout=name, module=moduleName ) )
					return GafferUI.CompoundEditor( scriptNode )
				imported.add( moduleName )

		try :
			return eval( layout.repr, contextDict, contextDict )
		except Exception as e :
			traceback.print_exc()
			IECore.msg( IECore.MessageHandler.Level.Error, "GafferUI.Layouts", "Failed to load \"{layout}\" layout. {message}.".format( layout=name, message=e ) )
			return GafferUI.CompoundEditor( scriptNode )

	def setDefault( self, name, persistent = False ) :

		if name == self.__default and persistent == self.__defaultPersistent :
			return

		if name not in self.__namedLayouts :
			raise KeyError( name )

		self.__default = name
		self.__defaultPersistent = persistent
		if persistent :
			self.__save()

	def getDefault( self ) :

		return self.__default

	def createDefault( self, scriptNode ) :

		if self.__default in self.__namedLayouts :
			return self.create( self.__default, scriptNode )
		else :
			return GafferUI.CompoundEditor( scriptNode )

	## The Editor factory provides access to every single registered subclass of
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

	def __save( self ) :

		f = open( os.path.join( self.__applicationRoot().preferencesLocation(), "layouts.py" ), "w" )
		f.write( "# This file was automatically generated by Gaffer.\n" )
		f.write( "# Do not edit this file - it will be overwritten.\n\n" )

		f.write( "import GafferUI\n\n" )
		f.write( "layouts = GafferUI.Layouts.acquire( application )\n" )

		for name, layout in self.__namedLayouts.items() :
			if layout.persistent :
				f.write( "layouts.add( {0}, {1}, persistent = True )\n".format( repr( name ), repr( layout.repr ) ) )

		if self.__defaultPersistent and self.__default in self.__namedLayouts :
			f.write( "layouts.setDefault( {0}, persistent = True )\n".format( repr( self.__default ) ) )
