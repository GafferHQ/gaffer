##########################################################################
#
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

import os
import weakref
import six

import IECore

import Gaffer
import GafferUI

## The Bookmarks class provides a registry of named locations for use
# in Path UIs. To allow different gaffer applications to coexist in the
# same process, separate bookmarks are maintained per application.
class Bookmarks( object ) :

	## Use acquire() in preference to this constructor.
	def __init__( self, applicationRoot, pathType, category ) :

		self.__applicationRoot = weakref.ref( applicationRoot )
		self.__pathType = pathType
		self.__category = category

	## Acquires a set of bookmarks for the specified target. Bookmarks are
	# grouped according to the type of path they can be applied to and to an
	# arbitrary category. The None category is special - bookmarks added to this
	# category are available in all categories with the same path type.
	#
	# Bookmarks are stored on a per-application basis but target can be any
	# of the following :
	#
	#  - An instance of Gaffer.Application
	#  - An instance of Gaffer.ApplicationRoot
	#  - An instance of Gaffer.GraphComponent. In this case, the bookmarks
	#     of the ApplicationRoot ancestor of target are returned, with None
	#     being returned in the absence of such an ancestor.
	#  - An of instance of GafferUI.Widget. In this case, an instance of
	#     of Editor or ScriptWindow will be sought, and the application
	#     determined using the attached script. This too may return None if
	#     no application can be found.
	#  - A tuple or list, containing potential targets in the above form. Each
	#     is tried in turn until bookmarks are found - this is useful when both
	#     a GraphComponent and a Widget are available, but it is not known that
	#     they each have a suitable ancestor for bookmark acquisition.
	#
	@classmethod
	def acquire( cls, target, pathType=Gaffer.FileSystemPath, category=None ) :

		if isinstance( target, ( tuple, list ) ) :
			for t in target :
				result = cls.acquire( t, pathType, category )
				if result is not None :
					return result
			return None

		if isinstance( target, Gaffer.Application ) :
			applicationRoot = target.root()
		elif isinstance( target, Gaffer.ApplicationRoot ) :
			applicationRoot = target
		elif isinstance( target, Gaffer.GraphComponent ) :
			applicationRoot = target.ancestor( Gaffer.ApplicationRoot )
		else :
			assert( isinstance( target, GafferUI.Widget ) )
			scriptWidget = None
			if isinstance( target, ( GafferUI.Editor, GafferUI.ScriptWindow ) ) :
				scriptWidget = target
			else :
				scriptWidget = target.ancestor( GafferUI.Editor )
				if scriptWidget is None :
					scriptWidget = target.ancestor( GafferUI.ScriptWindow )

			if scriptWidget is None :
				# needed to find bookmarks for floating op windows
				# in the browser app. ideally we'd have a more general
				# mechanism for finding scriptWidget in the closest
				# descendant-of-an-ancestor.
				window = target
				while window is not None :
					window = window.ancestor( GafferUI.Window )
					if window is not None and isinstance( window.getChild(), GafferUI.Editor ) :
						scriptWidget = window.getChild()
						break

			if scriptWidget is not None :
				applicationRoot = scriptWidget.scriptNode().ancestor( Gaffer.ApplicationRoot )
			else :
				applicationRoot = None

		if applicationRoot is None :
			return None

		return Bookmarks( applicationRoot, pathType, category )

	## Adds a bookmark. If persistent is True, then the bookmark
	# will be saved in the application preferences and restored
	# when the application next runs. The path passed may either
	# be a string or a callable which takes the optional forWidget
	# argument passed to get() and returns a string - this latter
	# option makes it possible to define context sensitive bookmarks.
	def add( self, name, path, persistent=False ) :

		assert( isinstance( path, six.string_types ) or ( callable( path ) and not persistent ) )

		# backwards compatibility with old mechanism for storing recents -
		# convert to new form.
		if name.startswith( "Recent/" ) :
			self.addRecent( path )
			return

		s = self.__storage( self.__category )
		try :
			# find existing bookmark
			b = next( x for x in s if x.name == name )
		except StopIteration :
			# add new one if none exists
			b = IECore.Struct()
			s.append( b )

		# update bookmark
		b.name = name
		b.path = path
		b.persistent = persistent

		if persistent :
			self.__save()

	## Removes a bookmark previously stored with add().
	def remove( self, name ) :

		for s in [
			self.__storage( self.__category ),
			self.__storage( None )
		] :
			for i, b in enumerate( s ) :
				if b.name == name :
					del s[i]
					if b.persistent :
						self.__save()
					return

		raise KeyError( name )

	## Returns a list of the names of currently defined bookmarks.
	def names( self, persistent=None ) :

		u = set()
		result = []

		for s in [
			self.__storage( None ),
			self.__storage( self.__category ),
		] :
			for b in s :
				if persistent is not None and b.persistent != persistent :
					continue
				if b.name.startswith( "__" ) :
					continue
				if b.name not in u :
					result.append( b.name )
					u.add( b.name )

		return result

	## Returns the named bookmark as a string. The optional
	# forWidget argument may be specified to provide a context
	# in which dynamic (callable) bookmarks may compute their
	# result.
	def get( self, name, forWidget=None ) :

		for s in [
			self.__storage( self.__category ),
			self.__storage( None ),
		] :
			for b in s :
				if b.name == name :
					if callable( b.path ) :
						return b.path( forWidget )
					else :
						return b.path

		raise KeyError( name )

	## Adds a recently visited location to the bookmarks.
	# Recent locations are always persistent, and are recycled
	# so only the latest few are available. Recent bookmarks are
	# not returned by names() or get(), but are instead accessed
	# with recents().
	def addRecent( self, path ) :

		assert( isinstance( path, six.string_types ) )

		name = "__recent:" + path

		# first remove any recent items that match this one,
		# and remove old items to make room for the new one
		# if necessary. we only do this for the category storage
		# because we don't want to flush recents from the general
		# storage if a particular category is used heavily.

		names = [ x.name for x in self.__storage( self.__category ) if x.name.startswith( "__recent:" ) ]
		if name in names :
			self.remove( name )
			names.remove( name )

		while len( names ) > 5 :
			self.remove( names[0] )
			del names[0]

		# now add on the new bookmark

		self.add( name, path, persistent=True )

	## Removes a recently visited location from the bookmarks.
	def removeRecent( self, path ) :

		self.remove( "__recent:" + path )

	## Returns a list of strings specifying the location of
	# the bookmarks added with addRecent().
	def recents( self ) :

		u = set()
		result = []

		for s in [
			self.__storage( None ),
			self.__storage( self.__category ),
		] :
			for b in s :
				if b.name.startswith( "__recent:" ) :
					if b.path not in u :
						result.append( b.path )
						u.add( b.path )

		return result

	## Sets a default location which can be used when no
	# information has been provided as to where to start
	# browsing. Default locations are not persistent.
	def setDefault( self, path ) :

		self.add( "__default", path )

	def getDefault( self, forWidget=None ) :

		try :
			return self.get( "__default", forWidget )
		except KeyError :
			return "/"

	def __storage( self, category ) :

		a = self.__applicationRoot()
		try :
			b = a.__bookmarks
		except :
			a.__bookmarks = {}
			b = a.__bookmarks

		return b.setdefault( ( self.__pathType, category ), [] )

	def __save( self ) :

		bookmarkSerializations = [ "import GafferUI", "" ]
		for key, value in self.__applicationRoot().__bookmarks.items() :
			acquired = False
			for b in value :
				if not b.persistent :
					continue
				if not acquired :
					bookmarkSerializations.append(
						"bookmarks = GafferUI.Bookmarks.acquire( application, %s, %s )" %
						( Gaffer.Serialisation.classPath( key[0] ), repr( key[1] ) )
					)
					acquired = True
				if b.name.startswith( "__recent:" ) :
					bookmarkSerializations.append( "bookmarks.addRecent( %s )" % repr( b.path ) )
				else :
					bookmarkSerializations.append( "bookmarks.add( %s, %s, persistent=True )" % ( repr( b.name ), repr( b.path ) ) )

		serialization  = "# This file was automatically generated by Gaffer.\n"
		serialization += "# Do not edit this file - it will be overwritten.\n"
		serialization += "\n"
		serialization += "import Gaffer\n"
		serialization += "\n"

		# Some apps have both gui and no-gui modes, so we need to protect importing UI modules.
		# Since we don't have an official mechanism to detect the modes, we're just hardcoding
		# a list of known apps for the time being.
		if self.__applicationRoot().getName() in ( "op", "dispatch" ) :
			serialization += "if application['gui'].getTypedValue() :\n\n"
			serialization += "\t" + "\n\t".join( bookmarkSerializations )
		else :
			serialization += "\n".join( bookmarkSerializations )

		with open( os.path.join( self.__applicationRoot().preferencesLocation(), "bookmarks.py" ), "w" ) as f :
			f.write( serialization )
