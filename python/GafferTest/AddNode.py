##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

class AddNode( Gaffer.ComputeNode ) :

	def __init__( self, name="AddNode" ) :

		Gaffer.ComputeNode.__init__( self, name )

		p1 = Gaffer.IntPlug( "op1", Gaffer.Plug.Direction.In )
		p2 = Gaffer.IntPlug( "op2", Gaffer.Plug.Direction.In )

		self.addChild( Gaffer.BoolPlug( "enabled", defaultValue = True ) )
		self.addChild( p1 )
		self.addChild( p2 )

		p3 = Gaffer.IntPlug( "sum", Gaffer.Plug.Direction.Out )

		self.addChild( p3 )

	def enabledPlug( self ) :

		return self["enabled"]

	def correspondingInput( self, output ) :

		if output.isSame( self["sum"] ) :

			return self["op1"]

		return Gaffer.ComputeNode.correspondingInput( self, output )

	def affects( self, input ) :

		outputs = []
		if input.getName() in ( "enabled", "op1", "op2" ) :
			outputs.append( self.getChild( "sum" ) )

		return outputs

	def hash( self, output, context, h ) :

		assert( output.isSame( self.getChild( "sum" ) ) or plug.getFlags() & plug.Flags.Dynamic )

		self.getChild("enabled").hash( h )
		self.getChild("op1").hash( h )
		self.getChild("op2").hash( h )

	def compute( self, plug, context ) :

		# we're allowing the addition of dynamic output plugs which will also receive the sum
		# in order to support GafferTest.ScriptNodeTest.testDynamicPlugSerialisation().
		assert( plug.isSame( self.getChild( "sum" ) ) or plug.getFlags() & plug.Flags.Dynamic )
		assert( isinstance( context, Gaffer.Context ) )
		assert( plug.settable() )
		assert( not self["op1"].settable() )
		assert( not self["op2"].settable() )

		if self["enabled"].getValue() :
			plug.setValue( self.getChild("op1").getValue() + self.getChild("op2").getValue() )
		else :
			plug.setValue( self.getChild("op1").getValue() )

IECore.registerRunTimeTyped( AddNode, typeName = "GafferTest::AddNode" )
