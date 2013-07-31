##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

## This class is used by the CompoundPlugTest.
class CompoundPlugNode( Gaffer.DependencyNode ) :

	def __init__( self, name="CompoundPlugNode" ) :
	
		Gaffer.DependencyNode.__init__( self, name )
		
		p = Gaffer.CompoundPlug( name = "p" )
		c1 = Gaffer.FloatPlug( name = "f" )
		c2 = Gaffer.StringPlug( name = "s" )
		p.addChild( c1 )
		p.addChild( c2 )
		self.addChild( p )
		
		po = Gaffer.CompoundPlug( name = "o", direction = Gaffer.Plug.Direction.Out )
		co1 = Gaffer.FloatPlug( name = "f", direction = Gaffer.Plug.Direction.Out )
		co2 = Gaffer.StringPlug( name = "s", direction = Gaffer.Plug.Direction.Out )
		po.addChild( co1 )
		po.addChild( co2 )
		self.addChild( po )

		# for CompoundPlugTest.testSerialisationOfDynamicPlugsOnNondynamicParent().
		self.addChild( Gaffer.CompoundPlug( name = "nonDynamicParent" ) )
				
	def affects( self, inputPlug ) :
	
		outputs = Gaffer.DependencyNode.affects( self, inputPlug )
		
		if inputPlug.parent().isSame( self["p"] ) :
			outputs.append( self["o"][inputPlug.getName()] )
			
		return outputs
		
IECore.registerRunTimeTyped( CompoundPlugNode, typeName = "GafferTest::CompoundPlugNode" )
