##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

import Gaffer
import GafferUI

import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.DeleteRenderPasses,

	"description",
	"""
	Deletes render passes from the scene globals.
	""",

	plugs = {

		"mode" : [

			"description",
			"""
			Defines how the names listed in the `names` plug
			are treated. Delete mode deletes the listed names.
			Keep mode keeps the listed names, deleting all others.
			""",

			"preset:Delete", GafferScene.DeleteRenderPasses.Mode.Delete,
			"preset:Keep", GafferScene.DeleteRenderPasses.Mode.Keep,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"names" : [

			"description",
			"""
			The names of render passes to be deleted (or kept
			if the mode is set to Keep). Names should be separated
			by spaces and may contain any of Gaffer's standard
			wildcards.
			""",

			"ui:scene:acceptsRenderPassNames", True,

		],

	}

)

##########################################################################
# Right click menu for adding render pass names to plugs
# This is driven by metadata so it can be used for plugs on other
# nodes too.
##########################################################################

def __setValue( plug, value, *unused ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.setValue( value )

def __passPopupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	if plug is None :
		return

	if not Gaffer.Metadata.value( plug, "ui:scene:acceptsRenderPassNames" ) :
		return

	with plugValueWidget.context() :
		globals = plug.node()["in"]["globals"].getValue()
		currentNames = set( plug.getValue().split() )

	menuDefinition.prepend( "/RenderPassesDivider", { "divider" : True } )

	passNames = globals.get( "option:renderPass:names" ) or []
	if not len( passNames ) :
		menuDefinition.prepend( "/Render Passes/No Render Passes Available", { "active" : False } )
		return

	for passName in reversed( sorted( list( passNames ) ) ) :

		newNames = set( currentNames )

		if passName not in currentNames :
			newNames.add( passName )
		else :
			newNames.discard( passName )

		menuDefinition.prepend(
			"/Render Passes/{}".format( passName ),
			{
				"command" : functools.partial( __setValue, plug, " ".join( sorted( newNames ) ) ),
				"checkBox" : passName in currentNames,
				"active" : plug.settable() and not Gaffer.MetadataAlgo.readOnly( plug ),
			}
		)

GafferUI.PlugValueWidget.popupMenuSignal().connect( __passPopupMenu, scoped = False )
