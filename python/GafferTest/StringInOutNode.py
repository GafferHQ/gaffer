##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import IECore
import Gaffer

class StringInOutNode( Gaffer.ComputeNode ) :

	def __init__( self, name="StringInOutNode", defaultValue="", substitutions = IECore.StringAlgo.Substitutions.AllSubstitutions ) :

		Gaffer.ComputeNode.__init__( self, name )

		self.addChild( Gaffer.StringPlug( "in", Gaffer.Plug.Direction.In, defaultValue, substitutions = substitutions ) )
		self.addChild( Gaffer.StringPlug( "out", Gaffer.Plug.Direction.Out ) )

		self.numHashCalls = 0
		self.numComputeCalls = 0

	def affects( self, input ) :

		outputs = Gaffer.ComputeNode.affects( self, input )

		if input.isSame( self["in"] ) :
			outputs.append( self["out"] )

		return outputs

	def hash( self, output, context, h ) :

		if output.isSame( self["out"] ) :
			self["in"].hash( h )

		self.numHashCalls += 1

	def compute( self, plug, context ) :

		if plug.isSame( self["out"] ) :
			plug.setValue( self["in"].getValue() )

		self.numComputeCalls += 1

IECore.registerRunTimeTyped( StringInOutNode, typeName = "GafferTest::StringInOutNode" )
