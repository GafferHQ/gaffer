##########################################################################
#
#  Copyright (c) 2015, John Haddon. All rights reserved.
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

import functools

import Gaffer
import GafferArnold

# Defer parameter metadata lookups to the internal shader node
# aside from nodule:type, which we handle manually to prevent
# some connectable plugs appearing.

## \todo Refactor the GafferScene::Light base class so this can be
# registered there, and work for all subclasses. The main issue is that
# there is no simple generic way of querying the required "ai:light:"
# prefix from the subclass.
def __parameterUserDefault( plug ) :

	light = plug.node()
	return Gaffer.Metadata.value(
		"ai:light:" + light["__shader"]["name"].getValue() + ":" + plug.relativeName( light["parameters"] ),
		"userDefault"
	)

Gaffer.Metadata.registerNode(

	GafferArnold.ArnoldLight,

	plugs = {

		"parameters..." : [

			"userDefault", __parameterUserDefault,

		],

		"parameters.*" : [

			# Most light parameters are not connectable.
			"nodule:type", "",

		],

		"parameters.color" : [

			# The color parameter on quad and skydome lights is connectable.
			"nodule:type", lambda plug : "GafferUI::StandardNodule" if plug.node()["__shader"]["name"].getValue() in ( "quad_light", "skydome_light" ) else ""

		],

		"parameters.shader" : [

			# The shader parameter, which only exists on skydome lights, is connectable.
			"nodule:type", "GafferUI::StandardNodule"

		],

	}

)
