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
				toolTip = "Click to add plugs"
			)

			GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

		self.__plugParent = plugParent

		Gaffer.Metadata.nodeValueChangedSignal().connect(
			Gaffer.WeakMethod( self.__nodeMetadataChanged )
		)
		if isinstance( plugParent, Gaffer.Plug ) :
			Gaffer.Metadata.plugValueChangedSignal( plugParent.node() ).connect(
				Gaffer.WeakMethod( self.__plugMetadataChanged )
			)

		self.__updateReadOnly()

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		result.append( "/Bool", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.BoolPlug ) } )
		result.append( "/Float", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.FloatPlug ) } )
		result.append( "/Int", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.IntPlug ) } )
		result.append( "/NumericDivider", { "divider" : True } )

		result.append( "/String", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.StringPlug ) } )
		result.append( "/StringDivider", { "divider" : True } )

		result.append( "/V2i", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.V2iPlug ) } )
		result.append( "/V3i", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.V3iPlug ) } )
		result.append( "/V2f", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.V2fPlug ) } )
		result.append( "/V3f", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.V3fPlug  ) } )
		result.append( "/VectorDivider", { "divider" : True } )

		result.append( "/Color3f", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.Color3fPlug ) } )
		result.append( "/Color4f", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.Color4fPlug ) } )
		result.append( "/ColorDivider", { "divider" : True } )

		# Arrays

		for label, plugType in [
			( "Float", Gaffer.FloatVectorDataPlug ),
			( "Int", Gaffer.IntVectorDataPlug ),
			( "NumericDivider", None ),
			( "String", Gaffer.StringVectorDataPlug ),
		] :
			if plugType is not None :
				result.append(
					"/Array/" + label,
					{
						"command" : functools.partial(
							Gaffer.WeakMethod( self.__addPlug ), plugType
						),
					}
				)
			else :
				result.append( "/Array/" + label, { "divider" : True } )

		return result

	def __addPlug( self, plugCreator ) :

		with Gaffer.UndoScope( self.__plugParent.ancestor( Gaffer.ScriptNode ) ) :
			plug = plugCreator( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			if isinstance( self.__plugParent, Gaffer.Box ) :
				## \todo Could this be made the default via a metadata registration in SubGraphUI.py?
				Gaffer.Metadata.registerValue( plug, "nodule:type", "" )
			self.__plugParent.addChild( plug )

	def __updateReadOnly( self ) :

		self.__button.setEnabled( not Gaffer.MetadataAlgo.readOnly( self.__plugParent ) )

	def __nodeMetadataChanged( self, nodeTypeId, key, node ) :

		if Gaffer.MetadataAlgo.readOnlyAffectedByChange( self.__plugParent, nodeTypeId, key, node ) :
			self.__updateReadOnly()

	def __plugMetadataChanged( self, plug, key, reason ) :

		if Gaffer.MetadataAlgo.readOnlyAffectedByChange( self.__plugParent, plug, key ) :
			self.__updateReadOnly()
