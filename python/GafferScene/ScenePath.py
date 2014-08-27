##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import IECore

import Gaffer
import GafferScene

class ScenePath( Gaffer.Path ) :

	def __init__( self, scenePlug, context, path, root="/", filter=None ) :

		Gaffer.Path.__init__( self, path, root, filter=filter )

		assert( isinstance( scenePlug, GafferScene.ScenePlug ) )

		self.__scenePlug = scenePlug
		self.__plugDirtiedConnection = None

		self.__context = None
		self.setContext( context )

	def isValid( self ) :

		if not Gaffer.Path.isValid( self ) :
			return False

		with self.__context :
			path = IECore.InternedStringVectorData()
			for p in self :
				childNames = self.__scenePlug.childNames( path )
				if p not in childNames :
					return False
				path.append( p )

		return True

	def info( self ) :

		result = Gaffer.Path.info( self )
		if result is None :
			return None

		return result

	def isLeaf( self ) :

		# any part of the scene could get children at any time
		return False

	def _children( self ) :

		childNames = None
		with self.__context :
			with IECore.IgnoredExceptions( Exception ) :
				childNames = self.__scenePlug.childNames( str( self ) )

		if childNames is None :
			return []

		return [ ScenePath( self.__scenePlug, self.__context, self[:] + [ x.value() ], self.root() ) for x in childNames ]

	def copy( self ) :

		return ScenePath( self.__scenePlug, self.__context, self[:], self.root(), self.getFilter() )

	def setContext( self, context ) :

		if context is self.__context :
			return

		self.__context = context
		self.__contextChangedConnection = self.__context.changedSignal().connect( Gaffer.WeakMethod( self.__contextChanged ) )
		self._emitPathChanged()

	def getContext( self ) :

		return self.__context

	def pathChangedSignal( self ) :

		if self.__plugDirtiedConnection is None :
			self.__plugDirtiedConnection = self.__scenePlug.node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ) )

		return Gaffer.Path.pathChangedSignal( self )

	def __contextChanged( self, context, key ) :

		if not key.startswith( "ui:" ) :
			self._emitPathChanged()

	def __plugDirtied( self, plug ) :

		# only the childNames plug actually affects us right now,
		# but if in the future we start using the other plugs in
		# info() we'll need to take that into account here.
		if plug.isSame( self.__scenePlug["childNames"] ) :
			self._emitPathChanged()

