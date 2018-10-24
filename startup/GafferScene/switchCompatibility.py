##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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
import GafferScene

##########################################################################
# Simple stubs for the old specialised Switch nodes.
##########################################################################

class SceneSwitch( Gaffer.Switch ) :

	def __init__( self, name = "SceneSwitch" ) :

		Gaffer.Switch.__init__( self, name )
		self.setup( GafferScene.ScenePlug() )

GafferScene.SceneSwitch = SceneSwitch

class ShaderSwitch( Gaffer.Switch ) :

	def __init__( self, name = "ShaderSwitch" ) :

		Gaffer.Switch.__init__( self, name )

	def __getitem__( self, key ) :

		if key in ( "in", "out" ) and key not in self :
			self.setup( Gaffer.Plug() )

		return Gaffer.SwitchComputeNode.__getitem__( self, key )

GafferScene.ShaderSwitch = ShaderSwitch

class FilterSwitch( Gaffer.Switch ) :

	def __init__( self, name = "FilterSwitch" ) :

		Gaffer.Switch.__init__( self, name )
		self.setup( GafferScene.FilterPlug( flags = Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.Cacheable ) )

GafferScene.FilterSwitch = FilterSwitch

##########################################################################
# Code to auto-convert old IntPlugs to FilterPlugs when adding
# children to FilterProcessor.in. This maintains compatibility with
# files prior to version 0.28.0.0.
##########################################################################

def __filterProcessorAddChild( self, child ) :

	if type( child ) == Gaffer.IntPlug :
		scriptNode = self.ancestor( Gaffer.ScriptNode )
		if scriptNode is not None and scriptNode.isExecuting() :
			child = GafferScene.FilterPlug( name = child.getName(), direction = child.direction(), flags = child.getFlags() )

	self.__class__.addChild( self, child )

def __filterProcessorGetItemWrapper( originalGetItem ) :

	def getItem( self, key ) :

		result = originalGetItem( self, key )
		if key == "in" and isinstance( result, Gaffer.ArrayPlug ) :
			if len( result ) and isinstance( result[0], GafferScene.FilterPlug ) :
				result.addChild = types.MethodType( __filterProcessorAddChild, result )

		return result

	return getItem

Gaffer.Switch.__getitem__ = __filterProcessorGetItemWrapper( Gaffer.Switch.__getitem__ )
GafferScene.FilterProcessor.__getitem__ = __filterProcessorGetItemWrapper( GafferScene.FilterProcessor.__getitem__ )
