##########################################################################
#
#  Copyright (c) 2020, Hypothetical Inc. All rights reserved.
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
import IECoreScene

import Gaffer
import GafferUI

import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.ImageSampler,

	"description",
	"""
	Samples image data and transfers the values onto a primitive
	variable on the sampling objects.
	""",

	plugs = {

		"image" : [

			"description",
			"""
			The image to sample primitive variable data from.
			""",
			"plugValueWidget:type", "",
			"nodule:type", "GafferUI::StandardNodule",
			"noduleLayout:spacing", 2.0,

		],

		"primitiveVariables" : [

			"description",
			"""
			The primitive variables to sample onto from a set of image channels.
			""",
			"plugValueWidget:type", "GafferSceneUI.ImageSamplerUI.ImageSamplerPlugValueWidget",

		],

		"primitiveVariables.*" : [

			"plugValueWidget:type", "GafferSceneUI.ImageSamplerUI.ChildPlugValueWidget",

		],

		"primitiveVariables.*.active" : [

			"boolPlugValueWidget:displayMode", "switch",

		],

		"primitiveVariables.*.name" : [

			"description",
			"""
			The name of the primitive variable to sample onto.
			""",

		],

		"primitiveVariables.*.interpretation" : [

			"description",
			"""
			The interpretation of the primitive variable. The number of channels sampled
			must correspond to the number of components the interpretation requires:
			three channels for Color, Normal, Point, and Vector; two channels for
			UV; one channel for None.
			""",
			"preset:None", IECore.GeometricData.Interpretation.None,
			"preset:Color", IECore.GeometricData.Interpretation.Color,
			"preset:Normal", IECore.GeometricData.Interpretation.Normal,
			"preset:Point", IECore.GeometricData.Interpretation.Point,
			"preset:UV", IECore.GeometricData.Interpretation.UV,
			"preset:Vector", IECore.GeometricData.Interpretation.Vector,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"primitiveVariables.*.channels" : [

			"description",
			"""
			The image channels to sample from. Multiple channels are separated by spaces. 
			Wildcards are not allowed. For vector type primitive variables, the order of
			the channels corresponds to the order of components of the vector. 
			""",

		],

		"uvSet" : [

			"description",
			"""
			The primitive variable holding uv data used to sample the image.
			""",
			
		],

		"uvBoundsMode" : [

				"description",
				"""
				The method to use to handle uv data outside the range of 0.0 - 1.0.
				- Clamp : Values below 0.0 will be set to 0.0, values above 1.0 
				will be set to 1.0 and values in between are unchanged.
				- Tile : Values wrap on integer boundaries.
				""",
				"preset:Clamp", GafferScene.ImageSampler.UVBoundsMode.Clamp,
				"preset:Tile", GafferScene.ImageSampler.UVBoundsMode.Tile,
				"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		],

	}

)

##########################################################################
# Custom PlugValueWidgets for listing image samplers
##########################################################################

class ImageSamplerPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		column = GafferUI.ListContainer( spacing = 6 )
		GafferUI.PlugValueWidget.__init__( self, column, plug )

		with column :

			# this will take care of laying out our list of samplers, as
			# each output is represented as a child plug of the main plug.
			GafferUI.PlugLayout( plug )

			# now we just need a little footer with a button for adding new outputs
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				GafferUI.MenuButton(
					image="plus.png", hasFrame=False, menu = GafferUI.Menu( Gaffer.WeakMethod( self.__addMenuDefinition ) )
				)

				GafferUI.Spacer( imath.V2i( 1 ), maximumSize = imath.V2i( 100000, 1 ), parenting = { "expand" : True } )

	def hasLabel( self ) :

		return True

	def _updateFromPlug( self ) :

		pass

	def __addMenuDefinition( self ) :

		node = self.getPlug().node()
		currentNames = set( [ variable["name"].getValue() for variable in node["primitiveVariables"].children() ] )

		m = IECore.MenuDefinition()

		registeredVariables = [
			{
				"name" : "Cs",
				"interpretation" : IECore.GeometricData.Interpretation.Color,
				"channels" : "R G B"
			},
			{
				"name" : "N",
				"interpretation" : IECore.GeometricData.Interpretation.Normal,
				"channels" : "R G B"
			},
			{
				"name" : "P",
				"interpretation" : IECore.GeometricData.Interpretation.Point,
				"channels" : "R G B"
			},
			{
				"name" : "Pref",
				"interpretation" : IECore.GeometricData.Interpretation.Vector,
				"channels" : "R G B"
			},
			{
				"name" : "scale",
				"interpretation" : IECore.GeometricData.Interpretation.Vector,
				"channels" : "R G B"
			},
			{
				"name" : "UV",
				"interpretation" : IECore.GeometricData.Interpretation.UV,
				"channels" : "R G"
			},
			{
				"name" : "velocity",
				"interpretation" : IECore.GeometricData.Interpretation.Vector,
				"channels" : "R G B"
			},
			{
				"name" : "width",
				"interpretation" : IECore.GeometricData.Interpretation.None,
				"channels" : "R"
			},
		]

		for v in registeredVariables :
			menuPath = "/" + v["name"]
			m.append(
				menuPath,
				{
					"command" : functools.partial( node.addPrimitiveVariableSampler, v["name"], v["interpretation"], v["channels"] ),
					"active" : v["name"] not in currentNames
				}
			)

		m.append( "/BlankDivider", { "divider" : True } )
		m.append( "/Custom", { "command" : functools.partial( node.addPrimitiveVariableSampler, "", IECore.GeometricData.Interpretation.None, "R" ) } )

		return m

# A widget for representing an individual primtive variable.
class ChildPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, childPlug ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=4 )
		GafferUI.PlugValueWidget.__init__( self, column, childPlug )

		with column :

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=4 ) as header :

				collapseButton = GafferUI.Button( image = "collapsibleArrowRight.png", hasFrame=False )
				collapseButton.clickedSignal().connect( Gaffer.WeakMethod( self.__collapseButtonClicked ), scoped = False )

				GafferUI.PlugValueWidget.create( childPlug["active"] )
				self.__label = GafferUI.Label( childPlug["name"].getValue() )

				GafferUI.Spacer( imath.V2i( 1 ), maximumSize = imath.V2i( 100000, 1 ), parenting = { "expand" : True } )

				self.__deleteButton = GafferUI.Button( image = "delete.png", hasFrame=False )
				self.__deleteButton.clickedSignal().connect( Gaffer.WeakMethod( self.__deleteButtonClicked ), scoped = False )
				self.__deleteButton.setVisible( False )

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing= 4 ) as self.__detailsColumn :

				GafferUI.PlugWidget( childPlug["name"] )
				GafferUI.PlugWidget( childPlug["interpretation"] )
				GafferUI.PlugWidget( childPlug["channels"] )

				GafferUI.Divider( GafferUI.Divider.Orientation.Horizontal )

			self.__detailsColumn.setVisible( False )

			header.enterSignal().connect( Gaffer.WeakMethod( self.__enter ), scoped = False )
			header.leaveSignal().connect( Gaffer.WeakMethod( self.__leave ), scoped = False )

	def hasLabel( self ) :

		return True

	def _updateFromPlug( self ) :

		with self.getContext() :

			enabled = self.getPlug()["active"].getValue()
			self.__label.setEnabled( enabled )
			self.__detailsColumn.setEnabled( enabled )

			self.__label.setText( self.getPlug()["name"].getValue() )

	def __enter( self, widget ) :

		self.__deleteButton.setVisible( True )

	def __leave( self, widget ) :

		self.__deleteButton.setVisible( False )

	def __collapseButtonClicked( self, button ) :

		visible = not self.__detailsColumn.getVisible()
		self.__detailsColumn.setVisible( visible )
		button.setImage( "collapsibleArrowDown.png" if visible else "collapsibleArrowRight.png" )

	def __deleteButtonClicked( self, button ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().parent().removeChild( self.getPlug() )
