##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

from __future__ import with_statement

import IECore

import Gaffer
import GafferUI

## Supported plug metadata :
#
# "compoundDataPlugValueWidget:editable"
class CompoundDataPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__column = GafferUI.ListContainer( spacing = 6 )

		GafferUI.PlugValueWidget.__init__( self, self.__column, plug, **kw )

		with self.__column :

			self.__layout = GafferUI.PlugLayout( plug )

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal ) as self.__editRow :

				GafferUI.Spacer( IECore.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

				GafferUI.MenuButton(
					image = "plus.png",
					hasFrame = False,
					menu = GafferUI.Menu( Gaffer.WeakMethod( self.__addMenuDefinition ) )
				)

				GafferUI.Spacer( IECore.V2i( 1 ), IECore.V2i( 999999, 1 ), parenting = { "expand" : True } )

		self._updateFromPlug()

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

	def childPlugValueWidget( self, childPlug, lazy=True ) :

		return self.__layout.plugValueWidget( childPlug, lazy )

	def _updateFromPlug( self ) :

		editable = True
		if self.getPlug() is not None :
			editable = Gaffer.Metadata.value( self.getPlug(), "compoundDataPlugValueWidget:editable" )
			editable = editable if editable is not None else True

		self.__editRow.setVisible( editable )

	def __addMenuDefinition( self ) :

		result = IECore.MenuDefinition()
		result.append( "/Add/Bool", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.BoolData( False ) ) } )
		result.append( "/Add/Float", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.FloatData( 0 ) ) } )
		result.append( "/Add/Int", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.IntData( 0 ) ) } )
		result.append( "/Add/NumericDivider", { "divider" : True } )

		result.append( "/Add/String", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.StringData( "" ) ) } )
		result.append( "/Add/StringDivider", { "divider" : True } )

		result.append( "/Add/V2i/Vector", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.V2iData( IECore.V2i( 0 ), IECore.GeometricData.Interpretation.Vector ) ) } )
		result.append( "/Add/V2i/Normal", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.V2iData( IECore.V2i( 0 ), IECore.GeometricData.Interpretation.Normal ) ) } )
		result.append( "/Add/V2i/Point", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.V2iData( IECore.V2i( 0 ), IECore.GeometricData.Interpretation.Point ) ) } )

		result.append( "/Add/V3i/Vector", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.V3iData( IECore.V3i( 0 ), IECore.GeometricData.Interpretation.Vector ) ) } )
		result.append( "/Add/V3i/Normal", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.V3iData( IECore.V3i( 0 ), IECore.GeometricData.Interpretation.Normal ) ) } )
		result.append( "/Add/V3i/Point", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.V3iData( IECore.V3i( 0 ), IECore.GeometricData.Interpretation.Point ) ) } )

		result.append( "/Add/V2f/Vector", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.V2fData( IECore.V2f( 0 ), IECore.GeometricData.Interpretation.Vector ) ) } )
		result.append( "/Add/V2f/Normal", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.V2fData( IECore.V2f( 0 ), IECore.GeometricData.Interpretation.Normal ) ) } )
		result.append( "/Add/V2f/Point", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.V2fData( IECore.V2f( 0 ), IECore.GeometricData.Interpretation.Point ) ) } )

		result.append( "/Add/V3f/Vector", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.V3fData( IECore.V3f( 0 ), IECore.GeometricData.Interpretation.Vector ) ) } )
		result.append( "/Add/V3f/Normal", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.V3fData( IECore.V3f( 0 ), IECore.GeometricData.Interpretation.Normal ) ) } )
		result.append( "/Add/V3f/Point", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.V3fData( IECore.V3f( 0 ), IECore.GeometricData.Interpretation.Point ) ) } )

		result.append( "/Add/VectorDivider", { "divider" : True } )

		result.append( "/Add/Color3f", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.Color3fData( IECore.Color3f( 0 ) ) ) } )
		result.append( "/Add/Color4f", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.Color4fData( IECore.Color4f( 0, 0, 0, 1 ) ) ) } )

		return result

	def __addItem( self, name, value ) :

		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
			self.getPlug().addOptionalMember( name, value, enabled=True )

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

		if "enabled" in childPlug :
			self.__row.append(
				GafferUI.BoolPlugValueWidget(
					childPlug["enabled"],
					displayMode = GafferUI.BoolWidget.DisplayMode.Switch
				),
				verticalAlignment = GafferUI.Label.VerticalAlignment.Top,
			)

		self.__row.append( GafferUI.PlugValueWidget.create( childPlug["value"] ), expand = True )

		self._updateFromPlug()

	def setPlug( self, plug ) :

		GafferUI.PlugValueWidget.setPlug( self, plug )

		if isinstance( self.__row[0], GafferUI.LabelPlugValueWidget ) :
			self.__row[0].setPlug( plug )
		else :
			self.__row[0].setPlug( plug["name"] )

		if "enabled" in plug :
			self.__row[1].setPlug( plug["enabled"] )

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

		if "enabled" in self.getPlug() :
			with self.getContext() :
				enabled = self.getPlug()["enabled"].getValue()

			if isinstance( self.__row[0], GafferUI.StringPlugValueWidget ) :
				self.__row[0].setEnabled( enabled )

			self.__row[-1].setEnabled( enabled )

GafferUI.PlugValueWidget.registerType( Gaffer.CompoundDataPlug, CompoundDataPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.CompoundDataPlug.MemberPlug, _MemberPlugValueWidget )

##########################################################################
# Plug menu
##########################################################################

def __deletePlug( plug ) :

	with Gaffer.UndoContext( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.parent().removeChild( plug )

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	memberPlug = plug if isinstance( plug, Gaffer.CompoundDataPlug.MemberPlug ) else None
	memberPlug = memberPlug if memberPlug is not None else plug.ancestor( Gaffer.CompoundDataPlug.MemberPlug )
	if memberPlug is None :
		return

	if not memberPlug.getFlags( Gaffer.Plug.Flags.Dynamic ) :
		return

	menuDefinition.append( "/DeleteDivider", { "divider" : True } )
	menuDefinition.append(
		"/Delete",
		{
			"command" : IECore.curry( __deletePlug, memberPlug ),
			"active" : not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( memberPlug ),
		}
	)

__plugPopupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )
