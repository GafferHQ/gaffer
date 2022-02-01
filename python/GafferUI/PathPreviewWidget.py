##########################################################################
#
#  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferUI

## This Widget defines a base class for all Widgets which are able to
# preview the contents of a path in some way.
class PathPreviewWidget( GafferUI.Widget ) :

	def __init__( self, topLevelWidget, path, **kw ) :

		GafferUI.Widget.__init__( self, topLevelWidget, **kw )

		self.__path = None
		self.setPath( path )

	def setPath( self, path ) :

		assert( isinstance( path, Gaffer.Path ) )

		if path.isSame( self.__path ) :
			return

		prevPath = self.__path
		self.__path = path
		self.__currentPath = None
		self.__pathChangedConnection = self.__path.pathChangedSignal().connect(
			Gaffer.WeakMethod( self.__pathChanged ), scoped = True
		)

		if prevPath != None :
			# we don't call _updateFromPath when setPath is called from __init__,
			# as otherwise all the derived classes have to deal with not yet being
			# constructed in their implementations.
			self._updateFromPath()

	def getPath( self ) :

		return self.__path

	## Must be implemented by subclasses, to return True
	# if this Widget is currently displaying something useful,
	# and False if not.
	def isValid( self ) :

		raise NotImplementedError

	## Must be implemented by subclasses
	def _updateFromPath( self ) :

		raise NotImplementedError

	def __pathChanged( self, path ) :

		assert( path.isSame( self.__path ) )

		if str( path ) == self.__currentPath :
			return

		self._updateFromPath()

		self.__currentPath = str( path )

	@classmethod
	def types( cls ) :

		return [ x[0] for x in cls.__namesToCreators ]

	@classmethod
	def create( cls, name, path ) :

		for creatorName, creator in cls.__namesToCreators :
			if name == creatorName :
				return creator( path )

		return None

	@classmethod
	def registerType( cls, name, creator ) :

		cls.__namesToCreators.append( ( name, creator ) )

	__namesToCreators = []
