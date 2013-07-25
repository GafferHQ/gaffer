##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

import warnings

import Gaffer

class Path( object ) :

	## Paths can be constructed either from a "/slash/separated/string"
	# or a [ "list", "of", "strings" ] relative to a root.
	## \todo Reimplement the class paths in C++, with three distinct
	# constructors :
	#
	# Path( FilterPtr filter = 0 ) // empty path
	# Path( const std::string &path, FilterPtr filter = 0 )
	# Path( const std::vector<InternedString> &path, const std::string &root="/", FilterPtr filter = 0 )
	def __init__( self, path=None, root="/", filter=None ) :
	
		assert( isinstance( root, basestring ) )
	
		self.__items = []
		self.__root = ""
		
		if isinstance( path, basestring ) :
			
			self.setFromString( path )
			
		elif path is not None :
		
			self.__root = root
			for p in path :
					
				self.__checkElement( p )		
				self.__items.append( p )
				
		self.__filter = None
		self.setFilter( filter )
	
	## Returns the root of the path - this will be "/" for absolute
	# paths and "" for relative paths.
	def root( self ) :
	
		return self.__root
	
	## Returns true if this path is empty.
	def isEmpty( self ) :
	
		return not len( self ) and not self.__root
									
	## Returns true if this path is valid - ie references something
	# which actually exists.
	def isValid( self ) :
		
		return not self.isEmpty()
	
	## If the path is valid, returns a dictionary of information about what
	# the path points to. If the path is not valid, returns None. The contents
	# of the dictionary depends on the type of Path. Subclasses should call
	# their base class' implementation first, and then add additional information
	# to the dictionary returned.
	def info( self ) :
	
		if not self.isValid() :
			return None
			
		result = {}
		result["name"] = self[-1] if len( self ) else ""
		result["fullName"] = str( self )
		
		return result
	
	## Returns true if this path can never have child Paths.
	def isLeaf( self ) :
	
		raise NotImplementedError
	
	## Returns the parent of this path, or None if the path
	# has no parent (is the root).
	def parent( self ) :
	
		if not self.__items :
			return None
			
		parent = self.copy()
		del parent[-1]
		
		return parent
	
	## Returns a list of Path instances representing all
	# the children of this path. Note that an empty list may
	# be returned even if isLeaf() is False.
	def children( self ) :
	
		c = self._children()
			
		if self.__filter is not None :
			c = self.__filter.filter( c )
			
		return c	
	
	## The subclass specific part of children(). This must be implemented
	# by subclasses to return a list of children - filtering will be applied
	# in the children() method so can be ignored by the derived classes.	
	def _children( self ) :
	
		raise NotImplementedError
	
	def setFilter( self, filter ) :
	
		if filter is self.__filter :
			return
			
		self.__filter = filter
		if self.__filter is not None :
			self.__filterChangedConnection = self.__filter.changedSignal().connect( Gaffer.WeakMethod( self.__filterChanged ) )
		else :
			self.__filterChangedConnection = None
			
		self.__emitChangedSignal()
		
	def getFilter( self ) :
	
		return self.__filter
	
	## \deprecated
	# Use setFilter() instead. If you wish to use more than
	# one filter then use a CompoundPathFilter.
	def addFilter( self, pathFilter ) :
	
		warnings.warn( "Path.addFilter() is deprecated, use Path.setFilter() instead. If you wish to use more than one filter then use a CompoundPathFilter.", DeprecationWarning, 2 )		
		
		if not isinstance( self.__filter, Gaffer.CompoundPathFilter ) :
			self.__filter = Gaffer.CompoundPathFilter()	
			
		self.__filter.addFilter( pathFilter )
		
	## \deprecated
	# Use setFilter() instead. If you wish to use more than
	# one filter then use a CompoundPathFilter.
	def removeFilter( self, pathFilter ) :
	
		warnings.warn( "Path.removeFilter() is deprecated, use Path.setFilter() instead. If you wish to use more than one filter then use a CompoundPathFilter.", DeprecationWarning, 2 )		

		self.__filter.removeFilter( pathFilter )

	def pathChangedSignal( self ) :
	
		if not hasattr( self, "_Path__pathChangedSignal" ) :
			self.__pathChangedSignal = Gaffer.Signal1()
			
		return self.__pathChangedSignal

	## Sets the path root and items from the other
	# path, leaving the current filter intact.
	def setFromPath( self, path ) :
	
		if path.__items == self.__items and path.__root == self.__root :
			return
			
		self.__items = path.__items[:]
		self.__root = path.__root
		self.__emitChangedSignal()
		
	## Sets the path root and items from a "/"
	# separated string.
	def setFromString( self, path ) :
		
		newItems = [ x for x in path.split( "/" ) if x ]
		newRoot = "/" if path and path[0]=='/' else ""
				
		if newItems != self.__items or newRoot != self.__root :
			self.__items = newItems
			self.__root = newRoot
			self.__emitChangedSignal()
			
		return self
	
	def copy( self ) :
	
		c = self.__class__( self.__items, root=self.__root )
		c.setFilter( self.__filter )
		
		return c
		
	def append( self, element ) :
	
		self.__checkElement( element )
		self.__items.append( element )
		self.__emitChangedSignal()
		
		return self
	
	def truncateUntilValid( self ) :
	
		changed = False
		while len( self.__items ) and not self.isValid() :
			del self.__items[-1]
			changed = True
			
		if changed :
			self.__emitChangedSignal()
		
		return self
		
	def __len__( self ) :
	
		return len( self.__items )

	def __str__( self ) :
				
		return self.__root + "/".join( self.__items )
			
	def __setitem__( self, index, name ) :
	
		if isinstance( index, slice ) :
			for n in name :
				self.__checkElement( n )
		else :
			self.__checkElement( name )
		
		prev = self.__items[index]
				
		self.__items.__setitem__( index, name )
		
		if prev!=name :
			self.__emitChangedSignal()
		
	def __getitem__( self, index ) :
	
		return self.__items.__getitem__( index )

	def __delitem__( self, index ) :
	
		self.__items.__delitem__( index )
		self.__emitChangedSignal()
		
	def __eq__( self, other ) :
	
		if not isinstance( other, Path ) :
			return False
			
		return self.__items == other.__items and self.__root == other.__root
		
	def __ne__( self, other ) :
	
		if not isinstance( other, Path ) :
			return True
			
		return self.__items != other.__items	
			
	def __checkElement( self, element ) :
	
		if not isinstance( element, basestring ) :
			raise ValueError( "Path elements must be strings." )
				
		if "/" in element :
			raise ValueError( "Path element contains \"/\"." )
		
		if element=="" :
			raise ValueError( "Path element is empty." )	

	def __emitChangedSignal( self ) :
		
		if hasattr( self, "_Path__pathChangedSignal" ) :
			self.__pathChangedSignal( self )
			
	def __filterChanged( self, filter ) :
	
		assert( filter is self.__filter )
		
		self.__emitChangedSignal()
		
	def __repr__( self ) :
	
		return "%s( '%s' )" % ( self.__class__.__name__, str( self ) )
