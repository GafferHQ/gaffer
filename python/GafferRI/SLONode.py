##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

import os

import IECore
import IECoreRI

import Gaffer

class SLONode( Gaffer.Node ) :

	def __init__( self, name="SLONode", inputs={}, dynamicPlugs=() ) :
	
		Gaffer.Node.__init__( self, name )
		
		self.addChild( Gaffer.StringPlug( "name" ) )
		self.addChild( Gaffer.StringPlug( "type" ) )
		self.addChild( Gaffer.CompoundPlug( "parameters" ) )
		self.addChild( Gaffer.ObjectPlug( "out", direction=Gaffer.Plug.Direction.Out ) )
		self._init( inputs, dynamicPlugs )

	def loadShader( self ) :
			
		shader = self.__readShader()
		if not shader :
			return
		
		# set the type plug			
		self["type"].setValue( shader.type )
		
		# remove old plugs which are no longer valid
		parmNames = set( shader.parameters.keys() )
		parmPlugs = self["parameters"].children()
		for parmPlug in parmPlugs :
			if parmPlug.getName() not in parmNames :
				self["parameters"].removeChild( parmPlug )
		
		# add plugs for the current parameters
		types = shader.blindData()["ri:parameterTypeHints"]
		plugTypes = {
			IECore.FloatData.staticTypeId() : Gaffer.FloatPlug,			
			IECore.V3fData.staticTypeId() : Gaffer.V3fPlug,			
			IECore.Color3fData.staticTypeId() : Gaffer.Color3fPlug,			
			IECore.StringData.staticTypeId() : Gaffer.StringPlug,			
		}
		for name, value in shader.parameters.items() :
			plug = plugTypes[value.typeId()]( name=name, flags=Gaffer.Plug.Flags.Dynamic )
			plug.setValue( value.value )
			self["parameters"][name] = plug
		
	def dirty( self, plug ) :
	
		self["out"].setDirty()
		
		if plug.getName()=="name" :
			self.loadShader()
		
	def compute( self, plug ) :
	
		assert( plug.getName()=="out" )
	
		shader = self.__readShader()
		if shader :
			for parmPlug in self["parameters"].children() :
				shader.parameters[parmPlug.getName()].value = parmPlug.getValue()

		plug.setValue( shader )

	def __readShader( self ) :
	
		sp = IECore.SearchPath( os.environ.get( "DL_SHADERS_PATH" ), ":" )
		f = sp.find( self["name"].getValue() + ".sdl" )
		if not f :
			return None
		
		reader = IECoreRI.SLOReader( f )
		return reader.read()
			
IECore.registerRunTimeTyped( SLONode )
