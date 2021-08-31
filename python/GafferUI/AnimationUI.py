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

import math
import functools

import imath

import Gaffer
import GafferUI

Gaffer.Metadata.registerNode(

	Gaffer.Animation,

	"description",
	"""
	Generates keyframed animation to be applied to plugs
	on other nodes.
	""",

	"nodeGadget:type", "GafferUI::AuxiliaryNodeGadget",
	"auxiliaryNodeGadget:label", "a",

	plugs = {

		"curves" : [

			"description",
			"""
			Stores animation curves. Rather than access
			these directly, prefer to use the Animation::acquire()
			method.
			""",

		],

	},

)

# PlugValueWidget popup menu for setting keys
##########################################################################

def __setKey( plug, context ) :

	with context :
		value = plug.getValue()

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		curve = Gaffer.Animation.acquire( plug )
		time = Gaffer.Animation.Time( context.getTime(), Gaffer.Animation.Time.Units.Seconds )
		curve.addKey( Gaffer.Animation.Key( time, value ), True )

def __removeKey( plug, key ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		curve = Gaffer.Animation.acquire( plug )
		curve.removeKey( key )

def __setKeyInterpolator( plug, key, name ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		key.setInterpolator( name )

def __popupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	if not isinstance( plug, Gaffer.ValuePlug ) or not Gaffer.Animation.canAnimate( plug ) :
		return

	context = plugValueWidget.getContext()

	menuDefinition.prepend( "/AnimationDivider", { "divider" : True } )

	if Gaffer.Animation.isAnimated( plug ) :

		curve = Gaffer.Animation.acquire( plug )
		time = Gaffer.Animation.Time( context.getTime(), Gaffer.Animation.Time.Units.Seconds )

		nextKey = curve.nextKey( time )
		menuDefinition.prepend(
			"/Jump To/Next Key",
			{
				"command" : functools.partial( context.setTime, nextKey.getTime().getSeconds() if nextKey is not None else 0 ),
				"active" : nextKey is not None,
			}
		)

		previousKey = curve.previousKey( time )
		menuDefinition.prepend(
			"/Jump To/Previous Key",
			{
				"command" : functools.partial( context.setTime, previousKey.getTime().getSeconds() if previousKey is not None else 0 ),
				"active" : previousKey is not None,
			}
		)

		spanKey = curve.getKey( time ) or previousKey
		spanKeyOnThisFrame = spanKey is not None
		for name in reversed( Gaffer.Animation.Interpolator.getFactory().getNames() ) :
			menuDefinition.prepend(
				"/Set Interpolator/%s" % ( name ),
				{
					"command" : functools.partial(
						__setKeyInterpolator,
						plug,
						spanKey,
						name
					),
					"active" : spanKeyOnThisFrame and plugValueWidget._editable( canEditAnimation = True ),
					"checkBox" : spanKeyOnThisFrame and ( spanKey.getInterpolator().getName() == name )
				}
			)

		closestKey = curve.closestKey( time )
		closestKeyOnThisFrame = closestKey is not None and math.fabs( ( time - closestKey.getTime() ).getSeconds() ) * context.getFramesPerSecond() < 0.5
		menuDefinition.prepend(
			"/Remove Key",
			{
				"command" : functools.partial(
					__removeKey,
					plug,
					closestKey
				),
				"active" : bool( closestKeyOnThisFrame ) and plugValueWidget._editable( canEditAnimation = True ),
			}
		)

	menuDefinition.prepend(
		"/Set Key",
		{
			"command" : functools.partial(
				__setKey,
				plug,
				context
			),
			"active" : plugValueWidget._editable( canEditAnimation = True ),
		}
	)

GafferUI.PlugValueWidget.popupMenuSignal().connect( __popupMenu, scoped = False )
