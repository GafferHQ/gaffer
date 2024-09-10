##########################################################################
#
#  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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
import GafferScene
import GafferUI
import GafferSceneUI

import IECore
import imath

Gaffer.Metadata.registerNode(

	GafferScene.SetVisualiser,

	"description",
	"""
	Visualises Set membership values by applying a custom shader and coloring
	based on which sets each object belongs to. Membership of more than one set
	is visualised by a stripe pattern.
	""",

	"layout:customWidget:legend:widgetType", "GafferSceneUI.SetVisualiserUI._OutSetsPlugValueWidget",
	"layout:customWidget:legend:section", "Settings.Legend",
	"layout:section:Settings.Legend:collapsed", False,

	plugs = {

		"sets" : [

			"description",
			"""
			A space separated list of sets to consider membership of. This
			supports wild cards, eg: asset:* to allow membership display to
			focus on a specific group of sets. Right-click to insert the name
			of any sets in the input scene.
			""",

			"ui:scene:acceptsSetNames", True
		],

		"includeInherited" : [

			"description",
			"""
			When enabled, objects that inherit Set membership from their parents
			will also be coloured. Disabling this will only color objects that
			are exactly matched by any given Set.
			"""

		],

		"stripeWidth" : [

			"description",
			"""
			The thickness (in pixels) of the stripes used to indicate an object
			is in more than one set.
			"""

		],

		"colorOverrides" : [

			"description",
			"""
			Allows the randomly generated set colors to be overridden by
			specific colors to use for Sets matching the supplied filter. This
			can be a name, or a match string.
			""",

			"layout:section", "Settings.Color Overrides",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:customWidget:footer:widgetType", "GafferSceneUI.SetVisualiserUI._OverridesFooter",
			"layout:customWidget:footer:index", -1

		],

		"colorOverrides.*.name" : [

			"description",
			"""
			Specifies which set or sets to apply the override to. This can be
			a name, or a match string. Right-click to insert the name of any
			set in the input scene.
			""",

			"ui:scene:acceptsSetName", True

		]

	}

)

# PlugValueWidget registrations
#
# NOTE: These are very specific implementations for this use case!
##########################################################################

# A 'legend' style presentation of the colors used for each set
class _OutSetsPlugValueWidget( GafferUI.Widget ) :

	def __init__( self, node, **kw ) :

		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 )
		GafferUI.Widget.__init__( self, self.__column, **kw )

		self.__node = node
		self.__swatches = []

		node.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ) )

		self._update()

	def _update( self ) :

		with self.node().scriptNode().context() :
			sets = self.node()["__outSets"].getValue()

		names = sets["names"]
		colors = sets["colors"]
		numSets = len(names)

		# Try to re-use existing child widgets where we can

		while len( self.__swatches ) < numSets:
			self.__swatches.append( _SetColorLedgendRowWidget() )
		while len( self.__swatches ) > numSets:
			self.__swatches.pop()

		# List in Alphabetical order
		for i in range( numSets ):
			self.__swatches[i].setColorAndLabel( colors[ i ], str(names[ i ]) )

		self.__column[:] = self.__swatches

	@GafferUI.LazyMethod()
	def __updateLazily( self ) :
		self._update()

	def __plugDirtied( self, plug ) :

		if plug == self.node()["__outSets"] :
			self.__updateLazily()

	def node( self ):
		return self.__node

	def context( self ) :
		return self.node().scriptNode().context()

	# We make use of the full width of the editor, and parent this to a new
	# tab so we don't need the built-in label or tool-tips

	def hasLabel( self ) :
		return True

	def getToolTip( self ) :
		return None

# A simple 'Add' button that doesn't show all the data types listed in the
# CompoundDataPlugValueWidget's Add MenuButton.
# @TODO: Support type constraints in CompoundDataPlugValueWidget.
class _OverridesFooter( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.PlugValueWidget.__init__( self, row, plug )

		with row :

			GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

			self.__addButton = GafferUI.Button( image = "plus.png", hasFrame = False )
			self.__addButton.clickedSignal().connect( Gaffer.WeakMethod( self.__addOverride ) )

			GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

	def _updateFromEditable( self ) :

		self.__addButton.setEnabled( self._editable() )

	def __addOverride( self, _ ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().addChild( Gaffer.NameValuePlug( "", imath.Color3f( 1.0 ), True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

# A single-row that holds a Color swatch and a text label
class _SetColorLedgendRowWidget( GafferUI.ListContainer ) :

	def __init__( self, **kw ) :

		GafferUI.ListContainer.__init__( self, GafferUI.ListContainer.Orientation.Horizontal, spacing=4 )

		self.__spacer =	GafferUI.Spacer( imath.V2i( 20, 1 ), imath.V2i( 20 , 1 ) )
		self.addChild( self.__spacer )

		self.__swatch = GafferUI.ColorSwatch()
		# No easy way to manage size at present in GafferUI
		self.__swatch._qtWidget().setFixedWidth( 40 )
		self.__swatch._qtWidget().setFixedHeight( 20 )
		self.addChild( self.__swatch )

		self.__label = GafferUI.Label()
		self.addChild( self.__label )

		# Allow right-click to add an override for the target set
		self.__menu = GafferUI.Menu( Gaffer.WeakMethod( self.__addMenuDefinition ) )
		self.contextMenuSignal().connect( Gaffer.WeakMethod( self.__menu.popup ) )

	def setColorAndLabel( self, color, label ) :

		self.__swatch.setColor( color )
		self.__label.setText( label )

	def __colorOverridesPlug( self ) :

		# We don't want to be storing any plug references here to avoid
		# becoming stale, instead we trust our known widget hierarchy.
		outSetsWidget = self.ancestor( _OutSetsPlugValueWidget )
		return outSetsWidget.node()[ "colorOverrides" ], outSetsWidget.context()

	def __hasExistingOverrideFor( self, name ) :

		plug, context = self.__colorOverridesPlug()
		with context :
			for c in plug.children() :
				if c["name"].getValue() == name:
					return True

		return False

	def __addOverride( self ) :

		targetPlug, _ = self.__colorOverridesPlug()
		if targetPlug:
			with Gaffer.UndoScope( targetPlug.ancestor( Gaffer.ScriptNode ) ) :
				targetPlug.addChild( Gaffer.NameValuePlug( self.__label.getText(), imath.Color3f( 1.0 ), True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
			editor = self.ancestor( GafferUI.NodeUI )
			if editor:
				editor.plugValueWidget( targetPlug ).reveal()

	def __selectMembers( self ) :

		outSetsWidget = self.ancestor( _OutSetsPlugValueWidget )
		inPlug = outSetsWidget.node()[ "in" ]
		with outSetsWidget.context() :
			matcher = inPlug.set( self.__label.getText() ).value
			GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( outSetsWidget.scriptNode(), matcher )

	def __addMenuDefinition( self ) :

		result = IECore.MenuDefinition()
		result.append( "Add Color Override", {
			"command" : Gaffer.WeakMethod( self.__addOverride ),
			"active" : not self.__hasExistingOverrideFor( self.__label.getText() )
		} )
		result.append( "Select Members", {
			"command" : Gaffer.WeakMethod( self.__selectMembers )
		} )
		return result
