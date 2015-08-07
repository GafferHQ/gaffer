##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

# Backwards compatibility for nodes which have migrated from using
# an InputGenerator into using an ArrayPlug instead. This is requested
# on a per-node basis by setting an "enableInputGeneratorCompatibility"
# attribute to True. See startup/GafferImage/inputGeneratorCompatibility.py for
# an example.

def __nodeGetItem( self, key ) :

	if getattr( self, "enableInputGeneratorCompatibility", False ) :
		if key == "in" :
			# We now have an ArrayPlug where we used to have an ImagePlug.
			# Enable the required compatibility methods.
			result = Gaffer.Node.__originalGetItem( self, key )
			result.enableInputGeneratorCompatibility = True
			return result

		m = re.match( "^in([0-9]+)$", key )
		if m :
			# These were originally plugs parented directly to the node,
			# and are now children of the array plug.
			return Gaffer.Node.__originalGetItem( self, "in" )[int( m.group( 1 ) )]
		
	return Gaffer.Node.__originalGetItem( self, key )

def __arrayPlugSetInput( self, input ) :

	if getattr( self, "enableInputGeneratorCompatibility", False ) :
		if len( self ) and isinstance( input, self[0].__class__ ) :
			self[0].setInput( input )
			return

	Gaffer.ArrayPlug.__originalSetInput( self, input )

def __arrayPlugGetItem( self, key ) :

	if getattr( self, "enableInputGeneratorCompatibility", False ) :
		try :
			return Gaffer.ArrayPlug.__originalGetItem( self, key )
		except KeyError :
			try :
				return Gaffer.ArrayPlug.__originalGetItem( self, 0 )[key]
			except :
				raise e

	return Gaffer.ArrayPlug.__originalGetItem( self, key )

if not hasattr( Gaffer.Node, "__originalGetItem" ) :

	Gaffer.Node.__originalGetItem = Gaffer.Node.__getitem__
	Gaffer.Node.__getitem__ = __nodeGetItem

	Gaffer.ArrayPlug.__originalSetInput = Gaffer.ArrayPlug.setInput
	Gaffer.ArrayPlug.setInput = __arrayPlugSetInput

	Gaffer.ArrayPlug.__originalGetItem = Gaffer.ArrayPlug.__getitem__
	Gaffer.ArrayPlug.__getitem__ = __arrayPlugGetItem
