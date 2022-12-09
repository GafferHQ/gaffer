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
	"nodeGadget:focusGadgetVisible", False,

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

Gaffer.Metadata.registerValue( "Animation.Interpolation.Constant", "description", "Curve span has in key's value." )
Gaffer.Metadata.registerValue( "Animation.Interpolation.ConstantNext", "description", "Curve span has out key's value." )
Gaffer.Metadata.registerValue( "Animation.Interpolation.Linear", "description", "Curve span is linearly interpolated between values of in key and out key." )
Gaffer.Metadata.registerValue( "Animation.Interpolation.Cubic", "description", "Curve span is smoothly interpolated between values of in key and out key using tangent slope." )
Gaffer.Metadata.registerValue( "Animation.Interpolation.Bezier", "description", "Curve span is smoothly interpolated between values of in key and out key using tangent slope and scale." )

Gaffer.Metadata.registerValue( "Animation.Extrapolation.Constant", "description", "Curve is extended as a flat line." )
Gaffer.Metadata.registerValue( "Animation.Extrapolation.Linear", "description", "Curve is extended as a line with slope matching tangent in direction of extrapolation." )

Gaffer.Metadata.registerValue( "Animation.TieMode.Manual", "description", "Tangent slope and scale can be independently adjusted." )
Gaffer.Metadata.registerValue( "Animation.TieMode.Slope", "description", "Tangent slopes are kept equal." )
Gaffer.Metadata.registerValue( "Animation.TieMode.Scale", "description", "Tangent slopes are kept equal and scales are kept proportional." )

# PlugValueWidget popup menu for setting keys
##########################################################################

def __setKey( plug, context ) :

	with context :
		value = plug.getValue()

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		curve = Gaffer.Animation.acquire( plug )
		if isinstance( plug, Gaffer.BoolPlug ) :
			curve.addKey( Gaffer.Animation.Key( context.getTime(), value, Gaffer.Animation.Interpolation.Constant ) )
		else :
			curve.insertKey( context.getTime(), value )

def __removeKey( plug, key ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		curve = Gaffer.Animation.acquire( plug )
		curve.removeKey( key )

def __setKeyInterpolation( plug, key, mode, unused ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		key.setInterpolation( mode )

def __setCurveExtrapolation( plug, curve, direction, mode, unused ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		curve.setExtrapolation( direction, mode )

def __popupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	if not isinstance( plug, Gaffer.ValuePlug ) or not Gaffer.Animation.canAnimate( plug ) :
		return

	context = plugValueWidget.getContext()

	menuDefinition.prepend( "/AnimationDivider", { "divider" : True } )

	if Gaffer.Animation.isAnimated( plug ) :

		curve = Gaffer.Animation.acquire( plug )

		nextKey = curve.nextKey( context.getTime() )
		menuDefinition.prepend(
			"/Jump To/Next Key",
			{
				"command" : functools.partial( context.setTime, nextKey.getTime() if nextKey is not None else 0 ),
				"active" : nextKey is not None,
			}
		)

		previousKey = curve.previousKey( context.getTime() )
		menuDefinition.prepend(
			"/Jump To/Previous Key",
			{
				"command" : functools.partial( context.setTime, previousKey.getTime() if previousKey is not None else 0 ),
				"active" : previousKey is not None,
			}
		)

		for direction in reversed( sorted( Gaffer.Animation.Direction.values.values() ) ) :
			for mode in reversed( sorted( Gaffer.Animation.Extrapolation.values.values() ) ) :
				menuDefinition.prepend(
					"/Extrapolation/%s/%s" % ( direction.name, mode.name ),
					{
						"command" : functools.partial(
							__setCurveExtrapolation,
							plug,
							curve,
							direction,
							mode
						),
						"active" : plugValueWidget._editable( canEditAnimation = True ),
						"checkBox" : curve.getExtrapolation( direction ) == mode,
						"description" : Gaffer.Metadata.value( "Animation.Extrapolation.%s" % mode.name, "description" ),
					}
				)

		spanKey = curve.getKey( context.getTime() ) or previousKey
		spanKeyOnThisFrame = spanKey is not None
		for mode in reversed( sorted( Gaffer.Animation.Interpolation.values.values() ) ) :
			menuDefinition.prepend(
				"/Interpolation/%s" % ( mode.name ),
				{
					"command" : functools.partial(
						__setKeyInterpolation,
						plug,
						spanKey,
						mode
					),
					"active" : spanKeyOnThisFrame and plugValueWidget._editable( canEditAnimation = True ),
					"checkBox" : spanKeyOnThisFrame and ( spanKey.getInterpolation() == mode ),
					"description" : Gaffer.Metadata.value( "Animation.Interpolation.%s" % mode.name, "description" ),
				}
			)

		closestKey = curve.closestKey( context.getTime() )
		closestKeyOnThisFrame = closestKey is not None and math.fabs( context.getTime() - closestKey.getTime() ) * context.getFramesPerSecond() < 0.5
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
