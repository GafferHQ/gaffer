##########################################################################
#
#  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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

import re

import Gaffer
import GafferUI
import GafferSceneUI

import imath

# The signature for CompoundEditor.__init__ has changed some:
#  - 0.54.0.0 introduced 'windowState' and 'detachedPanels'
#  - 0.54.3.x migrated to the opaque _state dict
# We need to patch the constructor such that it only receives the args that
# it expects

# compatibility version only contains milestone/major
layoutCompatVersion = Gaffer.About.compatibilityVersion() * 1000 + Gaffer.About.minorVersion()

if layoutCompatVersion <= 54002 :

	def __initWrapper( originalInit ) :

		def init( self, *args, **kwargs ) :

			if Gaffer.About.compatibilityVersion() < 54 :

				toMigrate = ( "children", )
				toRemove = ( "windowState", "detachedPanels", "_state" )

			else :

				toMigrate = ( "children", "windowState", "detachedPanels" )
				toRemove = ()

			if "_state" in kwargs :
				for arg in toMigrate :
					if arg in kwargs[ "_state" ] :
						kwargs[ arg ] = kwargs[ "_state" ][ arg ]
				del kwargs[ "_state" ]

			for arg in toRemove :
				if arg in kwargs :
					del kwargs[ arg ]

			originalInit( self, *args, **kwargs )

		return init

	GafferUI.CompoundEditor.__init__ = __initWrapper( GafferUI.CompoundEditor.__init__ )

# 0.54.0.0 introduces a dependency on imath in its serialisation, so we need
# to modify the eval context in older versions so we don't error evaluating the
# repr, even though we fixed the constructor args above.

if Gaffer.About.compatibilityVersion() < 54 :

	# windowState requires imath, so we need to modify the eval environment

	def __create( self, name, scriptNode ) :

		layout = self._Layouts__namedLayouts[name]

		# first try to import the modules the layout needs
		contextDict = { "scriptNode" : scriptNode, "imath" : imath }
		imported = set()
		classNameRegex = re.compile( "[a-zA-Z]*Gaffer[^(,]*\(" )
		for className in classNameRegex.findall( layout.repr ) :
			moduleName = className.partition( "." )[0]
			if moduleName not in imported :
				exec( "import %s" % moduleName, contextDict, contextDict )
				imported.add( moduleName )

		return eval( layout.repr, contextDict, contextDict )

	GafferUI.Layouts.create = __create

# UVEditor was also added, which can cause hard failures in old versions,
# so we'll patch this with the closest thing...
if not hasattr( GafferSceneUI, 'UVInspector' ) :
	GafferSceneUI.UVInspector = GafferSceneUI.PrimitiveInspector
