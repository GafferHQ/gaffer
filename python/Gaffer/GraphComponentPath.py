##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

## \todo We need to emit the changed signal when children are added
# and removed. It would be easiest to do this by having a descendantAddedSignal
# on GraphComponent (otherwise we have to make connections to every child everywhere).
class GraphComponentPath( Gaffer.Path ) :

	def __init__( self, rootComponent, path, root="/", filter=None ) :

		Gaffer.Path.__init__( self, path, root, filter=filter )

		assert( isinstance( rootComponent, Gaffer.GraphComponent ) )

		self.__rootComponent = rootComponent

	def isValid( self, canceller = None ) :

		try :
			self.__graphComponent()
			return True
		except :
			return False

	def isLeaf( self, canceller = None ) :

		return False

	def copy( self ) :

		return GraphComponentPath( self.__rootComponent, self[:], self.root(), self.getFilter() )

	def propertyNames( self, canceller = None ) :

		return Gaffer.Path.propertyNames( self ) + [ "graphComponent:graphComponent" ]

	def property( self, name, canceller = None ) :

		if name == "graphComponent:graphComponent" :
			return self.__graphComponent()
		else :
			return Gaffer.Path.property( self, name )

	def cancellationSubject( self ) :

		if isinstance( self.__rootComponent, Gaffer.ScriptNode ) :
			script = self.__rootComponent
		else :
			script = self.__rootComponent.ancestor( Gaffer.ScriptNode )

		if script is None :
			return None

		# The BackgroundTask cancellation mechanism is plug-centric, but we deal
		# with any kind of GraphComponent. Returning a plug on the script is
		# currently sufficient for any edit to a child of the script to cancel
		# background tasks.
		## \todo Perhaps BackgroundTask cancellation shouldn't only be plug-centric?
		return script["fileName"]

	def _children( self, canceller ) :

		try :
			e = self.__graphComponent()
			return [ GraphComponentPath( self.__rootComponent, self[:] + [ x ], self.root(), self.getFilter() ) for x in e.keys() ]
		except :
			return []

		return []

	def __graphComponent( self ) :

		e = self.__rootComponent
		for p in self :
			e = e[p]

		return e

IECore.registerRunTimeTyped( GraphComponentPath, typeName = "Gaffer::GraphComponentPath" )
