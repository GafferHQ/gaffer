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

import inspect

import IECore
import IECoreScene

import Gaffer
import GafferScene

# RenderMan requires three separate setup steps to use Stylized Looks :
#
# 1. Assign PxrStylizedControl shaders to objects.
# 2. Add appropriate display filters.
# 3. Set up a bunch of AOVs used to pass data between the components.
#
# Steps 1 and 2 require user input, because the user will be dialing in the
# settings on the shaders and filters. But setting up the AOVs is fiddly and
# error-prone and shouldn't be left to users. So this adaptor adds the AOVs to
# the scene automatically when it detects that Stylized display filters are
# present.
class _StylizedAOVAdaptor( GafferScene.SceneProcessor ) :

	def __init__( self, name = "_StylizedAOVAdaptor" ) :

		GafferScene.SceneProcessor.__init__( self, name )

		self["out"].setInput( self["in"] )

		self["__globalsExpression"] = Gaffer.Expression()
		self["__globalsExpression"].setExpression( inspect.cleandoc(
			"""
			import GafferRenderMan
			parent["out"]["globals"] = GafferRenderMan._StylizedAOVAdaptor._adaptedGlobals( parent["in"]["globals"] )
			"""
		) )

	__stylizedFilters = {
		"PxrStylizedCanvas", "PxrStylizedHatching", "PxrStylizedLines", "PxrStylizedToon",
	}

	__aovDefinitions = {

		"albedo" : "lpe nothruput;noinfinitecheck;noclamp;unoccluded;overwrite;C<.S'passthru'>*((U2L)|O)",
		"diffuse" : "lpe C(D[DS]*[LO])|[LO]",
		"directSpecular" : "lpe C<RS>[<L.>O]",
		"sampleCount" : "float sampleCount",
		"P" : "color P",
		"NPRshadow" : "lpe shadows;C[DS]+<L.>",

	} | {

		name : f"color {name}"
		for name in [
			"NPRNtriplanar", "NPRPtriplanar", "NPRalbedo", "NPRcurvature",
			"NPRdistort", "NPRhatchOut", "NPRlineAlbedo", "NPRlineCamdist", "NPRmask", "NPRlineNZ",
			"NPRlineOut", "NPRlineOutAlpha", "NPRlineWidth", "NPRoutline", "NPRsections",
			"NPRtextureCoords", "NPRtoonOut", "Nn",
		]

	}

	@staticmethod
	def _adaptedGlobals( inputGlobals ) :

		# See if any of the Stylized Looks display filters are in use. If they're
		# not then we have no work to do.

		displayFilter = inputGlobals.get( "option:ri:displayfilter" )
		if displayFilter is None or not isinstance( displayFilter, IECoreScene.ShaderNetwork ) :
			return inputGlobals

		displayFilters = {
			shader.name for shader in displayFilter.shaders().values()
		}

		if not displayFilters.intersection( _StylizedAOVAdaptor.__stylizedFilters ) :
			return inputGlobals

		# Stylized Looks are in use, so add all the AOVs needed. We use a `null`
		# display driver for this - if the user wants to write them to disk then
		# they can specify separate outputs for that themselves.

		outputGlobals = inputGlobals.copy()
		for aov in _StylizedAOVAdaptor.__aovDefinitions :

			output = IECoreScene.Output(
				aov, "null", _StylizedAOVAdaptor.__aovDefinitions[aov],
				{ "layerName" : aov }
			)
			if aov == "sampleCount" :
				output.parameters()["ri:accumulationRule"] = IECore.StringData( "sum" )

			outputGlobals[f"output:_StylizedAOVAdaptor:{aov}"] = output

		return outputGlobals

IECore.registerRunTimeTyped( _StylizedAOVAdaptor, typeName = "GafferRenderMan::_StylizedAOVAdaptor" )

GafferScene.SceneAlgo.registerRenderAdaptor( "RenderManStylizedAOVAdaptor", _StylizedAOVAdaptor, "*Render", "RenderMan" )
