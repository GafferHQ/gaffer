##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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

import PyOpenColorIO

import Gaffer
import GafferUI
import GafferImageUI
import GafferArnold

def __parameterUserDefault( plug ) :

	node = plug.node()
	return Gaffer.Metadata.value(
		"ai:color_manager:" + node["__shader"]["name"].getValue() + ":" + plug.relativeName( node["parameters"] ),
		"userDefault"
	)

def __ocioConfig( plug ) :

	try :
		context = GafferUI.ContextTracker.acquireForFocus( plug ).context( plug )
		with context :
			if plug.node()["__shader"]["name"].getValue() != "color_manager_ocio" :
				return None
			config = context.substitute( plug.node()["parameters"]["config"].getValue() )
		if not config :
			return PyOpenColorIO.GetCurrentConfig()
		else :
			return PyOpenColorIO.Config.CreateFromFile( context.substitute( config ) )
	except :
		return None

def __colorSpacePresetNames( plug ) :

	config = __ocioConfig( plug )
	if config is None :
		return None

	return GafferImageUI.OpenColorIOTransformUI.colorSpacePresetNames(
		plug, config = config
	)


def __colorSpacePresetValues( plug ) :

	config = __ocioConfig( plug )
	if config is None :
		return None

	return GafferImageUI.OpenColorIOTransformUI.colorSpacePresetValues(
		plug, config = config
	)

def __colorSpacePlugValueWidget( plug ) :

	if __ocioConfig( plug ) is None :
		return None
	else :
		return "GafferUI.PresetsPlugValueWidget"

Gaffer.Metadata.registerNode(

	GafferArnold.ArnoldColorManager,

	"description",
	"""
	Specifies the colour manager to be used in Arnold renders. This is represented
	in the scene as an option called `ai:color_manager`.
	""",

	plugs = {

		"parameters" : [

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",

			"description",
			"""
			The parameters for the colour manager.
			""",

		],

		"parameters..." : [

			"userDefault", __parameterUserDefault,

		],

		"parameters.color_space_narrow" : [

			"presetNames", __colorSpacePresetNames,
			"presetValues", __colorSpacePresetValues,
			"plugValueWidget:type", __colorSpacePlugValueWidget,
			"openColorIO:includeRoles", True,

		],

		"parameters.color_space_linear" : [

			"presetNames", __colorSpacePresetNames,
			"presetValues", __colorSpacePresetValues,
			"plugValueWidget:type", __colorSpacePlugValueWidget,
			"openColorIO:includeRoles", True,

		]

	}

)
