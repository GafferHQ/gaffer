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

import IECore

import Gaffer
import GafferScene
import GafferArnold

# Register a render adaptor that inserts a `color_manager_ocio` driven
# by the OpenColorIOAlgo context, if no Arnold color manager exists in the
# scene already.

def __ocioColorManagerAdaptor() :

	result = GafferScene.SceneProcessor()

	result["colorManager"] = GafferArnold.ArnoldColorManager()
	result["colorManager"].loadColorManager( "color_manager_ocio" )
	result["colorManager"]["in"].setInput( result["in"] )
	result["colorManager"]["parameters"]["config"].setValue( "${ocio:config}" )
	result["colorManager"]["parameters"]["color_space_linear"].setValue( "${ocio:workingSpace}" )
	# This is the least convincing of the defaults, but the `matte_paint` role is `sRGB` for
	# both the ACES 1.3 and the Gaffer 1.2 Legacy configs, which seems a decent guess for a
	# low bit depth file.
	result["colorManager"]["parameters"]["color_space_narrow"].setValue( "matte_paint" )

	result["optionQuery"] = GafferScene.OptionQuery()
	result["optionQuery"]["scene"].setInput( result["in"] )
	result["optionQuery"].addQuery( Gaffer.ObjectPlug( defaultValue = IECore.NullObject().defaultNullObject() ), "ai:color_manager" )

	result["expression"] = Gaffer.Expression()
	result["expression"].setExpression(
		"""parent["colorManager"]["enabled"] = not parent["optionQuery"]["out"]["out0"]["exists"]"""
	)

	result["out"].setInput( result["colorManager"]["out"] )

	return result

GafferScene.SceneAlgo.registerRenderAdaptor( "DefaultArnoldColorManager", __ocioColorManagerAdaptor )
