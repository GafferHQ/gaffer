##########################################################################
#
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

import functools
import imath

import IECore
import IECoreScene

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI
import weakref

# Widget for TweakPlug, which is used to build tweak nodes such as LightTweaks, CameraTweaks
# and ShaderTweaks.  Shows a value plug that you can use to specify a tweak value, along with
# a target parameter name, an enabled plug, and a mode.  The mode can be "Replace",
# or "Add"/"Subtract"/"Multiply" if the plug is numeric,
# or "Remove" if the metadata "tweakPlugValueWidget:allowRemove" is set

class TweakPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		# TODO - would be nice if this stuff didn't need to be added to the instance as metadata
		# John has said that in the future we may be able to use match patterns to register metadata
		# to children of a plug type, like we can do with nodes.
		# This would allow us to use dynamic metadata to hide the value plug when in "Remove" mode

		Gaffer.Metadata.registerValue( plug['name'], "description",
			"The name of the parameter to apply the tweak to.", persistent=False
		)
		Gaffer.Metadata.registerValue( plug['mode'], "plugValueWidget:type",
			"GafferUI.PresetsPlugValueWidget", persistent=False
		)

		presetNames = [ "Replace" ]

		# Identify plugs which are derived from NumericPlug or CompoundNumericPlug
		plugIsNumeric = hasattr( plug["value"], "hasMinValue" )
		if plugIsNumeric:
			presetNames += [ "Add", "Subtract", "Multiply" ]

		if Gaffer.Metadata.value( plug, "tweakPlugValueWidget:allowRemove" ):
			presetNames += [ "Remove" ]

		for name in presetNames:
			Gaffer.Metadata.registerValue( plug['mode'], "preset:" + name, GafferScene.TweakPlug.Mode.names[ name ], persistent = False )

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__row, plug )


		nameWidget = GafferUI.StringPlugValueWidget( plug["name"] )
		nameWidget.textWidget()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )

		self.__row.append( nameWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		self.__row.append(
			GafferUI.BoolPlugValueWidget(
				plug["enabled"],
				displayMode = GafferUI.BoolWidget.DisplayMode.Switch
			),
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top,
		)

		self.__row.append( GafferUI.PlugValueWidget.create( plug["mode"] ) )
		self.__row.append( GafferUI.PlugValueWidget.create( plug["value"] ), expand = True )

		self._updateFromPlug()

	def setPlug( self, plug ) :

		GafferUI.PlugValueWidget.setPlug( self, plug )

		self.__row[0].setPlug( plug["name"] )
		self.__row[1].setPlug( plug["enabled"] )
		self.__row[2].setPlug( plug["mode"] )
		self.__row[3].setPlug( plug["value"] )

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

		with self.getContext() :
			enabled = self.getPlug()["enabled"].getValue()

		for i in ( 0, 2, 3 ) :
			self.__row[i].setEnabled( enabled )

def __deletePlug( plug ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.parent().removeChild( plug )

def __plugPopupMenu( menuDefinition, plugValueWidget ):

	plug = plugValueWidget.getPlug()
	parent = plug.parent()
	node = plug.node()

	if not isinstance( plug, TweakPlug ):
		return

	menuDefinition.append( "/DeleteDivider", { "divider" : True } )
	menuDefinition.append(
		"/Delete",
		{
			"command" : functools.partial( __deletePlug, parent ),
			"active" : not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( parent )
		}
	)

__plugPopupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )

GafferUI.PlugValueWidget.registerType( GafferScene.TweakPlug, TweakPlugValueWidget )
