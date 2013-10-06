##########################################################################
#  
#  Copyright (c) 2013, John Haddon. All rights reserved.
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
import GafferScene
import GafferOSL
import GafferOSLTest

class OSLObjectTest( GafferOSLTest.OSLTestCase ) :

	def test( self ) :
	
		p = GafferScene.Plane()
		p["dimensions"].setValue( IECore.V2f( 1, 2 ) )
		p["divisions"].setValue( IECore.V2i( 10 ) )
		
		self.assertSceneValid( p["out"] )
		
		o = GafferOSL.OSLObject()
		o["in"].setInput( p["out"] )
		
		self.assertScenesEqual( p["out"], o["out"] )
		
		# shading network to swap x and y
		
		globals = GafferOSL.OSLShader()
		globals.loadShader( "utility/globals" )
		
		splitPoint = GafferOSL.OSLShader()
		splitPoint.loadShader( "utility/splitPoint" )
		splitPoint["parameters"]["p"].setInput( globals["out"]["globalP"] )
		
		buildColor = GafferOSL.OSLShader()
		buildColor.loadShader( "utility/buildColor" )
		buildColor["parameters"]["r"].setInput( splitPoint["out"]["y"] )
		buildColor["parameters"]["g"].setInput( splitPoint["out"]["x"] )
		
		constant = GafferOSL.OSLShader()
		constant.loadShader( "surface/constant" )
		constant["parameters"]["Cs"].setInput( buildColor["out"]["c"] )
		
		o["shader"].setInput( constant["out"] )
		
		self.assertScenesEqual( p["out"], o["out"] )
		
		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )
		
		o["filter"].setInput( filter["match"] )
		
		self.assertSceneValid( o["out"] )
		
		boundIn = p["out"].bound( "/plane" )
		boundOut = o["out"].bound( "/plane" )
		
		self.assertEqual( boundIn.min.x, boundOut.min.y )
		self.assertEqual( boundIn.max.x, boundOut.max.y )
		self.assertEqual( boundIn.min.y, boundOut.min.x )
		self.assertEqual( boundIn.max.y, boundOut.max.x )
		
if __name__ == "__main__":
	unittest.main()
