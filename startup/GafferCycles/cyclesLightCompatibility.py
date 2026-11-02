##########################################################################
#
#  Copyright (c) 2026, Alex Fuller. All rights reserved.
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

_original_getitem = Gaffer.GraphComponent.__getitem__

def __compatibility_getitem( self, key ) :

	try:
		return _original_getitem( self, key )

	except KeyError:
		node = self if isinstance( self, Gaffer.Node ) else self.ancestor( Gaffer.Node )
		if node:
			node_name = node.getName().lower()
			target_key = None

			if key == "size" and "point_light" in node_name or "spot_light" in node_name :
				target_key = "radius"
			if "spot_light" in node_name :
				if key = "spot_angle" :
					target_key = "angle"
				elif key = "spot_smooth" :
					target_key = "smooth"

			if target_key:
				if target_key in self:
					return _original_getitem( self, target_key )
				elif hasattr( self, "parameters" ) and target_key in self["parameters"]:
					return _original_getitem( self["parameters"], target_key )

		raise

Gaffer.GraphComponent.__getitem__ = __compatibility_getitem
