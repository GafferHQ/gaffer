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

	## Creates a plug on `plugParent()`. Expected to be called from menu items
	# created by `plugCreationMenuSignal()`. The optional `name` argument is
	# used only when wrapping the created plug in a NameValuePlug or TweakPlug.
	def createPlug( self, prototypePlug, name = "" ) :

		plug = prototypePlug.createCounterpart( prototypePlug.getName(), Gaffer.Plug.Direction.In )

		with Gaffer.UndoScope( self.__plugParent.ancestor( Gaffer.ScriptNode ) ) :
			if isinstance( self.__plugParent, Gaffer.CompoundDataPlug ) :
				plug = Gaffer.NameValuePlug( "", plug, True, "member0" )
				plug["name"].setValue( name )
			elif isinstance( self.__plugParent, Gaffer.TweaksPlug ) :
				plug = Gaffer.TweakPlug( "tweak0", valuePlug = plug )
				plug["name"].setValue( name )
			if isinstance( self.__plugParent, Gaffer.Box ) :
				## \todo Could this be made the default via a metadata registration in SubGraphUI.py?
				Gaffer.Metadata.registerValue( plug, "nodule:type", "" )
			plug.setFlags( Gaffer.Plug.Flags.Dynamic, True )
			self.__plugParent.addChild( plug )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		includedTypes = Gaffer.Metadata.value( self.__plugParent, "plugCreationWidget:includedTypes" ) or "*"
		excludedTypes = Gaffer.Metadata.value( self.__plugParent, "plugCreationWidget:excludedTypes" ) or ""
		includedTypes = includedTypes.replace( ".", "::" )
		excludedTypes = excludedTypes.replace( ".", "::" )

		pendingDivider = None
		def appendItem( menuPath, plugType, plugKW = {} ) :

			typeName = plugType.staticTypeName()

			if IECore.StringAlgo.matchMultiple( typeName, excludedTypes ) :
				return

			if not IECore.StringAlgo.matchMultiple( typeName, includedTypes ) :
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
