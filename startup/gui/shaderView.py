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

import IECore

import GafferSceneUI

with IECore.IgnoredExceptions( ImportError ) :

	import GafferAppleseed
	GafferSceneUI.ShaderView.registerRenderer( "osl", GafferAppleseed.InteractiveAppleseedRender )

	def __appleseedShaderBall() :

		result = GafferAppleseed.AppleseedShaderBall()

		# Limit the number of samples.
		result["maxSamples"]["enabled"].setValue( True )
		result["maxSamples"]["value"].setValue( 32 )

		# Reserve some cores for the rest of the UI
		result["threads"]["enabled"].setValue( True )
		result["threads"]["value"].setValue( -3 )

		return result

	GafferSceneUI.ShaderView.registerScene( "osl", "Default", __appleseedShaderBall )

with IECore.IgnoredExceptions( ImportError ) :

	import GafferRenderMan
	GafferSceneUI.ShaderView.registerRenderer( "ri", GafferRenderMan.InteractiveRenderManRender )
	GafferSceneUI.ShaderView.registerScene( "ri", "Default", GafferRenderMan.RenderManShaderBall )

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
