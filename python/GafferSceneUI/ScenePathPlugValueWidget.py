##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
import GafferImage
import GafferScene

# Supported metadata :
#
# - `scenePathPlugValueWidget:scene` : The name of a plug on the same node, used to
#   provide a scene browser for path selection. Also accepts a space-separated list
#   of names, taking the first plug with an input connection.
# - `scenePathPlugValueWidget:setNames` : Limits the scene browser to include only
#   locations in the specified sets.
# - `scenePathPlugValueWidget:setsLabel` : A UI label for turning on and off the
#   set filter.
class ScenePathPlugValueWidget( GafferUI.PathPlugValueWidget ) :

	def __init__( self, plug, path = None, **kw ) :

		if path is None :

			filter = None
			sets = Gaffer.Metadata.value( plug, "scenePathPlugValueWidget:setNames" )
			if sets :
				filter = GafferScene.ScenePath.createStandardFilter(
					list( sets ),
					Gaffer.Metadata.value( plug, "scenePathPlugValueWidget:setsLabel" )
				)

			path = GafferScene.ScenePath(
				None,
				plug.node().scriptNode().context(),
				"/",
				filter = filter
			)

		GafferUI.PathPlugValueWidget.__init__( self, plug, path, **kw )

	def _auxiliaryPlugs( self, plug ) :

		scenePlugNames = Gaffer.Metadata.value( plug, "scenePathPlugValueWidget:scene" ) or "in"
		return [
			plug.node().descendant( n )
			for n in scenePlugNames.split()
			if isinstance( plug.node().descendant( n ), GafferScene.ScenePlug )
		]

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		values = GafferUI.PathPlugValueWidget._valuesForUpdate( plugs, auxiliaryPlugs )

		result = []
		for value, scenePlugs in zip( values, auxiliaryPlugs ) :

			# Find the first ScenePlug with an input, falling back to the last
			# one in the list.
			scenePlug = None
			for scenePlug in scenePlugs :
				if scenePlug.getInput() :
					break

			result.append( {
				"value" : value,
				"scenePlug" : scenePlug,
			} )

		return result

	def _updateFromValues( self, values, exception ) :

		GafferUI.PathPlugValueWidget._updateFromValues(
			self, [ v["value"] for v in values ], exception
		)

		scenePlug = next( ( v["scenePlug"] for v in values if v["scenePlug"] is not None ), None )
		if scenePlug is not None :
			self.path().setScene( scenePlug )
			self.__focusChangedConnection = None
		else :
			# The `_auxiliaryPlugs()` search doesn't work well for ShaderNodes,
			# since they don't have ScenePlug inputs. We _could_ traverse outputs
			# from the shader looking for a ShaderAssignment node to get a ScenePlug
			# from. But this wouldn't be useful if the scene hierarchy was
			# manipulated downstream of the ShaderAssignment as shaders need the
			# final paths as seen by the renderer. So instead we use the focus node, as
			# it is more likely to be pointed at the final render node.
			self.path().setScene( self.__scenePlugFromFocus() )
			self.__focusChangedConnection = self.getPlug().ancestor( Gaffer.ScriptNode ).focusChangedSignal().connect(
				Gaffer.WeakMethod( self.__focusChanged ), scoped = True
			)

	def _pathChooserDialogue( self ) :

		dialogue = GafferUI.PathPlugValueWidget._pathChooserDialogue( self )

		# Unsorted tree view with only a name column - like the HierarchyView.
		dialogue.pathChooserWidget().pathListingWidget().setDisplayMode( GafferUI.PathListingWidget.DisplayMode.Tree )
		dialogue.pathChooserWidget().pathListingWidget().setColumns( ( GafferUI.PathListingWidget.defaultNameColumn, ) )
		dialogue.pathChooserWidget().pathListingWidget().setSortable( False )

		# View relative to the root, rather than the current location.
		## \todo The save/restore of pathNames is to work around the PathChooserWidget
		# truncating the path when the root directory changes. I don't think that
		# behaviour makes sense in tree view mode, so we should probably fix it there.
		dirPath = dialogue.pathChooserWidget().directoryPathWidget().getPath()
		if len( dirPath ) :
			path = dialogue.pathChooserWidget().pathWidget().getPath()
			pathNames = path[:]
			del dirPath[:]
			path[:] = pathNames

		return dialogue

	def __scenePlugFromFocus( self ) :

		focusNode = self.getPlug().ancestor( Gaffer.ScriptNode ).getFocus()
		if focusNode is not None :
			outputScene = next( GafferScene.ScenePlug.RecursiveOutputRange( focusNode ), None )
			if outputScene is not None :
				return outputScene
			outputImage = next( GafferImage.ImagePlug.RecursiveOutputRange( focusNode ), None )
			if outputImage is not None :
				return GafferScene.SceneAlgo.sourceScene( outputImage )

	def __focusChanged( self, scriptNode, node ) :

		scenePlug = self.__scenePlugFromFocus()
		if scenePlug is not None :
			self.path().setScene( scenePlug )
