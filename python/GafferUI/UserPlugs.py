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

import functools
import imath

import IECore

import Gaffer
import GafferUI

## Appends menu items for the creation of user plugs on the specified parent.
def appendPlugCreationMenuDefinitions( plugParent, menuDefinition, prefix = "" ) :

	active = not Gaffer.MetadataAlgo.readOnly( plugParent )

	menuDefinition.append( prefix + "/Bool", { "command" : functools.partial( __addPlug, plugParent, Gaffer.BoolPlug ), "active" : active } )
	menuDefinition.append( prefix + "/Float", { "command" : functools.partial( __addPlug, plugParent, Gaffer.FloatPlug ), "active" : active } )
	menuDefinition.append( prefix + "/Int", { "command" : functools.partial( __addPlug, plugParent, Gaffer.IntPlug ), "active" : active } )
	menuDefinition.append( prefix + "/NumericDivider", { "divider" : True } )

	menuDefinition.append( prefix + "/String", { "command" : functools.partial( __addPlug, plugParent, Gaffer.StringPlug ), "active" : active } )
	menuDefinition.append( prefix + "/FilePath", { "command" : functools.partial(__addPlug, plugParent, Gaffer.FilePathPlug ), "active" : active } )
	menuDefinition.append( prefix + "/StringDivider", { "divider" : True } )

	menuDefinition.append( prefix + "/V2i", { "command" : functools.partial( __addPlug, plugParent, Gaffer.V2iPlug ), "active" : active } )
	menuDefinition.append( prefix + "/V3i", { "command" : functools.partial( __addPlug, plugParent, Gaffer.V3iPlug ), "active" : active } )
	menuDefinition.append( prefix + "/V2f", { "command" : functools.partial( __addPlug, plugParent, Gaffer.V2fPlug ), "active" : active } )
	menuDefinition.append( prefix + "/V3f", { "command" : functools.partial( __addPlug, plugParent, Gaffer.V3fPlug  ), "active" : active } )
	menuDefinition.append( prefix + "/VectorDivider", { "divider" : True } )

	menuDefinition.append( prefix + "/Color3f", { "command" : functools.partial( __addPlug, plugParent, Gaffer.Color3fPlug ), "active" : active } )
	menuDefinition.append( prefix + "/Color4f", { "command" : functools.partial( __addPlug, plugParent, Gaffer.Color4fPlug ), "active" : active } )
	menuDefinition.append( prefix + "/ColorDivider", { "divider" : True } )

	# Arrays

	for label, plugType in [
		( "Float", Gaffer.FloatVectorDataPlug ),
		( "Int", Gaffer.IntVectorDataPlug ),
		( "NumericDivider", None ),
		( "String", Gaffer.StringVectorDataPlug ),
	] :
		if plugType is not None :
			menuDefinition.append(
				prefix + "/Array/" + label,
				{
					"command" : functools.partial(
						__addPlug, plugParent,
						plugCreator = functools.partial( plugType, defaultValue = plugType.ValueType() )
					),
					"active" : active
				}
			)
		else :
			menuDefinition.append( prefix + "/Array/" + label, { "divider" : True } )

## Returns a widget that allows the user to add plugs to a particular parent.
# Intended for use within a PlugLayout.
def plugCreationWidget( plugParent ) :

	return __PlugCreationWidget( plugParent )

def __addPlug( plugParent, plugCreator, **kw ) :

	with Gaffer.UndoScope( plugParent.ancestor( Gaffer.ScriptNode ) ) :
		plug = plugCreator( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		Gaffer.Metadata.registerValue( plug, "nodule:type", "" )
		plugParent.addChild( plug )

## \todo Maybe it would make more sense to expose this directly?
class __PlugCreationWidget( GafferUI.Widget ) :

	def __init__( self, plugParent, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
		GafferUI.Widget.__init__( self, row, **kw )

		with row :
			GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )
			self.__button = GafferUI.MenuButton(
				image="plus.png",
				hasFrame=False,
				menu=GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ),
				toolTip = "Click to add plugs"
			)
			GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

		self.__plugParent = plugParent

		Gaffer.Metadata.nodeValueChangedSignal().connect(
			Gaffer.WeakMethod( self.__nodeMetadataChanged ), scoped = False
		)
		if isinstance( plugParent, Gaffer.Plug ) :
			Gaffer.Metadata.plugValueChangedSignal( plugParent.node() ).connect(
				Gaffer.WeakMethod( self.__plugMetadataChanged ), scoped = False
			)

		self.__updateReadOnly()

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()
		appendPlugCreationMenuDefinitions( self.__plugParent, result )
		return result

	def __updateReadOnly( self ) :

		self.__button.setEnabled( not Gaffer.MetadataAlgo.readOnly( self.__plugParent ) )

	def __nodeMetadataChanged( self, nodeTypeId, key, node ) :

		if Gaffer.MetadataAlgo.readOnlyAffectedByChange( self.__plugParent, nodeTypeId, key, node ) :
			self.__updateReadOnly()

	def __plugMetadataChanged( self, plug, key, reason ) :

		if Gaffer.MetadataAlgo.readOnlyAffectedByChange( self.__plugParent, plug, key ) :
			self.__updateReadOnly()
