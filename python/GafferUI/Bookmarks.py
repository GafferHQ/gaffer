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

import IECore

import Gaffer
import GafferUI

## The Bookmarks class provides a registry of named locations for use
# in Path UIs. To allow different gaffer applications to coexist in the
# same process, separate bookmarks are maintained per application.
class Bookmarks :
	
	## Use acquire() in preference to this constructor.
	def __init__( self, applicationRoot, pathType, category ) :
	
		self.__applicationRoot = weakref.ref( applicationRoot )
		self.__pathType = pathType
		self.__category = category
		
	## Acquires a set of bookmarks for the specified application. Bookmarks are
	# grouped according to the type of path they can be applied to and to an
	# arbitrary category. The None category is special - bookmarks added to this
	# category are available in all categories with the same path type.
	@classmethod
	def acquire( cls, applicationOrApplicationRoot, pathType=Gaffer.FileSystemPath, category=None ) :
	
		if isinstance( applicationOrApplicationRoot, Gaffer.Application ) :
			applicationRoot = applicationOrApplicationRoot.root()
		else :
			assert( isinstance( applicationOrApplicationRoot, Gaffer.ApplicationRoot ) )
			applicationRoot = applicationOrApplicationRoot
	
		return Bookmarks( applicationRoot, pathType, category )
		
	## Adds a bookmark. If persistent is True, then the bookmark
	# will be saved in the application preferences and restored
	# when the application next runs. The path passed may either
	# be a string or a callable which takes the optional forWidget
	# argument passed to get() and returns a string - this latter
	# option makes it possible to define context sensitive bookmarks.
	def add( self, name, path, persistent=False ) :

		assert( isinstance( path, basestring ) or ( callable( path ) and not persistent ) )

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
	
	## Adds a recently visited location to the bookmarks.
	# Recent locations are prefixed with "Recent/", are always
	# persistent, and are recycled so only the latest few are available.
	def addRecent( self, path ) :
	
		assert( isinstance( path, basestring ) )
	
		name = "Recent/" + path.rpartition( "/" )[-1]
	
		names = [ n for n in self.names() if n.startswith( "Recent/" ) ]
		if name in names :
			self.remove( name )
			names.remove( name )
		
		while len( names ) > 5 :
			self.remove( names[0] )
			del names[0]
		
		self.add( name, path, persistent=True )
		
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

		f = open( os.path.join( self.__applicationRoot().preferencesLocation(), "bookmarks.py" ), "w" )
		f.write( "# This file was automatically generated by Gaffer.\n" )
		f.write( "# Do not edit this file - it will be overwritten.\n\n" )

		f.write( "import Gaffer\n" )
		f.write( "import GafferUI\n" )
			
		f.write( "\n" )
	
		for key, value in self.__applicationRoot().__bookmarks.items() :
			acquired = False
			for b in value :
				if not b.persistent :
					continue
				if not acquired :
					f.write(
						"bookmarks = GafferUI.Bookmarks.acquire( application, %s, %s )\n" %
						( Gaffer.Serialisation.classPath( key[0] ).rpartition( "." )[0], repr( key[1] ) )
					)
					acquired = True
				f.write( "bookmarks.add( %s, %s, persistent=True )\n" % ( repr( b.name ), repr( b.path ) ) )
	