##########################################################################
#  
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

import os
import unittest
import subprocess

import IECore

import Gaffer
import GafferScene
import GafferRenderMan

class RenderManRenderTest( unittest.TestCase ) :

	__scriptFileName = "/tmp/test.gfr"
		
	def testBoundsAndImageOutput( self ) :
	
		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["plane"]["transform"]["translate"].setValue( IECore.V3f( 0, 0, -5 ) )
		
		s["displays"] = GafferScene.Displays()
		s["displays"].addDisplay(
			"beauty",
			IECore.Display(
				"/tmp/test.tif",
				"tiff",
				"rgba",
				{}
			)
		)
		s["displays"]["in"].setInput( s["plane"]["out"] )
		
		s["render"] = GafferRenderMan.RenderManRender()
		s["render"]["in"].setInput( s["displays"]["out"] )
		s["render"]["mode"].setValue( "generate" )
		
		s["render"]["ribFileName"].setValue( "/tmp/test.rib" )

		s["fileName"].setValue( "/tmp/test.gfr" )
		s.save()
		
		s["render"].execute()
		
		self.assertTrue( os.path.exists( "/tmp/test.rib" ) )
		
		p = subprocess.Popen(
			"renderdl " + "/tmp/test.rib",
			shell = True,
			stderr = subprocess.PIPE
		)
		p.wait()
		
		self.failIf( "exceeded its bounds" in "".join( p.stderr.readlines() ) )
		
		self.assertTrue( os.path.exists( "/tmp/test.tif" ) )
						
	def setUp( self ) :
	
		for f in (
			"/tmp/test.tif",
			"/tmp/test.rib"
		) :
			if os.path.exists( f ) :
				os.remove( f )
				
if __name__ == "__main__":
	unittest.main()
