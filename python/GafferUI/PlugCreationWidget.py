##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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
import traceback

import imath

import IECore

import Gaffer
import GafferUI

## Supports the following metadata registered to the parent node or plug :
#
# - `plugCreationWidget:includedTypes` : Filters the types of plugs which
#   can be created.
# - `plugCreationWidget:excludedTypes` : Filters the types of plugs which
#   can be created.
# - `plugCreationWidget:useGeometricInterpretation` : Provides specific
#   Point/Vector/Normal options when making vector plugs.
# - `plugCreationWidget:action` : Specifies one of the following actions
#   used to create plugs :
#       - "addPlug" : Adds plugs as children of the parent.
#       - "addNameValuePlug" : As above, but wrapping in a NameValuePlug.
#       - "addTweakPlug" : As above, but wrapping in a NameValuePlug.
#       - "setup" : Calls `setup()` on the parent.
class PlugCreationWidget( GafferUI.Widget ) :

	def __init__( self, plugParent, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
		GafferUI.Widget.__init__( self, row, **kw )

		with row :

			GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

			self.__button = GafferUI.MenuButton(
				image = "plus.png",
				hasFrame = False,
				menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ),
				toolTip = "Click to add plugs",
				immediate = True,
			)

			GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

		self.__plugParent = plugParent
		self.__contextTracker = GafferUI.ContextTracker.acquireForFocus( plugParent )

		self.__currentDropHandler = None
		self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
		self.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ) )
		self.dropSignal().connect( Gaffer.WeakMethod( self.__drop ) )

		Gaffer.Metadata.nodeValueChangedSignal().connect(
			Gaffer.WeakMethod( self.__nodeMetadataChanged )
		)
		if isinstance( plugParent, Gaffer.Plug ) :
			Gaffer.Metadata.plugValueChangedSignal( plugParent.node() ).connect(
				Gaffer.WeakMethod( self.__plugMetadataChanged )
			)

		self.__updateReadOnly()

	## Returns the GraphComponent on which this widget creates plugs.
	def plugParent( self ) :

		return self.__plugParent

	__plugCreationMenuSignal = Gaffer.Signals.Signal2(
		Gaffer.Signals.CatchingCombiner( "PlugCreationWidget.plugCreationMenuSignal" )
	)
	## Signal emitted to allow customisation of the menu used
	# to create plugs. The signature for slots is `( menuDefinition, plugCreationWidget )`,
	# and slots should just modify the menu definition in place.
	@staticmethod
	def plugCreationMenuSignal() :

		return PlugCreationWidget.__plugCreationMenuSignal

	## Signal emitted to allow customisation of the drag & drop behaviour.
	# The signature for slots is `( plugCreationWidget, dragDropEvent )` and
	# they should return a callable which will be called with the same
	# arguments on drop.
	@staticmethod
	def plugCreationDragEnterSignal() :

		try :
			return PlugCreationWidget.__plugCreationDragEnterSignal
		except AttributeError :
			PlugCreationWidget.__plugCreationDragEnterSignal = Gaffer.Signals.Signal2(
				PlugCreationWidget.__dragEnterSignalCombiner
			)
			return PlugCreationWidget.__plugCreationDragEnterSignal

	## Creates a plug on `plugParent()`. Expected to be called from menu items
	# created by `plugCreationMenuSignal()`. The optional `name` argument is
	# used only when wrapping the created plug in a NameValuePlug or TweakPlug.
	def createPlug( self, prototypePlug, name = "" ) :

		plug = prototypePlug.createCounterpart( prototypePlug.getName(), Gaffer.Plug.Direction.In )

		action = Gaffer.Metadata.value( self.__plugParent, "plugCreationWidget:action" ) or "addPlug"

		if action == "addPlug" and isinstance( self.__plugParent, Gaffer.CompoundDataPlug ) :
			action = "addNameValuePlug"
		elif action == "addPlug" and isinstance( self.__plugParent, Gaffer.TweaksPlug ) :
			action = "addTweakPlug"

		with Gaffer.UndoScope( self.__plugParent.ancestor( Gaffer.ScriptNode ) ) :

			match action :
				case "addPlug" :
					if isinstance( self.__plugParent, Gaffer.Box ) :
						## \todo Could this be made the default via a metadata registration in SubGraphUI.py?
						Gaffer.Metadata.registerValue( plug, "nodule:type", "" )
					plug.setFlags( Gaffer.Plug.Flags.Dynamic, True )
					self.__plugParent.addChild( plug )
				case "addNameValuePlug" :
					plug = Gaffer.NameValuePlug( "", plug, True, "member0", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
					plug["name"].setValue( name )
					self.__plugParent.addChild( plug )
				case "addTweakPlug" :
					plug = Gaffer.TweakPlug( "tweak0", valuePlug = plug, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
					plug["name"].setValue( name )
					self.__plugParent.addChild( plug )
				case "setup" :
					self.__plugParent.setup( plug )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		pendingDivider = None
		def appendItem( menuPath, plugType, plugKW = {} ) :

			if not self.__plugTypeIncluded( plugType ) :
				return

			nonlocal pendingDivider
			if pendingDivider :
				if result.size() :
					result.append( pendingDivider, { "divider" : True } )
				pendingDivider = None

			result.append(
				menuPath,
				{ "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), plugType, plugKW ) }
			)

		def appendDivider( menuPath ) :

			# Don't append a divider immediately, because the following
			# items might get omitted by the `includedTypes` filter. Instead
			# mark as pending and add as necessary in `appendItem()`.
			#
			# If we already have a pending divider, then don't replace it,
			# otherwise we omit dividers in front of submenus (this doesn't
			# mean we lose a divider inside the submenu, because we don't
			# need one until after we have our first item in the submenu).
			nonlocal pendingDivider
			if pendingDivider is None :
				pendingDivider = menuPath

		appendItem( "/Bool", Gaffer.BoolPlug )
		appendItem( "/Float", Gaffer.FloatPlug )
		appendItem( "/Int", Gaffer.IntPlug )

		appendDivider( "/StringDivider" )
		appendItem( "/String", Gaffer.StringPlug )

		appendDivider( "/VectorDivider" )

		for plugType in [ Gaffer.V2iPlug, Gaffer.V3iPlug, Gaffer.V2fPlug, Gaffer.V3fPlug ] :
			menuPath = "/{}".format( plugType.__name__.replace( "Plug", "" ) )
			if Gaffer.Metadata.value( self.__plugParent, "plugCreationWidget:useGeometricInterpretation" ) :
				for interpretation in [ "Point", "Vector", "Normal" ] :
					appendItem(
						f"{menuPath}/{interpretation}", plugType,
						{ "interpretation" : getattr( IECore.GeometricData.Interpretation, interpretation ) },
					)
			else :
				appendItem( menuPath, plugType )

		appendDivider( "/ColorDivider" )
		appendItem( "/Color3f", Gaffer.Color3fPlug )
		appendItem( "/Color4f", Gaffer.Color4fPlug )

		appendDivider( "/BoxDivider" )
		appendItem( "/Box2i", Gaffer.Box2iPlug, { "defaultValue" : imath.Box2i( imath.V2i( 0 ), imath.V2i( 0 ) ) } )
		appendItem( "/Box2f", Gaffer.Box2fPlug, { "defaultValue" : imath.Box2f( imath.V2f( 0 ), imath.V2f( 0 ) ) } )
		appendItem( "/Box3i", Gaffer.Box3iPlug, { "defaultValue" : imath.Box3i( imath.V3i( 0 ), imath.V3i( 0 ) ) } )
		appendItem( "/Box3f", Gaffer.Box3fPlug, { "defaultValue" : imath.Box3f( imath.V3f( 0 ), imath.V3f( 0 ) ) } )

		appendDivider( "/ObjectDivider" )
		appendItem( "/Object", Gaffer.ObjectPlug, { "defaultValue" : IECore.NullObject.defaultNullObject() } )

		# Arrays

		appendDivider( "/ArrayDivider" )
		appendItem( "/Array/Bool", Gaffer.BoolVectorDataPlug )
		appendItem( "/Array/Float", Gaffer.FloatVectorDataPlug )
		appendItem( "/Array/Int", Gaffer.IntVectorDataPlug )
		appendDivider( "/Array/StringDivider" )
		appendItem( "/Array/String", Gaffer.StringVectorDataPlug )
		appendDivider( "/Array/VectorDivider" )
		appendItem( "/Array/V2i", Gaffer.V2iVectorDataPlug )
		appendItem( "/Array/V3i", Gaffer.V3iVectorDataPlug )
		appendItem( "/Array/V2f", Gaffer.V2fVectorDataPlug )
		appendItem( "/Array/V3f", Gaffer.V3fVectorDataPlug )
		appendDivider( "/Array/ColorDivider" )
		appendItem( "/Array/Color3f", Gaffer.Color3fVectorDataPlug )
		appendItem( "/Array/Color4f", Gaffer.Color4fVectorDataPlug )

		with self.__contextTracker.context( self.__plugParent ) :
			self.plugCreationMenuSignal()( result, self )

		if not result.size() :
			result.append( "/All Types Excluded", { "active" : False } )

		return result

	def __addPlug( self, plugType, plugKW = {} ) :

		self.createPlug( plugType( **plugKW ) )

	def __updateReadOnly( self ) :

		self.__button.setEnabled( not Gaffer.MetadataAlgo.readOnly( self.__plugParent ) )

	def __nodeMetadataChanged( self, nodeTypeId, key, node ) :

		if Gaffer.MetadataAlgo.readOnlyAffectedByChange( self.__plugParent, nodeTypeId, key, node ) :
			self.__updateReadOnly()

	def __plugMetadataChanged( self, plug, key, reason ) :

		if Gaffer.MetadataAlgo.readOnlyAffectedByChange( self.__plugParent, plug, key ) :
			self.__updateReadOnly()

	def __plugTypeIncluded( self, plugType ) :

		includedTypes = Gaffer.Metadata.value( self.__plugParent, "plugCreationWidget:includedTypes" ) or "*"
		excludedTypes = Gaffer.Metadata.value( self.__plugParent, "plugCreationWidget:excludedTypes" ) or ""
		includedTypes = includedTypes.replace( ".", "::" )
		excludedTypes = excludedTypes.replace( ".", "::" )

		typeName = plugType.staticTypeName()

		if IECore.StringAlgo.matchMultiple( typeName, excludedTypes ) :
			return False

		return IECore.StringAlgo.matchMultiple( typeName, includedTypes )

	@staticmethod
	def __dragEnterSignalCombiner( results ) :

		while True :
			try :
				result = next( results )
				if result is not None :
					return result
			except StopIteration :
				return None
			except Exception as e :
				# Print message but continue to execute other slots
				IECore.msg( IECore.Msg.Level.Error, "PlugCreationWidget", traceback.format_exc() )
				# Remove circular references that would keep widget in limbo.
				e.__traceback__ = None

	@staticmethod
	def __dataDropHandler( plugCreationWidget, dragDropEvent ) :

		plug = None
		with IECore.IgnoredExceptions( Exception ) :
			plug = Gaffer.PlugAlgo.createPlugFromData( "plug", Gaffer.Plug.Direction.In, Gaffer.Plug.Flags.Default, dragDropEvent.data )
			plug.setName( plug.typeName().rpartition( ":" )[2] )

		if plug is None or not plugCreationWidget.__plugTypeIncluded( type( plug ) ) :
			GafferUI.PopupWindow.showWarning( "Unsupported data type", parent = plugCreationWidget )
			return

		plugCreationWidget.createPlug( plug )

	@staticmethod
	def __plugDropHandler( plugCreationWidget, dragDropEvent ) :

		name = ""
		plug = dragDropEvent.data
		if isinstance( plug, ( Gaffer.NameValuePlug, Gaffer.TweakPlug ) ) :
			with IECore.IgnoredExceptions( Exception ) :
				name = plug["name"].getValue()
			plug = plug["value"]

		if not plugCreationWidget.__plugTypeIncluded( type( plug ) ) :
			GafferUI.PopupWindow.showWarning( "Unsupported type", parent = plugCreationWidget )
			return

		plugCreationWidget.createPlug( plug.createCounterpart( dragDropEvent.data.getName(), Gaffer.Plug.Direction.In ), name = name )

	def __dragEnter( self, widget, event ) :

		with self.__contextTracker.context( self.__plugParent ) :
			self.__currentDropHandler = PlugCreationWidget.plugCreationDragEnterSignal()( self, event )

		if self.__currentDropHandler is None :
			if isinstance( event.data, IECore.Data ) :
				self.__currentDropHandler = PlugCreationWidget.__dataDropHandler
			elif isinstance( event.data, Gaffer.ValuePlug ) :
				self.__currentDropHandler = PlugCreationWidget.__plugDropHandler

		if self.__currentDropHandler is not None :
			self.__button.setHighlighted( True )
			return True

		return False

	def __dragLeave( self, widget, event ) :

		self.__button.setHighlighted( False )
		self.__currentDropHandler = None

	def __drop( self, widget, event ) :

		self.__button.setHighlighted( False )

		with self.__contextTracker.context( self.__plugParent ) :
			self.__currentDropHandler( self, event )

		self.__currentDropHandler = None
