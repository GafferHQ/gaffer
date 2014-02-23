##########################################################################
#  
#  Copyright (c) 2013-2014, John Haddon. All rights reserved.
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
		
		inPoint = GafferOSL.OSLShader()
		inPoint.loadShader( "ObjectProcessing/InPoint" )
		
		splitPoint = GafferOSL.OSLShader()
		splitPoint.loadShader( "Utility/SplitPoint" )
		splitPoint["parameters"]["p"].setInput( inPoint["out"]["value"] )
		
		buildPoint = GafferOSL.OSLShader()
		buildPoint.loadShader( "Utility/BuildPoint" )
		buildPoint["parameters"]["x"].setInput( splitPoint["out"]["y"] )
		buildPoint["parameters"]["y"].setInput( splitPoint["out"]["x"] )
		
		outPoint = GafferOSL.OSLShader()
		outPoint.loadShader( "ObjectProcessing/OutPoint" )
		outPoint["parameters"]["value"].setInput( buildPoint["out"]["p"] )
		
		primVarShader = GafferOSL.OSLShader()
		primVarShader.loadShader( "ObjectProcessing/OutObject" )
		primVarShader["parameters"]["in0"].setInput( outPoint["out"]["primitiveVariable"] )
		
		o["shader"].setInput( primVarShader["out"] )
		
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
	
	def testOnlyAcceptsSurfaceShaders( self ) :
	
		object = GafferOSL.OSLObject()
		shader = GafferOSL.OSLShader()
	
		shader.loadShader( "ObjectProcessing/OutPoint" )
		self.assertFalse( object["shader"].acceptsInput( shader["out"] ) )

		shader.loadShader( "ObjectProcessing/OutObject" )
		self.assertTrue( object["shader"].acceptsInput( shader["out"] ) )

	def testAcceptsNone( self ) :
	
		object = GafferOSL.OSLObject()
		self.assertTrue( object["shader"].acceptsInput( None ) )
	
	def testAcceptsShaderSwitch( self ) :
	
		object = GafferOSL.OSLObject()
		switch = GafferScene.ShaderSwitch()
		
		self.assertTrue( object["shader"].acceptsInput( switch["out"] ) )	

	def testPrimitiveVariableWithZeroValue( self ) :
	
		outPoint = GafferOSL.OSLShader()
		outPoint.loadShader( "ObjectProcessing/OutPoint" )
		outPoint["parameters"]["name"].setValue( "velocity" )
		outPoint["parameters"]["value"].setValue( IECore.V3f( 0 ) )
		
		primVarShader = GafferOSL.OSLShader()
		primVarShader.loadShader( "ObjectProcessing/OutObject" )
		primVarShader["parameters"]["in0"].setInput( outPoint["out"]["primitiveVariable"] )
		
		p = GafferScene.Plane()
		p["dimensions"].setValue( IECore.V2f( 1, 2 ) )
		p["divisions"].setValue( IECore.V2i( 10 ) )
		
		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )
		
		o = GafferOSL.OSLObject()
		o["in"].setInput( p["out"] )
		o["shader"].setInput( primVarShader["out"] )
		o["filter"].setInput( filter["match"] )
		
		for v in o["out"].object( "/plane" )["velocity"].data :
			self.assertEqual( v, IECore.V3f( 0 ) )
		
if __name__ == "__main__":
	unittest.main()
