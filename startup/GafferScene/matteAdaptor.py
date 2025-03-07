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

def __matteAdaptor() :

	__matteAttributes = [ "ai:matte", "cycles:use_holdout", "dl:matte", "ri:Ri:Matte" ]

	processor = GafferScene.SceneProcessor()

	processor["__optionQuery"] = GafferScene.OptionQuery()
	processor["__optionQuery"]["scene"].setInput( processor["in"] )

	processor["__optionQuery"].addQuery( Gaffer.StringPlug() )
	processor["__optionQuery"].addQuery( Gaffer.StringPlug() )

	processor["__optionQuery"]["queries"][0]["name"].setValue( "render:matteInclusions" )
	processor["__optionQuery"]["queries"][1]["name"].setValue( "render:matteExclusions" )

	processor["__matteInclusionsFilter"] = GafferScene.SetFilter()
	processor["__matteInclusionsExpression"] = Gaffer.Expression()
	processor["__matteInclusionsExpression"].setExpression(
		inspect.cleandoc(
			"""
			matteInclusions = parent["__optionQuery"]["out"]["out0"]["value"]
			matteExclusions = parent["__optionQuery"]["out"]["out1"]["value"]
			parent["__matteInclusionsFilter"]["setExpression"] = "({}) - ({})".format( matteInclusions, matteExclusions ) if ( matteInclusions and matteExclusions ) else matteInclusions
			"""
		)
	)

	processor["__filterQuery"] = GafferScene.FilterQuery()
	processor["__filterQuery"]["scene"].setInput( processor["in"] )
	processor["__filterQuery"]["filter"].setInput( processor["__matteInclusionsFilter"]["out"] )
	processor["__filterQuery"]["location"].setValue( "/" )

	processor["__allMatte"] = GafferScene.CustomAttributes()
	processor["__allMatte"]["in"].setInput( processor["in"] )
	for attribute in __matteAttributes :
		processor["__allMatte"]["attributes"].addChild( Gaffer.NameValuePlug( attribute, Gaffer.BoolPlug( defaultValue = True ) ) )

	processor["__allMatte"]["global"].setValue( True )
	# all locations are matte if `render:matteInclusions` matches the root of the scene
	processor["__allMatte"]["enabled"].setInput( processor["__filterQuery"]["exactMatch"] )

	processor["__matteInclusions"] = GafferScene.AttributeTweaks()
	processor["__matteInclusions"]["in"].setInput( processor["__allMatte"]["out"] )
	for attribute in __matteAttributes :
		processor["__matteInclusions"]["tweaks"].addChild( Gaffer.TweakPlug( attribute, Gaffer.BoolPlug( defaultValue = True ), mode = Gaffer.TweakPlug.Mode.CreateIfMissing ) )

	processor["__matteInclusions"]["filter"].setInput( processor["__matteInclusionsFilter"]["out"] )
	# __matteInclusions is only required when `render:matteInclusions` exists and the root of the scene hasn't been set as matte
	processor["__matteInclusionsEnabledExpression"] = Gaffer.Expression()
	processor["__matteInclusionsEnabledExpression"].setExpression(
		"""parent["__matteInclusions"]["enabled"] = parent["__optionQuery"]["out"]["out0"]["exists"] and not parent["__filterQuery"]["exactMatch"]"""
	)

	processor["__matteExclusionsFilter"] = GafferScene.SetFilter()
	processor["__matteExclusionsFilter"]["setExpression"].setInput( processor["__optionQuery"]["out"][1]["value"] )

	processor["__matteExclusions"] = GafferScene.AttributeTweaks()
	processor["__matteExclusions"]["in"].setInput( processor["__matteInclusions"]["out"] )
	for attribute in __matteAttributes :
		processor["__matteExclusions"]["tweaks"].addChild( Gaffer.TweakPlug( attribute, Gaffer.BoolPlug(), mode = Gaffer.TweakPlug.Mode.CreateIfMissing ) )

	processor["__matteExclusions"]["filter"].setInput( processor["__matteExclusionsFilter"]["out"] )
	# __matteExclusions is only required when `render:matteExclusions` exists
	processor["__matteExclusions"]["enabled"].setInput( processor["__optionQuery"]["out"][1]["exists"] )

	processor["out"].setInput( processor["__matteExclusions"]["out"] )

	return processor

GafferScene.SceneAlgo.registerRenderAdaptor( "MatteAdaptor", __matteAdaptor )
