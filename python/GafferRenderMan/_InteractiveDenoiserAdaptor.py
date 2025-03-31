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
import os
import pathlib

import IECore

import Gaffer
import GafferScene

# RenderMan's interactive denoiser is not trivial for a user to set up. It requires
# the insertion of a "man in the middle" driver called `quicklyNoiseless`, and this
# must be fed with a specific set of AOVs. Rather than make folks do this manually,
# this adaptor does it automatically, controlled by some custom options in the scene.
class _InteractiveDenoiserAdaptor( GafferScene.SceneProcessor ) :

	def __init__( self, name = "_InteractiveDenoiserAdaptor" ) :

		GafferScene.SceneProcessor.__init__( self, name )

		self["out"].setInput( self["in"] )

		self["__globalsExpression"] = Gaffer.Expression()
		self["__globalsExpression"].setExpression( inspect.cleandoc(
			"""
			import GafferRenderMan
			parent["out"]["globals"] = GafferRenderMan._InteractiveDenoiserAdaptor._adaptedGlobals( parent["in"]["globals"] )
			"""
		) )

	@staticmethod
	def _adaptedGlobals( inputGlobals ) :

		# Early out if we don't want to enable the denoiser.

		enabled = inputGlobals.get( "option:ri:interactiveDenoiser:enabled" )
		if enabled is None or not enabled.value :
			return inputGlobals

		# Find an output we can base all the denoising AOVs on. We need to know
		# the right values for `displayPort` and other parameters, which we can
		# get this from the beauty output.

		templateOutput = None
		for key, value in inputGlobals.items() :
			if not key.startswith( "output:" ) :
				continue
			if value.getType() not in ( "ieDisplay", "socket" ) :
				continue
			if value.getData() in { "rgb", "rgba" } :
				templateOutput = value.copy()
				break

		if templateOutput is None :
			IECore.msg( IECore.Msg.Warning, "_InteractiveDenoiserAdaptor", "No beauty output found" )
			return inputGlobals

		# Set up the template for the `quicklyNoiseless` driver.

		if templateOutput.getType() == "ieDisplay" :
			templateOutput.parameters()["dspyDSOPath"] = IECore.StringData(
				str( pathlib.Path( __file__ ).parents[2] / "plugins" / "d_ieDisplay.so" )
			)
		else :
			templateOutput.parameters()["dspyDSOPath"] = IECore.StringData(
				str( pathlib.Path( os.environ["RMANTREE"] ) / "lib" / "plugins" / "d_socket.so" )
			)

		templateOutput.setType( "quicklyNoiseless" )
		templateOutput.setName( "denoiser" )

		# Works around RenderMan terminating on renderer shutdown with :
		# ```
		# terminate called after throwing an instance of 'std::runtime_error
		#   what():  Channel not found: Ci.r`
		# ```
		templateOutput.parameters()["immediateClose"] = IECore.BoolData( True )

		qnParameterPrefix = "option:ri:interactiveDenoiser:"
		for name, value in inputGlobals.items() :
			if name.startswith( qnParameterPrefix ) :
				name = name[len(qnParameterPrefix):]
				if name != "enabled" :
					templateOutput.parameters()[name] = value

		# Set the driver up with all the required outputs.

		requiredOutputs = [
			( "beauty", "rgba", "filter" ),
			( "mse", "rgb", "mse" ),
			( "albedo", "lpe nothruput;noinfinitecheck;noclamp;unoccluded;overwrite;C<.S'passthru'>*((U2L)|O)", "filter" ),
			( "albedo_mse", "lpe nothruput;noinfinitecheck;noclamp;unoccluded;overwrite;C<.S'passthru'>*((U2L)|O)", "mse" ),
			( "diffuse", "lpe C(D[DS]*[LO])|[LO]", "filter" ),
			( "diffuse_mse", "lpe C(D[DS]*[LO])|[LO]", "mse" ),
			( "specular", "lpe CS[DS]*[LO]", "filter" ),
			( "specular_mse", "lpe CS[DS]*[LO]", "mse" ),
			( "normal", "lpe nothruput;noinfinitecheck;noclamp;unoccluded;overwrite;CU6L", "filter" ),
			( "normal_mse", "lpe nothruput;noinfinitecheck;noclamp;unoccluded;overwrite;CU6L", "mse" ),
			( "sampleCount", "float sampleCount", "sum" ),
		]

		outputGlobals = inputGlobals.copy()
		for layerName, data, accumulationRule in requiredOutputs :

			output = templateOutput.copy()
			output.setData( data )
			output.parameters()["layerName"] = IECore.StringData( layerName )
			output.parameters()["ri:accumulationRule"] = IECore.StringData( accumulationRule )

			outputGlobals[f"output:{layerName}"] = output

		return outputGlobals

IECore.registerRunTimeTyped( _InteractiveDenoiserAdaptor, typeName = "GafferRenderMan::_InteractiveDenoiserAdaptor" )

GafferScene.SceneAlgo.registerRenderAdaptor( "InteractiveRenderManDenoiserAdaptor", _InteractiveDenoiserAdaptor, "InteractiveRender", "RenderMan" )
