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
import GafferUI
import os

class gui( Gaffer.Application ) :

	def __init__( self ) :
	
		Gaffer.Application.__init__( self )
		
		self.parameters().addParameters(
		
			[
				IECore.StringVectorParameter(
					name = "scripts",
					description = "A list of scripts to edit.",
					defaultValue = IECore.StringVectorData()
				)
			]
			
		)
		
		self.parameters().userData()["parser"] = IECore.CompoundObject(
			{
				"flagless" : IECore.StringVectorData( [ "scripts" ] )
			}
		)
		
	def doRun( self, args ) :
	
		self._executeStartupFiles( [ "gui" ] )
	
		application = Gaffer.ApplicationRoot()
		GafferUI.ScriptWindow.connect( application )
		
		if len( args["scripts"] ) :
			for fileName in args["scripts"] :
				scriptNode = Gaffer.ScriptNode( os.path.splitext( os.path.basename( fileName ) )[0] )
				scriptNode["fileName"].setValue( os.path.abspath( fileName ) )
				scriptNode.load()
				application["scripts"].addChild( scriptNode )
		else :
			application["scripts"]["script1"] = Gaffer.ScriptNode()
			
			s = application["scripts"]["script1"]
			n = Gaffer.Node()
			n.addChild( Gaffer.StringPlug( "s1" ) )
			n.addChild( Gaffer.StringPlug( "s2" ) )
			n.addChild( Gaffer.IntPlug( "i1" ) )
			n.addChild( Gaffer.FloatPlug( "f1" ) )
			n.addChild( Gaffer.Color3fPlug( "c1" ) )
			n.addChild( Gaffer.Color4fPlug( "c2" ) )
			
			n["c1"].setValue( IECore.Color3f( 1, 0, 0 ) )
			n["c2"].setValue( IECore.Color4f( 1.0, 0.5, 0.25, 0.5 ) )
			
			c = Gaffer.CompoundPlug( "c" )
			c.addChild( Gaffer.StringPlug( "s1" ) )
			c.addChild( Gaffer.StringPlug( "s2" ) )
			c.addChild( Gaffer.IntPlug( "i1" ) )
			c.addChild( Gaffer.FloatPlug( "f1" ) )
			
			n.addChild( c )
			
			s.addChild( n )
			s.selection().add( n )
								
		GafferUI.EventLoop.start()		
		
		return 0
