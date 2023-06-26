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

import Gaffer

# Backwards compatibility for old `preferences.py` files that reference the
# `displayColorSpace` plug we had before we moved all color management into
# settings on the ScriptNode.

def __preferencesGetItemWrapper( originalGetItem ) :

	def getItem( self, key ) :

		if key == "displayColorSpace" and key not in self :
			# This plug no longer exists, so we provide a non-serialisable
			# surrogate just to keep old scripts loading without
			# error.
			self["displayColorSpace"] = Gaffer.Plug( "displayColorSpace", flags = Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.Serialisable )
			self["displayColorSpace"]["view"] = Gaffer.StringPlug()
			self["displayColorSpace"]["context"] = Gaffer.CompoundDataPlug()
			Gaffer.Metadata.registerValue( self["displayColorSpace"], "layout:visibilityActivator", False )

		return originalGetItem( self, key )

	return getItem

Gaffer.Preferences.__getitem__ = __preferencesGetItemWrapper( Gaffer.Preferences.__getitem__ )
