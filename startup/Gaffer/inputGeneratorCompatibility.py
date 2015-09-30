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
# by calling `ArrayPlug.enableInputGeneratorCompatibility( nodeType )`
# for a particular node type.

def __nodeGetItem( self, key ) :

	if key == "in" :
		# We now have an ArrayPlug where we used to have an element plug.
		# Enable the required compatibility methods.
		result = self.__originalGetItem( key )
		result.enableInputGeneratorCompatibility = True
		return result

	m = re.match( "^in([0-9]+)$", key )
	if m :
		# These were originally plugs parented directly to the node,
		# and are now children of the array plug.
		return self.__originalGetItem( "in" )[int( m.group( 1 ) )]

	return self.__originalGetItem( key )

def __nodeAddChild( self, child ) :

	if re.match( "^in([0-9]+)$", child.getName() ) :
		# This was an old input created by an InputGenerator.
		# Add it to the new array plug instead.
		self["in"].addChild( child )
		return

	self.__originalAddChild( child )

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
			if key == self.getName() :
				# Some nodes (I'm looking at you UnionFilter) used to
				# name their first child without a numeric suffix.
				return Gaffer.ArrayPlug.__originalGetItem( self, 0 )
			else :
				# Simulate access to the child of the first plug in an
				# old InputGenerator.
				return Gaffer.ArrayPlug.__originalGetItem( self, 0 )[key]

	return Gaffer.ArrayPlug.__originalGetItem( self, key )

def __arrayPlugHash( self ) :

	if getattr( self, "enableInputGeneratorCompatibility", False ) :
		return self[0].hash() if isinstance( self[0], Gaffer.ValuePlug ) else None

	raise AttributeError( "'ArrayPlug' object has no attribute 'hash'" )

def __arrayPlugGetValue( self ) :

	if getattr( self, "enableInputGeneratorCompatibility", False ) :
		return self[0].getValue() if isinstance( self[0], Gaffer.ValuePlug ) else None

	raise AttributeError( "'ArrayPlug' object has no attribute 'getValue'" )

@staticmethod
def __enableInputGeneratorCompatibility( nodeType ) :

	if not hasattr( nodeType, "__originalGetItem" ) :

		nodeType.__originalGetItem = nodeType.__getitem__
		nodeType.__getitem__ = __nodeGetItem

		nodeType.__originalAddChild = nodeType.addChild
		nodeType.addChild = __nodeAddChild

if not hasattr( Gaffer.ArrayPlug, "__originalGetItem" ) :

	Gaffer.ArrayPlug.__originalSetInput = Gaffer.ArrayPlug.setInput
	Gaffer.ArrayPlug.setInput = __arrayPlugSetInput

	Gaffer.ArrayPlug.__originalGetItem = Gaffer.ArrayPlug.__getitem__
	Gaffer.ArrayPlug.__getitem__ = __arrayPlugGetItem

	Gaffer.ArrayPlug.hash = __arrayPlugHash
	Gaffer.ArrayPlug.getValue = __arrayPlugGetValue

	Gaffer.ArrayPlug.enableInputGeneratorCompatibility = __enableInputGeneratorCompatibility

Gaffer.ArrayPlug.enableInputGeneratorCompatibility( Gaffer.SwitchDependencyNode )
Gaffer.ArrayPlug.enableInputGeneratorCompatibility( Gaffer.SwitchComputeNode )
