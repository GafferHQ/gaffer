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

import IECore

import Gaffer
import GafferUI
import GafferDispatch

Gaffer.Metadata.registerNode(

	GafferDispatch.Wedge,

	"description",
	"""
	Causes upstream nodes to be dispatched multiple times in a range
	of contexts, each time with a different value for a specified variable.
	This variable should be referenced in upstream expressions to apply
	variation to the tasks being performed. For instance, it could be
	used to drive a shader parameter to perform a series of "wedges" to
	demonstrate the results of a range of possible parameter values.
	""",

	"layout:activator:modeIsFloatRange", lambda node : node["mode"].getValue() == int( node.Mode.FloatRange ),
	"layout:activator:modeIsIntRange", lambda node : node["mode"].getValue() == int( node.Mode.IntRange ),
	"layout:activator:modeIsColorRange", lambda node : node["mode"].getValue() == int( node.Mode.ColorRange ),
	"layout:activator:modeIsFloatList", lambda node : node["mode"].getValue() == int( node.Mode.FloatList ),
	"layout:activator:modeIsIntList", lambda node : node["mode"].getValue() == int( node.Mode.IntList ),
	"layout:activator:modeIsStringList", lambda node : node["mode"].getValue() == int( node.Mode.StringList ),
	"layout:activator:modeIsNumeric", lambda node : node["mode"].getValue() in ( int( node.Mode.IntRange ), int( node.Mode.FloatRange ) ),

	"layout:customWidget:numericValues:widgetType", "GafferUI.WedgeUI._NumericValuesPreview",
	"layout:customWidget:numericValues:visibilityActivator", "modeIsNumeric",
	"layout:customWidget:numericValues:section", "Settings",

	"layout:customWidget:colorValues:widgetType", "GafferUI.WedgeUI._ColorValuesPreview",
	"layout:customWidget:colorValues:visibilityActivator", "modeIsColorRange",
	"layout:customWidget:colorValues:section", "Settings",

	"ui:spreadsheet:activeRowNamesConnection", "strings",
	"ui:spreadsheet:selectorContextVariablePlug", "variable",

	plugs = {

		"variable" : [

			"description",
			"""
			The name of the context variable defined by the wedge.
			This should be used in upstream expressions to apply the
			wedged value to specific nodes.
			""",

		],

		"indexVariable" : [

			"description",
			"""
			The name of an index context variable defined by the wedge.
			This is assigned values starting at 0 and incrementing for
			each new value - for instance a wedged float range might
			assign variable values of `0.25, 0,5, 0.75` or `0.1, 0,2, 0.3`
			but the corresponding index variable would take on values of
			`0, 1, 2` in both cases.

			The index variable is particularly useful for generating
			unique filenames when using a float range to perform
			wedged renders.
			""",

		],

		"mode" : [

			"description",
			"""
			The method used to define the range of values used by
			the wedge. It is possible to define numeric or color
			ranges, and also to specify explicit lists of numbers or
			strings.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"preset:Float Range", int( GafferDispatch.Wedge.Mode.FloatRange ),
			"preset:Int Range", int( GafferDispatch.Wedge.Mode.IntRange ),
			"preset:Color Range", int( GafferDispatch.Wedge.Mode.ColorRange ),
			"preset:Float List", int( GafferDispatch.Wedge.Mode.FloatList ),
			"preset:Int List", int( GafferDispatch.Wedge.Mode.IntList ),
			"preset:String List", int( GafferDispatch.Wedge.Mode.StringList ),

		],

		# Float Ramge

		"floatMin" : [

			"description",
			"""
			The smallest value of the wedge range when the
			mode is set to "Float Range". Has no effect in
			other modes.
			""",

			"layout:visibilityActivator", "modeIsFloatRange",

		],

		"floatMax" : [

			"description",
			"""
			The largest allowable value of the wedge range
			when the mode is set to "Float Range". Has no
			effect in other modes.
			""",

			"layout:visibilityActivator", "modeIsFloatRange",

		],

		"floatSteps" : [

			"description",
			"""
			The number of steps in the value range
			defined when in "Float Range" mode. The
			steps are distributed evenly between the
			min and max values. Has no effect in
			other modes.
			""",

			"layout:visibilityActivator", "modeIsFloatRange",

		],

		# Int Range

		"intMin" : [

			"description",
			"""
			The smallest value of the wedge range when the
			mode is set to "Int Range". Has no effect in
			other modes.
			""",

			"layout:visibilityActivator", "modeIsIntRange",

		],

		"intMax" : [

			"description",
			"""
			The largest allowable value of the wedge range
			when the mode is set to "Int Range". Has no
			effect in other modes.
			""",

			"layout:visibilityActivator", "modeIsIntRange",

		],

		"intStep" : [

			"description",
			"""
			The step between successive values when the
			mode is set to "Int Range". Values are
			generated by adding this step to the minimum
			value until the maximum value is exceeded.
			Note that if (max - min) is not exactly divisible
			by the step then the maximum value may not
			be used at all. Has no effect in other modes.
			""",

			"layout:visibilityActivator", "modeIsIntRange",

		],

		# Color Range

		"ramp" : [

			"description",
			"""
			The range of colours used when the mode
			is set to "Colour Range". Has no effect in
			other modes.
			""",

			"layout:visibilityActivator", "modeIsColorRange",

		],

		"colorSteps" : [

			"description",
			"""
			The number of steps in the wedge range
			defined when in "Colour Range" mode. The
			steps are distributed evenly from the start
			to the end of the ramp. Has no effect in
			other modes.
			""",

			"label", "Steps",
			"layout:visibilityActivator", "modeIsColorRange",

		],

		# Lists

		"floats" : [

			"description",
			"""
			The list of values used when in "Float List"
			mode. Has no effect in other modes.
			""",

			"layout:visibilityActivator", "modeIsFloatList",

		],

		"ints" : [

			"description",
			"""
			The list of values used when in "Int List"
			mode. Has no effect in other modes.
			""",

			"layout:visibilityActivator", "modeIsIntList",

		],

		"strings" : [

			"description",
			"""
			The list of values used when in "String List"
			mode. Has no effect in other modes.
			""",

			"layout:visibilityActivator", "modeIsStringList",

		],

	}

)

##########################################################################
# Preview widgets
##########################################################################

class _ValuesPreview( GafferUI.Widget ) :

	def __init__( self, previewWidget, node, **kw ) :

		self.__grid = GafferUI.GridContainer( spacing = 4 )

		GafferUI.Widget.__init__( self, self.__grid, **kw )

		self.__grid[0,0] =  GafferUI.Spacer(
			imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ),
			imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ),
		)
		self.__grid[1,0] = previewWidget

		previewWidget.setToolTip( "The values generated by the wedge" )

		self.__node = node
		node.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ), scoped = False )

	def node( self ) :

		return self.__node

	def _update( self ) :

		raise NotImplementedError

	@GafferUI.LazyMethod()
	def __updateLazily( self ) :

		self._update()

	def __plugDirtied( self, plug ) :

		self.__updateLazily()

class _NumericValuesPreview( _ValuesPreview ) :

	def __init__( self, node, **kw ) :

		self.__textWidget = GafferUI.MultiLineTextWidget( editable = False )
		_ValuesPreview.__init__( self, self.__textWidget, node, **kw )

		self._update()

	def _update( self ) :

		with self.node().scriptNode().context() :

			try :
				values = self.node().values()
			except Exception as e :
				self.__textWidget.setText( str( e ) )
				return

		if len( values ) and isinstance( values[0], float ) :
			values = [ GafferUI.NumericWidget.valueToString( v ) for v in values ]
		else :
			values = [ str( v ) for v in values ]

		self.__textWidget.setText( ", ".join( values ) )

class _ColorValuesPreview( _ValuesPreview ) :

	def __init__( self, node, **kw ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
		self.__row._qtWidget().setFixedHeight( 100 )

		_ValuesPreview.__init__( self, self.__row, node, **kw )

		self._update()

	def _update( self ) :

		with self.node().scriptNode().context() :
			try :
				values = self.node().values()
			except :
				return

		if not len( values ) or not isinstance( values[0], imath.Color3f ) :
			return

		for i in range( 0, max( len( values ), len( self.__row ) ) ) :

			if i >= len( values ) :

				self.__row[i].setVisible( False )

			else :

				if i < len( self.__row ) :
					swatch = self.__row[i]
					swatch.setVisible( True )
				else :
					swatch = GafferUI.ColorSwatch()
					swatch._qtWidget().setMinimumSize( 0, 12 )
					self.__row.append( swatch )

				swatch.setColor( values[i])
