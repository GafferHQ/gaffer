##########################################################################
#
#  Copyright (c) 2013-2014, John Haddon. All rights reserved.
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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
import IECoreScene
import Gaffer
import GafferUI

import GafferOSL

import imath
import functools

# TODO _ duplicated from CompoundDataPlugValueWidget._MemberPlugValueWidget, omitted support for enabled
class _MemberPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, childPlug ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__row, childPlug )

		if not childPlug.getFlags( Gaffer.Plug.Flags.Dynamic ) :
			nameWidget = GafferUI.LabelPlugValueWidget(
				childPlug,
				horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right,
				verticalAlignment = GafferUI.Label.VerticalAlignment.Center,
			)
			nameWidget.label()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )
			# cheat to get the height of the label to match the height of a line edit
			# so the label and plug widgets align nicely. ideally we'd get the stylesheet
			# sorted for the QLabel so that that happened naturally, but QLabel sizing appears
			# somewhat unpredictable (and is sensitive to HTML in the text as well), making this
			# a tricky task.
			nameWidget.label()._qtWidget().setFixedHeight( 20 )
		else :
			nameWidget = GafferUI.StringPlugValueWidget( childPlug["name"] )
			nameWidget.textWidget()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )

		self.__row.append( nameWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		self.__row.append( GafferUI.PlugValueWidget.create( childPlug["value"] ), expand = True )

		self._updateFromPlug()

	def setPlug( self, plug ) :

		GafferUI.PlugValueWidget.setPlug( self, plug )

		if isinstance( self.__row[0], GafferUI.LabelPlugValueWidget ) :
			self.__row[0].setPlug( plug )
		else :
			self.__row[0].setPlug( plug["name"] )

		self.__row[-1].setPlug( plug["value"] )

	def hasLabel( self ) :

		return True

	def childPlugValueWidget( self, childPlug, lazy=True ) :

		for w in self.__row :
			if w.getPlug().isSame( childPlug ) :
				return w

		return None

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )

		for w in self.__row :
			w.setReadOnly( readOnly )

	def _updateFromPlug( self ) :
		pass



##########################################################################
# _PrimitiveVariablesFooter
##########################################################################

class _PrimitiveVariablesFooter( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.PlugValueWidget.__init__( self, row, plug )

		with row :

				GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

				menuButton = GafferUI.MenuButton(
					image = "plus.png",
					hasFrame = False,
					menu = GafferUI.Menu(
						Gaffer.WeakMethod( self.__menuDefinition ),
						title = "Add Input"
					),
					toolTip = "Add Input"
				)
				menuButton.setEnabled( not Gaffer.MetadataAlgo.readOnly( plug ) )

				GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

	def _updateFromPlug( self ) :

		self.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		# TODO - uv
		labelsAndConstructors = [
			( "closure", GafferOSL.ClosurePlug ),
			( "P", functools.partial( Gaffer.V3fPlug, interpretation = IECore.GeometricData.Interpretation.Point ) ),
			( "Pref", functools.partial( Gaffer.V3fPlug, interpretation = IECore.GeometricData.Interpretation.Point ) ),
			( "velocity", functools.partial( Gaffer.V3fPlug, interpretation = IECore.GeometricData.Interpretation.Vector ) ),
			( "width", functools.partial( Gaffer.FloatPlug ) ),
			( "Cs", functools.partial( Gaffer.Color3fPlug ) ),
			( "customInt", Gaffer.IntPlug ),
			( "customFloat", Gaffer.FloatPlug ),
			( "customVector", functools.partial( Gaffer.V3fPlug, interpretation = IECore.GeometricData.Interpretation.Vector ) ),
			( "customNormal", functools.partial( Gaffer.V3fPlug, interpretation = IECore.GeometricData.Interpretation.Normal ) ),
			( "customPoint", functools.partial( Gaffer.V3fPlug, interpretation = IECore.GeometricData.Interpretation.Point ) ),
			( "customColor", Gaffer.Color3fPlug ),
			( "customMatrix", Gaffer.M44fPlug ),
			( "customString", Gaffer.StringPlug ),
		]

		for label, constructor in labelsAndConstructors :

			result.append(
				"/" + label,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), label, constructor ),
				}
			)

		return result

	def __addPlug( self, name, plugConstructor ) :

		if plugConstructor == GafferOSL.ClosurePlug:
			with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
				self.getPlug().addChild( GafferOSL.ClosurePlug( name, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		else:
			plug = Gaffer.Plug( "primitiveVariable", 
				direction = Gaffer.Plug.Direction.In,
				flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			plug.addChild( Gaffer.StringPlug(
				"name",
				direction = Gaffer.Plug.Direction.In,
				flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
			) )
			plug["name"].setValue( name )
			plug.addChild( plugConstructor(
				"value",
				direction = Gaffer.Plug.Direction.In,
				flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
			) )

			with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
				self.getPlug().addChild( plug )

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferOSL.OSLObject,

	"description",
	"""
	Executes OSL shaders to perform object processing. Use the shaders from
	the OSL/ObjectProcessing menu to read primitive variables from the input
	object and then write primitive variables back to it.
	""",

	plugs = {

		"multiInput" : [

			"description",
			"""
			A special input for an OSL closure which will output multiple variables.
			For an old-style OSLObject, you would set up a network such as:
				InPoint->ProcessingNodes->OutPoint->OutObject->OSLObject.multiInput
			""",

			"nodule:type", "GafferUI::StandardNodule",
			"noduleLayout:section", "left",
			"noduleLayout:visible", False,
			"plugValueWidget:type", "",

		],
		"primitiveVariables" : [

			"description",
			"""
			Define primitive varibles to output by adding child plugs and connecting
			corresponding OSL shaders.  Supported plug types are :

			- FloatPlug
			- IntPlug
			- ColorPlug
			- V3fPlug ( outputting vector, normal or point )
			- M44fPlug
			- StringPlug

			If you want to add multiple outputs at once, you can also add a closure plug,
			which can accept a connection from an OSLCode with a combined output closure.
			""",
			"layout:customWidget:footer:widgetType", "GafferOSLUI.OSLObjectUI._PrimitiveVariablesFooter",
			"layout:customWidget:footer:index", -1,
			"nodule:type", "GafferUI::CompoundNodule",
			"noduleLayout:section", "left",
			"noduleLayout:spacing", 0.2,
			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
		],
		"primitiveVariables.*" : [

			# Although the parameters plug is positioned
			# as we want above, we must also register
			# appropriate values for each individual parameter,
			# for the case where they get promoted to a box
			# individually.
			"noduleLayout:section", "left",
			"nodule:type", "GafferUI::CompoundNodule",
			"plugValueWidget:type", "GafferOSLUI.OSLObjectUI._MemberPlugValueWidget"
		],
		"primitiveVariables.closure*" : [
			"nodule:type", "GafferUI::StandardNodule",
			"plugValueWidget:type", "", #TODO - should do standard placeholder thing
		],
		"primitiveVariables.*.name" : [

			"nodule:type", "",
			"plugValueWidget:type", "GafferUI.StringPlugValueWidget",
		],
		"primitiveVariables.*.value" : [

			# Although the parameters plug is positioned
			# as we want above, we must also register
			# appropriate values for each individual parameter,
			# for the case where they get promoted to a box
			# individually.
			"noduleLayout:section", "left",
			"nodule:type", "GafferUI::StandardNodule",
			"noduleLayout:label", lambda plug : plug.parent()["name"].getValue(),

			#TODO - how do I reset this to choose the default ( color or numeric )?
			"plugValueWidget:type", lambda plug : "GafferUI." + type( GafferUI.PlugValueWidget.create( plug, useTypeOnly=True ) ).__name__,
		],

		"interpolation" : [

			"description",
			"""
			The interpolation type of the primitive variables created by this node.
			For instance, Uniform interpolation means that the shader is run once per face on a mesh, allowing it to output primitive variables with a value per face. 
			All non-constant input primitive variables are resampled to match the selected interpolation so that they can be accessed from the shader.
			""",

			"preset:Uniform", IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			"preset:Vertex", IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			"preset:FaceVarying", IECoreScene.PrimitiveVariable.Interpolation.FaceVarying,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",


		]

	}

)

#########################################################################
# primitiveVariable plug menu
##########################################################################

def __deletePlug( plug ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.parent().removeChild( plug )

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	if not isinstance( plug.node(), GafferOSL.OSLObject ):
		return

	relativeName = plug.relativeName( plug.node() ).split( "." )
	if relativeName[0] != "primitiveVariables" or len( relativeName ) < 2:
		return

	primVarPlug = plug.node()["primitiveVariables"][relativeName[1]]

	menuDefinition.append( "/DeleteDivider", { "divider" : True } )
	menuDefinition.append(
		"/Delete",
		{
			"command" : functools.partial( __deletePlug, primVarPlug ),
			"active" : not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( primVarPlug ),
		}
	)

__plugPopupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )


