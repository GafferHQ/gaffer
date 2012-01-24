##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

class SphereNode( Gaffer.Node ) :

	def __init__( self, name="Sphere", inputs={}, dynamicPlugs=() ) :
	
		Gaffer.Node.__init__( self, name )
		
		radiusPlug = Gaffer.FloatPlug( name="radius", defaultValue=1, minValue=0 )
		self.addChild( radiusPlug )
		
		zMinPlug = Gaffer.FloatPlug( name="zMin", defaultValue=-1, minValue=-1, maxValue=1 )
		self.addChild( zMinPlug )
		
		zMaxPlug = Gaffer.FloatPlug( name="zMax", defaultValue=1, minValue=-1, maxValue=1 )
		self.addChild( zMaxPlug )
		
		thetaPlug = Gaffer.FloatPlug( name="theta", defaultValue=360, minValue=0, maxValue=360 )
		self.addChild( thetaPlug )
		
		resultPlug = Gaffer.ObjectPlug( "output", Gaffer.Plug.Direction.Out )
		self.addChild( resultPlug )
		
		self._init( inputs, dynamicPlugs )

	def dirty( self, plug ) :
	
		if plug.getName() in ( "radius", "zMin", "zMax", "theta" ) :
		
			self["output"].setDirty()
			
	def compute( self, plug, context ) :
	
		assert( plug.isSame( self["output"] ) )
		
		result = IECore.SpherePrimitive( self["radius"].getValue(), self["zMin"].getValue(), self["zMax"].getValue(), self["theta"].getValue() )
		plug.setValue( result )

IECore.registerRunTimeTyped( SphereNode )
