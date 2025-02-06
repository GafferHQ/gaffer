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

import functools

import imath

import IECore

import Gaffer
import GafferUI
import GafferML

Gaffer.Metadata.registerNode(

	GafferML.DataToTensor,

	"description",
	"""
	Converts Gaffer data to tensors for use with the Inference node.
	Potential data sources include PrimitiveVariableQuery nodes to fetch data
	from 3D scenes, or expressions to generate arbitrary input data.
	""",

	"layout:customWidget:setupButton:widgetType", "GafferMLUI.DataToTensorUI._SetupWidget",
	"layout:customWidget:setupButton:section", "Settings",
	"layout:customWidget:setupButton:visibilityActivator", lambda node : "data" not in node,

	"noduleLayout:customGadget:setupButton:gadgetType", "GafferMLUI.DataToTensorUI._SetupGadget",
	"noduleLayout:customGadget:setupButton:index", 0,

	"layout:activator:isSetup", lambda node : "data" in node,

	plugs = {

		"data" : [

			"description",
			"""
			The data to be converted.
			""",

			"layout:index", 0,
			"noduleLayout:index", 0,

		],

		"shapeMode" : [

			"description",
			"""
			Method used to determine the shape of the tensor.

			- Automatic : Derives the shape from the data automatically. For example, a V3fVectorData of size 10
			  would give a shape of `[ 10, 3 ]`.
			- Custom : The shape is specified manually using the `shape` plug.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Automatic", GafferML.DataToTensor.ShapeMode.Automatic,
			"preset:Custom", GafferML.DataToTensor.ShapeMode.Custom,

			"layout:index", 1,
			"layout:visibilityActivator", "isSetup",

			"nodule:type", "",

		],

		"shape" : [

			"description",
			"""
			Defines the shape of the tensor. The product of the shape
			must equal the number of elements provided by the `data`
			plug.

			Only used when ShapeMode is Custom.
			""",

			"layout:index", 2,
			"noduleLayout:index", 2,

			"layout:activator", lambda plug : plug.node()["shapeMode"].getValue() == GafferML.DataToTensor.ShapeMode.Custom,
			"layout:visibilityActivator", "isSetup",

		],

		"tensor" : [

			"description",
			"""
			The output tensor.
			""",

			"layout:visibilityActivator", False,

		],

	}
)

class _SetupGadget( GafferUI.PlugAdder ) :

	def __init__( self, node ) :

		GafferUI.PlugAdder.__init__( self )

		self.__node = node
		self.__node.childAddedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ) )
		self.__node.childRemovedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ) )

		self.__updateVisibility()

	def canCreateConnection( self, endpoint ) :

		if not GafferUI.PlugAdder.canCreateConnection( self, endpoint ) :
			return False

		return (
			self.__node.canSetup( endpoint ) and
			endpoint.direction() == Gaffer.Plug.Direction.Out
		)

	def createConnection( self, endpoint ) :

		with Gaffer.UndoScope( self.__node.scriptNode() ) :
			self.__node.setup( endpoint )
			self.__node["data"].setInput( endpoint )

	def __childAddedOrRemoved( self, node, child ) :

		self.__updateVisibility()

	def __updateVisibility( self ) :

		self.setVisible( "data" not in self.__node )

GafferUI.NoduleLayout.registerCustomGadget( "GafferMLUI.DataToTensorUI._SetupGadget", _SetupGadget )

class _SetupWidget( GafferUI.Widget ) :

	def __init__( self, node ) :

		self.__node = node
		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.Widget.__init__( self, self.__row )

		with self.__row :

				GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

				GafferUI.MenuButton(
					menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ), title = "Choose Data Type" ),
					image = "plus.png", hasFrame = False
				)

				GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

	def __menuDefinition( self, menu ) :

		result = IECore.MenuDefinition()

		def setup( node, plugType ) :

			with Gaffer.UndoScope( node.scriptNode() ) :
				node.setup( plugType() )

		for plugType in (
			Gaffer.BoolVectorDataPlug,
			Gaffer.IntVectorDataPlug,
			Gaffer.FloatVectorDataPlug,
			None,
			Gaffer.V2iVectorDataPlug,
			Gaffer.V3iVectorDataPlug,
			Gaffer.V2fVectorDataPlug,
			Gaffer.V3fVectorDataPlug,
			None,
			Gaffer.Color3fVectorDataPlug,
			Gaffer.Color4fVectorDataPlug,
		) :
			if plugType is None :
				result.append( "/Divider{}".format( result.size() ), { "divider" : True } )
			else :
				result.append(
					"/" + plugType.__name__.replace( "VectorDataPlug", "" ),
					{
						"command" : functools.partial( setup, self.__node, plugType ),
						"active" : not Gaffer.MetadataAlgo.readOnly( self.__node ),
					}
				)

		return result
