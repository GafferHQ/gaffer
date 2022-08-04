##########################################################################
#
#  Copyright (c) 2018, Alex Fuller. All rights reserved.
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

import Gaffer
import GafferCycles

## \todo Refactor the GafferScene::Light base class so this can be
# registered there, and work for all subclasses. The main issue is that
# there is no simple generic way of querying the required "ai:light:"
# prefix from the subclass.
def __parameterUserDefault( plug ) :

	light = plug.node()
	return Gaffer.Metadata.value(
		"ccl:light:" + light["__shader"]["name"].getValue() + ":" + plug.relativeName( light["parameters"] ),
		"userDefault"
	)

Gaffer.Metadata.registerNode(

	GafferCycles.CyclesLight,

	plugs = {

		"parameters.*" : [

			# Most light parameters are not connectable.
			"nodule:type", "",

		],

		"parameters..." : [

			"userDefault", __parameterUserDefault,

		],

		# Metadata for "virtual" parameters that don't exist
		# in the Cycles API, and therefore won't have metadata
		# provided via CyclesShaderUI.

		"parameters.exposure" : [

			"nodule:type", ""

		],

	}

)
