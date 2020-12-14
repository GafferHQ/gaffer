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

import imath
import inspect
import IECore
import Gaffer
import GafferUI
import GafferScene

# Similar to CompoundDataPlugValueWidget, but different enough that the code can't be shared
class _ContextVariableListWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__column = GafferUI.ListContainer( spacing = 6 )

		GafferUI.PlugValueWidget.__init__( self, self.__column, plug, **kw )

		with self.__column :
			_ColumnHeadings( [ "Primitive Variables", "Quantize", "Variations" ] )

			self.__layout = GafferUI.PlugLayout( plug )

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal ) as self.__editRow :

				GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

				GafferUI.Button( image = "plus.png", hasFrame = False ).clickedSignal().connect( Gaffer.WeakMethod( self.__addItem ), scoped = False )

				GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

	def hasLabel( self ) :

		return True

	def setPlug( self, plug ) :

		GafferUI.PlugValueWidget.setPlug( self, plug )

		self.__layout = GafferUI.PlugLayout( plug )
		self.__column[0] = self.__layout

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )

		self.__layout.setReadOnly( readOnly )

	def childPlugValueWidget( self, childPlug ) :

		return self.__layout.plugValueWidget( childPlug )

	def __addItem( self, button ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().addChild( GafferScene.Instancer.ContextVariablePlug( "context", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

class _ContextVariableWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, overrideName = None ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__row, plug )

		with self.__row:
			GafferUI.StringPlugValueWidget( self.getPlug()["name"] ).textWidget()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )

			GafferUI.BoolPlugValueWidget( self.getPlug()["enabled"],
				displayMode = GafferUI.BoolWidget.DisplayMode.Switch
			)

			GafferUI.PlugValueWidget.create( self.getPlug()["quantize"] )
			toolTipPrefix = "Number of unique values of this context variable, which contribute to the total number of evaluations of the `prototypes` scene."
			if overrideName:
				_VariationsPlugValueWidget( self.getPlug().node()["variations"], overrideName, "", toolTipPrefix )
			else:
				_VariationsPlugValueWidget( self.getPlug().node()["variations"], self.getPlug()["name"], "", toolTipPrefix )

		self._updateFromPlugs()

	def setPlugs( self, plugs ) :

		GafferUI.PlugValueWidget.setPlugs( self, plugs )

		self.__row[0].setPlugs( plugs["name"] )
		self.__row[1].setPlugs( plugs["enabled"] )
		self.__row[2].setPlugs( plugs["quantize"] )

	def hasLabel( self ) :

		return True

	def childPlugValueWidget( self, childPlug ) :

		for w in self.__row :
			if childPlug in w.getPlugs() :
				return w

		return None

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )

		for w in self.__row :
			w.setReadOnly( readOnly )

	def _updateFromPlugs( self ) :

		with self.getContext() :
			enabled = self.getPlug()["enabled"].getValue()
			self.__row[0].setEnabled( enabled )
			self.__row[2].setEnabled( enabled )

GafferUI.PlugValueWidget.registerType( GafferScene.Instancer.ContextVariablePlug, _ContextVariableWidget )

class _VariationsPlugValueWidget( GafferUI.PlugValueWidget ) :

	# The variations plug returns a count for each context variable, and a total.  This plug can
	# display any one of these counts - which to display is selected by the "contextName" argument,
	# which can be either a string literal, or a String plug which will be evaluated to find the
	# name to access within the variations plug output
	def __init__( self, plug, contextName, label, toolTipPrefix, **kw ) :

		toolTip = toolTipPrefix + "  " + inspect.cleandoc(
			"""
			Varying the context requires extra evaluations of the `prototypes` scene, and can
			dramatically increase the cost of the Instancer.

			Note that variations are measured across all locations in the scene where the instancer is filtered.
			"""
		)

		l = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4, toolTip = toolTip )

		GafferUI.PlugValueWidget.__init__( self, l, plug, **kw )


		if isinstance( contextName, Gaffer.StringPlug ):
			self.contextName = None
			self.contextNamePlug = contextName
			self.contextNamePlug.node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__namePlugDirtied ), scoped = False )
		else:
			self.contextName = contextName
			self.contextNamePlug = None

		with l :
			GafferUI.Spacer( imath.V2i( 0 ), preferredSize = imath.V2i( 0 ) )
			if label :
				GafferUI.Label( "<h4>%s</h4>" % label, toolTip = toolTip )
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 2, borderWidth = 3 ) as h :
				h._qtWidget().setObjectName( "gafferVariationCount" )
				self.__busyWidget = GafferUI.BusyWidget( size = 14 )
				self.__countLabel = GafferUI.Label( horizontalAlignment = GafferUI.HorizontalAlignment.Right, toolTip = toolTip )
				self.__countLabel._qtWidget().setMinimumWidth( 90 )

		self.__updateLabel( -1 )
		self._updateFromPlug()

	def setPlugs( self, plugs ) :
		# VariationsPlugValueWidget is a special widget that requires both the plug and contextName
		# to be set in the constructor.  Does not support setPlugs.
		raise NotImplementedError

	def hasLabel( self ) :
		return True

	def __namePlugDirtied( self, plug ) :

		if plug == self.contextNamePlug :
			self._updateFromPlug()

	def _updateFromPlug( self ) :

		self.__updateLazily()

	@GafferUI.LazyMethod()
	def __updateLazily( self ) :

		with self.getContext() :
			self.__updateInBackground()

	@GafferUI.BackgroundMethod()
	def __updateInBackground( self ) :

		resultDict = self.getPlug().getValue()

		contextName = ""
		if self.contextNamePlug:
			contextName = self.contextNamePlug.getValue()

			if contextName == "":
				return -1
		else:
			contextName = self.contextName

		if contextName in resultDict:
			# Success. We have valid infomation to display.
			return resultDict[contextName].value

		# Could be that this variable is disabled
		return -1

	@__updateInBackground.preCall
	def __updateInBackgroundPreCall( self ) :

		self.__updateLabel( -1 )
		self.__busyWidget.setBusy( True )

	@__updateInBackground.postCall
	def __updateInBackgroundPostCall( self, backgroundResult ) :

		if isinstance( backgroundResult, IECore.Cancelled ) :
			# Cancellation. This could be due to any of the
			# following :
			#
			# - This widget being hidden.
			# - A graph edit that will affect the result and will have
			#   triggered a call to _updateFromPlug().
			# - A graph edit that won't trigger a call to _updateFromPlug().
			#
			# LazyMethod takes care of all this for us. If we're hidden,
			# it waits till we're visible. If `updateFromPlug()` has already
			# called `__updateLazily()`, our call will just replace the
			# pending call.
			self.__updateLazily()
			return
		elif isinstance( backgroundResult, Exception ) :
			# Computation error. This will be reported elsewhere
			# in the UI.
			self.__updateLabel( -1 )
		else :
			self.__updateLabel( backgroundResult )

		self.__busyWidget.setBusy( False )

	def __updateLabel( self, count ) :
		self.__countLabel.setText( str(count) + " " if count >= 0 else " " )


def _variationsPlugValueWidgetWidth() :
	# Size of the visible part of the _VariationsPlugValueWidget
	# the busy widget, plus a couple of border widths
	return 112

class _ColumnHeadings( GafferUI.ListContainer ):

	def __init__( self, headings, toolTipOverride = "" ) :
		GafferUI.ListContainer.__init__( self, GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		with self:
			GafferUI.Label( "<h4><b>" + headings[0] + "</b></h4>", toolTip = toolTipOverride )._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )
			GafferUI.Spacer( imath.V2i( 25, 2 ) ) # approximate width of a BoolWidget Switch
			self.addChild( GafferUI.Label( "<h4><b>" + headings[1] + "</b></h4>", toolTip = toolTipOverride ), expand = True, horizontalAlignment=GafferUI.HorizontalAlignment.Left )
			GafferUI.Label( "<h4><b>" + headings[2] + "</b></h4>", toolTip = toolTipOverride )._qtWidget().setFixedWidth( _variationsPlugValueWidgetWidth() )

# Would be really nice if we could specify constructor arguments for widgets in the metadata,
# so we didn't need to declare specializations for different arguments

_VariationSpacer = lambda node : GafferUI.Spacer( imath.V2i( _variationsPlugValueWidgetWidth(), 1 ), imath.V2i( _variationsPlugValueWidgetWidth(), 1 ) )

_SeedColumnHeadings = lambda node : _ColumnHeadings( ["Seed", "", "Variations"], toolTipOverride = inspect.cleandoc(
	"""
	# Seed

	Creates a seed context variable based on the id primvar or point index.  This hashes the point id
	to create a persistent integer for each instance.  The context variable is available to the upstream
	prototypes network.
	"""
) )

_TimeOffsetColumnHeadings = lambda node : _ColumnHeadings( [ "Time Offset", "Quantize", "Variations" ], toolTipOverride = inspect.cleandoc(
	"""
	# Time Offset

	Modify the current time when evaluating the prototypes network, by adding a primvar.
	"""
) )
_SectionSpacer = lambda node : GafferUI.Spacer( imath.V2i( 1, 5 ), imath.V2i( 1, 5 ) )
_SeedCountSpacer = lambda node : GafferUI.Spacer( imath.V2i( 0 ), imath.V2i( 999999, 0 ) )
_SeedCountWidget = lambda node : _VariationsPlugValueWidget( node["variations"], node["seedVariable"], label = "",
	toolTipPrefix = "Number of unique values of the seed context variable, which contribute to the total number of evaluations of the `prototypes` scene."
)
_TotalCountWidget = lambda plug : _VariationsPlugValueWidget( plug, "", label = "Total Variations",
	toolTipPrefix = "The total number of unique contexts for evaluating the `prototypes` scene, including all context variables, and different prototype roots."
)

_TimeOffsetContextVariableWidget = lambda plug : _ContextVariableWidget( plug, overrideName = "frame" )

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.Instancer,

	"description",
	"""
	Copies from an input scene onto the vertices of a target
	object, making one copy per vertex. Additional primitive
	variables on the target object can be used to choose between
	multiple instances, and to specify their orientation and
	scale. Note the target object will be removed from the scene.
	""",

	"layout:section:Settings.General:collapsed", False,
	"layout:section:Settings.Transforms:collapsed", False,
	"layout:section:Settings.Attributes:collapsed", False,

	"layout:activator:modeIsIndexedRootsList", lambda node : node["prototypeMode"].getValue() == GafferScene.Instancer.PrototypeMode.IndexedRootsList,
	"layout:activator:modeIsNotIndexedRootsList", lambda node : node["prototypeMode"].getValue() != GafferScene.Instancer.PrototypeMode.IndexedRootsList,
	"layout:activator:modeIsNotRootPerVertex", lambda node : node["prototypeMode"].getValue() != GafferScene.Instancer.PrototypeMode.RootPerVertex,
	"layout:activator:seedEnabled", lambda node : node["seedEnabled"].getValue(),
	"layout:activator:seedParameters", lambda node : not node["rawSeed"].getValue(),

	"layout:customWidget:seedColumnHeadings:widgetType", "GafferSceneUI.InstancerUI._SeedColumnHeadings",
	"layout:customWidget:seedColumnHeadings:section", "Context Variations",
	"layout:customWidget:seedColumnHeadings:index", 18,

	"layout:customWidget:idContextCountSpacer:widgetType", "GafferSceneUI.InstancerUI._SeedCountSpacer",
	"layout:customWidget:idContextCountSpacer:section", "Context Variations",
	"layout:customWidget:idContextCountSpacer:index", 19,
	"layout:customWidget:idContextCountSpacer:accessory", True,

	"layout:customWidget:idContextCount:widgetType", "GafferSceneUI.InstancerUI._SeedCountWidget",
	"layout:customWidget:idContextCount:section", "Context Variations",
	"layout:customWidget:idContextCount:index", 19,
	"layout:customWidget:idContextCount:accessory", True,

	"layout:customWidget:seedVariableSpacer:widgetType", "GafferSceneUI.InstancerUI._VariationSpacer",
	"layout:customWidget:seedVariableSpacer:section", "Context Variations",
	"layout:customWidget:seedVariableSpacer:index", 20,
	"layout:customWidget:seedVariableSpacer:accessory", True,

	"layout:customWidget:seedsSpacer:widgetType", "GafferSceneUI.InstancerUI._VariationSpacer",
	"layout:customWidget:seedsSpacer:section", "Context Variations",
	"layout:customWidget:seedsSpacer:index", 21,
	"layout:customWidget:seedsSpacer:accessory", True,

	"layout:customWidget:seedPermutationSpacer:widgetType", "GafferSceneUI.InstancerUI._VariationSpacer",
	"layout:customWidget:seedPermutationSpacer:section", "Context Variations",
	"layout:customWidget:seedPermutationSpacer:index", 22,
	"layout:customWidget:seedPermutationSpacer:accessory", True,

	"layout:customWidget:seedSpacer:widgetType", "GafferSceneUI.InstancerUI._SectionSpacer",
	"layout:customWidget:seedSpacer:section", "Context Variations",
	"layout:customWidget:seedSpacer:index", 23,

	"layout:customWidget:timeOffsetHeadings:widgetType", "GafferSceneUI.InstancerUI._TimeOffsetColumnHeadings",
	"layout:customWidget:timeOffsetHeadings:section", "Context Variations",
	"layout:customWidget:timeOffsetHeadings:index", 24,
	"layout:customWidget:timeOffsetHeadings:description", "Testing description",

	"layout:customWidget:timeOffsetSpacer:widgetType", "GafferSceneUI.InstancerUI._SectionSpacer",
	"layout:customWidget:timeOffsetSpacer:section", "Context Variations",
	"layout:customWidget:timeOffsetSpacer:index", 25,
	"layout:customWidget:timeOffsetSpacer:divider", True,

	"layout:customWidget:totalSpacer:widgetType", "GafferSceneUI.InstancerUI._SectionSpacer",
	"layout:customWidget:totalSpacer:section", "Context Variations",
	"layout:customWidget:totalSpacer:index", 26,

	plugs = {

		"parent" : [

			"description",
			"""
			The object on which to make the instances. The
			position, orientation and scale of the instances
			are taken from per-vertex primitive variables on
			this object. This is ignored when a filter is
			connected, in which case the filter specifies
			multiple objects to make the instances from.
			""",

			"layout:section", "Settings.General",

		],

		"name" : [

			"description",
			"""
			The name of the location the instances will be
			generated below. This will be parented directly
			under the parent location.
			""",

			"layout:section", "Settings.General",

		],

		"prototypes" : [

			"description",
			"""
			The scene containing the prototypes to be applied to
			each vertex. Use the `prototypeMode` and associated
			plugs to control the mapping between prototypes and
			instances.

			Note that the prototypes are not limited to being a single
			object - they can have arbitrary child hierarchies.
			""",

			"plugValueWidget:type", "",

		],

		"prototypeMode" : [

			"description",
			"""
			The method used to define how the prototypes map
			onto each instance.

			- In "Indexed (Roots List)" mode, the `prototypeIndex`
			  primitive variable must be an integer per-vertex.
			  Optionally, a path in the prototypes scene corresponding
			  to each index can be specified via the `prototypeRootsList`
			  plug. If no roots are specified, an index of 0 applies the
			  first location from the prototypes scene, an index of 1
			  applies the second, and so on.

			- In "Indexed (Roots Variable)" mode, the `prototypeIndex`
			  primitive variable must be an integer per-vertex, and
			  the `prototypeRoots` primitive variable must be a separate
			  constant string array specifying a path in the prototypes
			  scene corresponding to each index.

			- In "Root per Vertex" mode, the `prototypeRoots` primitive
			  variable must be a string per-vertex which will be used to
			  specify a path in the prototypes scene for each instance.

			  > Note : it is advisable to provide an indexed string
			  array in order to limit the number of unique prototypes.
			""",

			"preset:Indexed (Roots List)", GafferScene.Instancer.PrototypeMode.IndexedRootsList,
			"preset:Indexed (Roots Variable)", GafferScene.Instancer.PrototypeMode.IndexedRootsVariable,
			"preset:Root per Vertex", GafferScene.Instancer.PrototypeMode.RootPerVertex,
			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"layout:section", "Prototypes",

		],

		"prototypeIndex" : [

			"description",
			"""
			The name of a per-vertex integer primitive variable used
			to determine which prototype is applied to the vertex.
			This plug is used in "Indexed (Roots List)" mode as well
			as "Indexed (Roots Variable)" mode.
			""",

			"userDefault", "prototypeIndex",
			"layout:section", "Prototypes",
			"layout:visibilityActivator", "modeIsNotRootPerVertex",

		],

		"prototypeRoots" : [

			"description",
			"""
			If `prototypeMode` is set to "Indexed (Roots Variable)",
			then this should specify the name of a constant string
			array primitive variable used to map between `prototypeIndex`
			and paths in the prototypes scene.

			If `prototypeMode` is set to "Root per Vertex", then this
			should specify the name of a per-vertex string primitive
			variable used to specify a path in the prototypes scene
			for each instance.

			This plug is not used in "Indexed (Roots List)" mode.
			""",

			"layout:section", "Prototypes",
			"layout:visibilityActivator", "modeIsNotIndexedRootsList",

		],

		"prototypeRootsList" : [

			"description",
			"""
			An explicit list of paths used to map between `prototypeIndex`
			and paths in the prototypes scene. This plug is only used in
			"Indexed (Roots List)" mode.
			""",

			"layout:section", "Prototypes",
			"layout:visibilityActivator", "modeIsIndexedRootsList",

		],

		"id" : [

			"description",
			"""
			The name of a per-vertex integer primitive variable
			used to give each instance a unique identity. This
			is useful when points are added and removed over time,
			as is often the case in a particle simulation. The
			id is used to name the instance in the output scene.
			""",

			"layout:section", "Settings.General",

		],

		"position" : [

			"description",
			"""
			The name of the per-vertex primitive variable used
			to specify the position of each instance.
			""",

			"layout:section", "Settings.Transforms",

		],

		"orientation" : [

			"description",
			"""
			The name of the per-vertex primitive variable used
			to specify the orientation of each instance. This
			must be provided as a quaternion : use an upstream
			Orientation node to convert from other representations
			before instancing.
			""",

			"userDefault", "orientation",
			"layout:section", "Settings.Transforms",

		],

		"scale" : [

			"description",
			"""
			The name of the per-vertex primitive variable used
			to specify the scale of each instance. Scale can be
			provided as a float for uniform scaling, or as a vector
			to define different scaling in each axis.
			""",

			"userDefault", "scale",
			"layout:section", "Settings.Transforms",

		],

		"attributes" : [

			"description",
			"""
			The names of per-vertex primitive variables to be
			turned into per-instance attributes. Names should
			be separated by spaces and can use Gaffer's
			standard wildcards.
			""",

			"layout:section", "Settings.Attributes",

		],

		"attributePrefix" : [

			"description",
			"""
			A prefix added to all per-instance attributes specified
			via the \"attributes\" plug.
			""",

			"userDefault", "user:",
			"layout:section", "Settings.Attributes",

		],

		"encapsulateInstanceGroups" : [

			"description",
			"""
			Converts each group of instances into a capsule, which won't
			be expanded until you Unencapsulate or render. When keeping
			these locations encapsulated, downstream nodes can't see the
			instance locations, which prevents editing but improves
			performance. This option should be preferred to a downstream
			Encapsulate node because it has the following benefits :

			- Substantially improved performance when the prototypes
			  define sets.
			- Fewer unnecessary updates during interactive rendering.
			""",
			"label", "Instance Groups",

			"layout:section", "Settings.Encapsulation",

		],

		"seedEnabled" : [
			"description",
			"""
			Creates a seed context variable based on a hash of the instance ID, which could come
			from the primitive varable specified in the `id` plug or otherwise the point index.
			This integer is available to the upstream prototypes network, and might typically
			be used with a Random node to randomise properties of the prototype.
			""",
			"layout:section", "Context Variations",
		],

		"seedVariable" : [
			"description",
			"""
			Name of the context variable to put the seed value in.
			""",
			"layout:section", "Context Variations",
			"layout:visibilityActivator", "seedEnabled",
		],

		"seeds" : [
			"description",
			"""
			The number of possible seed values.  Increasing this allows for more different variations
			to be driven by the seed, increasing the total number of variations required.
			""",
			"layout:section", "Context Variations",
			"layout:visibilityActivator", "seedEnabled",
			"layout:activator", "seedParameters",
		],

		"seedPermutation" : [
			"description",
			"""
			Changing the seedPermutation changes the mapping of ids to seeds.  This results in a different
			grouping of which instances end up with the same seed.
			""",
			"layout:section", "Context Variations",
			"layout:visibilityActivator", "seedEnabled",
			"layout:activator", "seedParameters",
		],

		"rawSeed" : [
			"description",
			"""
			Enable this in rare cases when it is required to pass through every single id directly into the seed
			context variable.  This is very expensive, because every single instance will need a separate
			context, but is sometimes useful, and may be an acceptable cost if there isn't a huge number of
			total instances.
			""",
			"layout:section", "Context Variations",
			"layout:visibilityActivator", "seedEnabled",
		],

		"contextVariables" : [
			"description",
			"""
			Specifies context variables to be created from primitive variables.  These variables are
			available to upstream prototypes network, allowing the prototypes scene to be generated
			differently depending on the source point.  Supports quantization to avoid re-evaluating the
			prototypes scene too many times.
			""",
			"layout:section", "Context Variations",
			"plugValueWidget:type", "GafferSceneUI.InstancerUI._ContextVariableListWidget",
		],

		"contextVariables.*" : [
			"deletable", True
		],

		"contextVariables.*.name" : [
			"description",
			"""
			Name of the primitive variable to read.  The same name will be used for the context variables
			available to the upstream prototype network.
			""",
		],

		"contextVariables.*.enabled" : [
			"description",
			"""
			Puts this variable in the context for the upstream prototypes network.
			""",
		],

		"contextVariables.*.quantize" : [
			"description",
			"""
			Quantizing to a large interval reduces the number of variations created.  For example, if the primvar varies from 0 to 1, and you quantize to 0.2, then only 6 unique variations will be created, even if there are millions of instances.  This dramatically improves performance, but if you need to see more continuous changes in the primvar values, you will need to reduce quantize, or in extreme cases where you need full accuracy and don't care about performance, set it to 0.
			""",
		],

		"timeOffset" : [
			"description",
			"Modify the current time when evaluating the prototypes network, by adding a primvar.",
			"layout:section", "Context Variations",
			"plugValueWidget:type", "GafferSceneUI.InstancerUI._TimeOffsetContextVariableWidget",
		],
		"timeOffset.name" : [
			"description",
			"""
			Name of a primitive variable to add to the time.  Must be a float or int primvar.  It will
			be treated as a number of frames, and can be negative or positive to adjust time forward or back.
			""",
		],
		"timeOffset.enabled" : [
			"description",
			"""
			Modifies the current time for the network upstream of the prototypes plug.
			""",
		],
		"timeOffset.quantize" : [
			"description",
			"""
			Quantizes the variable value before adding it to the time.  Quantizing to a large interval reduces the number of variations created.  For example, if the primvar varies from 0 to 1, and you quantize to 0.2, then only 6 unique variations will be created, even if there are millions of instances.  This dramatically improves performance, but if you need to see more continuous changes in the primvar values, you will need to reduce quantize, or in extreme cases where you need full accuracy and don't care about performance, set it to 0.
			""",
		],

		"variations" : [
			"description",
			"""
			This special output plug returns an CompoundData dictionary with counts about how many
			variations are being created.  For each context variable variable being set ( including
			"frame" when using Time Offset ), there is an entry with the name of the context variable,
			with an IntData containing the number of unique values of that context variable.  There is
			also an entry for "", with an IntData for the total number of unique contexts, considering
			all the context variables being created.

			Extracting the dictionary values and displaying them to users is handled by _VariationsPlugValueWidget.

			This information is important to display to users because varying the context requires
			extra evaluations of the `prototypes` scene, and can dramatically increase the cost of the Instancer.

			Note that variations are measured across all locations in the scene where the instancer is filtered.
			""",
			"layout:section", "Context Variations",
			"layout:index", 27,
			"plugValueWidget:type", "GafferSceneUI.InstancerUI._TotalCountWidget",
		],
	}

)
