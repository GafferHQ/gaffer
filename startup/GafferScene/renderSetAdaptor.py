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

def __renderSetAdaptor() :

	processor = GafferScene.SceneProcessor()

	processor["__optionQuery"] = GafferScene.OptionQuery()
	processor["__optionQuery"]["scene"].setInput( processor["in"] )

	processor["__optionQuery"].addQuery( Gaffer.StringPlug() )
	processor["__optionQuery"].addQuery( Gaffer.StringPlug() )
	processor["__optionQuery"].addQuery( Gaffer.StringPlug() )

	processor["__optionQuery"]["queries"][0]["name"].setValue( "render:inclusions" )
	processor["__optionQuery"]["queries"][1]["name"].setValue( "render:additionalLights" )
	processor["__optionQuery"]["queries"][2]["name"].setValue( "render:exclusions" )

	processor["__inclusionsFilter"] = GafferScene.SetFilter()
	processor["__inclusionsFilter"]["setExpression"].setInput( processor["__optionQuery"]["out"][0]["value"] )

	processor["__additionalLightsFilter"] = GafferScene.SetFilter()
	# __additionalLightsFilter is only required when `render:additionalLights` exists
	processor["__additionalLightsFilter"]["enabled"].setInput( processor["__optionQuery"]["out"][1]["exists"] )

	processor["__additionalLightsExpression"] = Gaffer.Expression()
	processor["__additionalLightsExpression"].setExpression(
		inspect.cleandoc(
			"""
			additionalLights = parent["__optionQuery"]["out"]["out1"]["value"]
			parent["__additionalLightsFilter"]["setExpression"] = "__lights in ({})".format( additionalLights ) if additionalLights else ""
			"""
		)
	)

	processor["__unionFilter"] = GafferScene.UnionFilter()
	processor["__unionFilter"]["in"]["in0"].setInput( processor["__inclusionsFilter"]["out"] )
	processor["__unionFilter"]["in"]["in1"].setInput( processor["__additionalLightsFilter"]["out"] )

	processor["__isolate"] = GafferScene.Isolate()
	processor["__isolate"]["in"].setInput( processor["in"] )
	processor["__isolate"]["filter"].setInput( processor["__unionFilter"]["out"] )
	# __isolate is only required when `render:inclusions` exists
	processor["__isolate"]["enabled"].setInput( processor["__optionQuery"]["out"][0]["exists"] )
	processor["__isolate"]["keepCameras"].setValue( True )

	processor["__exclusionsFilter"] = GafferScene.SetFilter()
	processor["__exclusionsFilter"]["setExpression"].setInput( processor["__optionQuery"]["out"][2]["value"] )

	processor["__prune"] = GafferScene.Prune()
	processor["__prune"]["in"].setInput( processor["__isolate"]["out"] )
	processor["__prune"]["filter"].setInput( processor["__exclusionsFilter"]["out"] )
	# __prune is only required when `render:exclusions` exists
	processor["__prune"]["enabled"].setInput( processor["__optionQuery"]["out"][2]["exists"] )

	processor["out"].setInput( processor["__prune"]["out"] )

	return processor

GafferScene.SceneAlgo.registerRenderAdaptor( "RenderSetAdaptor", __renderSetAdaptor )
