##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import os

import IECore

import GafferSceneUI

if os.environ.get( "CYCLES_ROOT" ) :

	with IECore.IgnoredExceptions( ImportError ) :

		import GafferCycles

		GafferSceneUI.ShaderView.registerRenderer( "cycles", GafferCycles.InteractiveCyclesRender )

		def __cyclesShaderBall() :

			result = GafferCycles.CyclesShaderBall()

			# Reserve some cores for the rest of the UI
			result["threads"]["enabled"].setValue( True )
			result["threads"]["value"].setValue( -3 )

			# Less issues when mixing around OSL shaders
			result["shadingSystem"]["enabled"].setValue( True )
			result["shadingSystem"]["value"].setValue( "OSL" )

			return result

		GafferSceneUI.ShaderView.registerScene( "cycles", "Default", __cyclesShaderBall )

		GafferSceneUI.ShaderView.registerRenderer( "osl", GafferCycles.InteractiveCyclesRender )
		GafferSceneUI.ShaderView.registerScene( "osl", "Default", __cyclesShaderBall )

with IECore.IgnoredExceptions( ImportError ) :

	import GafferArnold
	GafferSceneUI.ShaderView.registerRenderer( "ai", GafferArnold.InteractiveArnoldRender )

	def __arnoldShaderBall() :

		result = GafferArnold.ArnoldShaderBall()

		# Reserve some cores for the rest of the UI
		result["threads"]["enabled"].setValue( True )
		result["threads"]["value"].setValue( -3 )

		return result

	GafferSceneUI.ShaderView.registerScene( "ai", "Default", __arnoldShaderBall )

	# If Arnold is available, then we assume that the user would prefer
	# it over Cycles for OSL previews.
	GafferSceneUI.ShaderView.registerRenderer( "osl", GafferArnold.InteractiveArnoldRender )
	GafferSceneUI.ShaderView.registerScene( "osl", "Default", __arnoldShaderBall )
