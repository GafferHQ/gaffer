##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

import types

import Gaffer

# In Gaffer 1.7, points were stored directly on the RampPlug rather than
# in a `points` container, and they were serialised with `addChild()` rather
# than `addPoint()`. We redirect `addChild()` to convert such serialisations
# to the new form.
def __addChild( self, child ) :

	# Create a point using the official API. We'll use this instead of `child`.
	pointPlug = self["points"][self.addPoint()]

	# Add metadata to forward the old name to the child of `points`.
	Gaffer.Metadata.registerValue(
		self,
		"compatibility:childAlias:{name}".format( name = child.getName() ),
		"points.{name}".format( name = pointPlug.getName() ),
		persistent = False
	)

def __pointPlugAddChild( self, child ) :

	# The `x/y` component is being added in an old serialisation.
	# We don't need the plug because `addPoint()` created it already,
	# but we do need to transfer over its default value.

	componentPlug = self[child.getName()]
	componentPlug.setValue( child.defaultValue() )
	componentPlug.resetDefault()

def __getItemWrapper( originalGetItem ) :

	def getItem( self, key ) :

		item = originalGetItem( self, key )
		if key not in ( "interpolation", "points" ) :
			# We're accessing a point from an old serialisation. Inject
			# an `addChild()` function to handle the calls made to add the
			# `x` and `y` child plugs.
			item.addChild = types.MethodType( __pointPlugAddChild, item )

		return item

	return getItem

for plugType in ( Gaffer.RampffPlug, Gaffer.RampfColor3fPlug, Gaffer.RampfColor4fPlug ) :
	plugType.addChild = __addChild
	plugType.__getitem__ = __getItemWrapper( plugType.__getitem__ )
