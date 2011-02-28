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

import IECore

import Gaffer

class WriteNode( Gaffer.Node ) :

	def __init__( self, name="Write", inputs={}, dynamicPlugs=() ) :
	
		Gaffer.Node.__init__( self, name )
		
		inPlug = Gaffer.ObjectPlug( "in", Gaffer.Plug.Direction.In )
		self.addChild( inPlug )
		
		fileNamePlug = Gaffer.StringPlug( "filename", Gaffer.Plug.Direction.In )
		self.addChild( fileNamePlug )
		
		resultPlug = Gaffer.StringPlug( "output", Gaffer.Plug.Direction.Out )
		self.addChild( resultPlug )
		
		self._init( inputs, dynamicPlugs )

	def dirty( self, plug ) :
	
		if plug.getName()=="filename" or plug.getName()=="in" :
		
			self["output"].setDirty()
			
	def compute( self, plug ) :
	
		assert( plug.isSame( self["output"] ) )
		
		filename = self["filename"].getValue()
		if filename :
			
			writer = IECore.Writer.create( self["in"].getValue(), filename )
			if writer :
				writer.write()
		
		plug.setValue( filename )

IECore.registerRunTimeTyped( WriteNode )
