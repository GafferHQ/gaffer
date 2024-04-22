##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import inspect

import Gaffer
import GafferScene

def __cameraVisibilityAdaptor() :

	processor = GafferScene.SceneProcessor()

	processor["__optionQuery"] = GafferScene.OptionQuery()
	processor["__optionQuery"]["scene"].setInput( processor["in"] )

	processor["__optionQuery"].addQuery( Gaffer.StringPlug() )
	processor["__optionQuery"].addQuery( Gaffer.StringPlug() )

	processor["__optionQuery"]["queries"][0]["name"].setValue( "render:cameraInclusions" )
	processor["__optionQuery"]["queries"][1]["name"].setValue( "render:cameraExclusions" )

	processor["__cameraInclusionsFilter"] = GafferScene.SetFilter()
	processor["__cameraInclusionsExpression"] = Gaffer.Expression()
	processor["__cameraInclusionsExpression"].setExpression(
		inspect.cleandoc(
			"""
			cameraInclusions = parent["__optionQuery"]["out"]["out0"]["value"]
			cameraExclusions = parent["__optionQuery"]["out"]["out1"]["value"]
			parent["__cameraInclusionsFilter"]["setExpression"] = "({}) - ({})".format( cameraInclusions, cameraExclusions ) if ( cameraInclusions and cameraExclusions ) else cameraInclusions
			"""
		)
	)

	processor["__filterQuery"] = GafferScene.FilterQuery()
	processor["__filterQuery"]["scene"].setInput( processor["in"] )
	processor["__filterQuery"]["filter"].setInput( processor["__cameraInclusionsFilter"]["out"] )
	processor["__filterQuery"]["location"].setValue( "/" )

	processor["__allCameraExcluded"] = GafferScene.CustomAttributes()
	processor["__allCameraExcluded"]["in"].setInput( processor["in"] )
	processor["__allCameraExcluded"]["attributes"].addChild( Gaffer.NameValuePlug( "ai:visibility:camera", Gaffer.BoolPlug() ) )
	processor["__allCameraExcluded"]["attributes"].addChild( Gaffer.NameValuePlug( "cycles:visibility:camera", Gaffer.BoolPlug() ) )
	processor["__allCameraExcluded"]["attributes"].addChild( Gaffer.NameValuePlug( "dl:visibility.camera", Gaffer.BoolPlug() ) )
	processor["__allCameraExcluded"]["global"].setValue( True )
	# __allCameraExcluded is only required when `render:cameraInclusions` exists and does not match the root of the scene.
	processor["__allCameraExcludedExpression"] = Gaffer.Expression()
	processor["__allCameraExcludedExpression"].setExpression(
		"""parent["__allCameraExcluded"]["enabled"] = parent["__optionQuery"]["out"]["out0"]["exists"] and not parent["__filterQuery"]["exactMatch"]"""
	)

	processor["__cameraInclusions"] = GafferScene.AttributeTweaks()
	processor["__cameraInclusions"]["in"].setInput( processor["__allCameraExcluded"]["out"] )
	processor["__cameraInclusions"]["tweaks"].addChild( Gaffer.TweakPlug( "ai:visibility:camera", Gaffer.BoolPlug( defaultValue = True ), mode = Gaffer.TweakPlug.Mode.CreateIfMissing ) )
	processor["__cameraInclusions"]["tweaks"].addChild( Gaffer.TweakPlug( "cycles:visibility:camera", Gaffer.BoolPlug( defaultValue = True ), mode = Gaffer.TweakPlug.Mode.CreateIfMissing ) )
	processor["__cameraInclusions"]["tweaks"].addChild( Gaffer.TweakPlug( "dl:visibility.camera", Gaffer.BoolPlug( defaultValue = True ), mode = Gaffer.TweakPlug.Mode.CreateIfMissing ) )

	processor["__cameraInclusions"]["filter"].setInput( processor["__cameraInclusionsFilter"]["out"] )
	# __cameraInclusions is only required when `render:cameraInclusions` exists
	processor["__cameraInclusions"]["enabled"].setInput( processor["__optionQuery"]["out"][0]["exists"] )

	processor["__cameraExclusionsFilter"] = GafferScene.SetFilter()
	processor["__cameraExclusionsFilter"]["setExpression"].setInput( processor["__optionQuery"]["out"][1]["value"] )

	processor["__cameraExclusions"] = GafferScene.AttributeTweaks()
	processor["__cameraExclusions"]["in"].setInput( processor["__cameraInclusions"]["out"] )
	processor["__cameraExclusions"]["tweaks"].addChild( Gaffer.TweakPlug( "ai:visibility:camera", Gaffer.BoolPlug(), mode = Gaffer.TweakPlug.Mode.CreateIfMissing ) )
	processor["__cameraExclusions"]["tweaks"].addChild( Gaffer.TweakPlug( "cycles:visibility:camera", Gaffer.BoolPlug(), mode = Gaffer.TweakPlug.Mode.CreateIfMissing ) )
	processor["__cameraExclusions"]["tweaks"].addChild( Gaffer.TweakPlug( "dl:visibility.camera", Gaffer.BoolPlug(), mode = Gaffer.TweakPlug.Mode.CreateIfMissing ) )

	processor["__cameraExclusions"]["filter"].setInput( processor["__cameraExclusionsFilter"]["out"] )
	# __cameraExclusions is only required when `render:cameraExclusions` exists
	processor["__cameraExclusions"]["enabled"].setInput( processor["__optionQuery"]["out"][1]["exists"] )

	processor["out"].setInput( processor["__cameraExclusions"]["out"] )

	return processor

GafferScene.SceneAlgo.registerRenderAdaptor( "CameraVisibilityAdaptor", __cameraVisibilityAdaptor )
