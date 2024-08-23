##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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
import GafferUI
import GafferScene

## Base class to simplify the creation of Editors which operate on ScenePlugs.
class SceneEditor( GafferUI.NodeSetEditor ) :

	## Provides an `in` ScenePlug which defines the scene to be
	#  displayed and/or edited. Pass `numInputs > 1` to the constructor to
	#  instead provide an `in` ArrayPlug to provide multiple scenes.
	class Settings( GafferUI.Editor.Settings ) :

		def __init__( self, numInputs = 1 ) :

			GafferUI.Editor.Settings.__init__( self )

			if numInputs == 1 :
				self["in"] = GafferScene.ScenePlug()
			else :
				self["in"] = Gaffer.ArrayPlug( elementPrototype = GafferScene.ScenePlug(), minSize = numInputs, maxSize = numInputs )

	IECore.registerRunTimeTyped( Settings, typeName = "GafferSceneUI::SceneEditor::Settings" )

	def __init__( self, topLevelWidget, scriptNode, **kw ) :

		GafferUI.NodeSetEditor.__init__( self, topLevelWidget, scriptNode, nodeSet = scriptNode.focusSet(), **kw )

		self.__parentingConnections = {}

	def _updateFromSet( self ) :

		# Find ScenePlugs and connect them to `settings()["in"]`.

		updatedParentingConnections = {}
		inputsToFill = [ self.settings()["in"] ] if isinstance( self.settings()["in"], GafferScene.ScenePlug ) else list( self.settings()["in"].children() )

		with Gaffer.DirtyPropagationScope() :

			for node in self.getNodeSet()[-len(inputsToFill):] :

				outputScenePlug = next(
					( p for p in GafferScene.ScenePlug.RecursiveOutputRange( node ) if not p.getName().startswith( "__" ) ),
					None
				)
				if outputScenePlug is not None :
					inputsToFill.pop( 0 ).setInput( outputScenePlug )
					plugConnection = self.__parentingConnections.get( outputScenePlug )
					if plugConnection is None :
						plugConnection = outputScenePlug.parentChangedSignal().connect(
							Gaffer.WeakMethod( self.__scenePlugParentChanged ), scoped = True
						)
					updatedParentingConnections[outputScenePlug] = plugConnection

				nodeConnections = self.__parentingConnections.get( node )
				if nodeConnections is None :
					nodeConnections = [
						node.childAddedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ), scoped = True ),
						node.childRemovedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ), scoped = True ),
					]
				updatedParentingConnections[node] = nodeConnections

			for unfilledInput in inputsToFill :
				unfilledInput.setInput( None )

		# Note : We reuse existing connections where we can to avoid getting
		# into infinite loops. We are called from the very signals we are
		# connecting to, so if we made _new_ connections then we would be called
		# _again_ for the same invocation of the signal.
		self.__parentingConnections = updatedParentingConnections

		# Called last, because it will call `_titleFormat()`, which depends on
		# the inputs we just created.
		GafferUI.NodeSetEditor._updateFromSet( self )

	def _titleFormat( self ) :

		if isinstance( self.settings()["in"], GafferScene.ScenePlug ) :
			numInputs = 1 if self.settings()["in"].getInput() is not None else 0
		else :
			numInputs = sum( 1 for p in self.settings()["in"] if p.getInput() is not None )

		return GafferUI.NodeSetEditor._titleFormat(
			self,
			_maxNodes = numInputs,
			_reverseNodes = True,
			_ellipsis = False
		)

	def __scenePlugParentChanged( self, plug, newParent ) :

		self._updateFromSet()

	def __childAddedOrRemoved( self, node, child ) :

		if isinstance( child, GafferScene.ScenePlug ) :
			self._updateFromSet()
