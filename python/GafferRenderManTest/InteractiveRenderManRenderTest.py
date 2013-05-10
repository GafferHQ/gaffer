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

import unittest
import time

import IECore

import Gaffer
import GafferScene
import GafferRenderMan

class InteractiveRenderManRenderTest( unittest.TestCase ) :
	
	def __colorAtUV( self, image, uv ) :
	
		e = IECore.ImagePrimitiveEvaluator( image )
		r = e.createResult()
		e.pointAtUV( uv, r )
		
		return IECore.Color3f(
			r.floatPrimVar( image["R"] ),
			r.floatPrimVar( image["G"] ),
			r.floatPrimVar( image["B"] ),
		)
		
	def testLights( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["l"] = GafferRenderMan.RenderManLight()
		s["l"].loadShader( "pointlight" )
		s["l"]["parameters"]["lightcolor"].setValue( IECore.Color3f( 1, 0.5, 0.25 ) )
		s["l"]["transform"]["translate"]["z"].setValue( 1 )
		
		s["p"] = GafferScene.Plane()
		
		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 1 )
		
		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["l"]["out"] )
		s["g"]["in1"].setInput( s["p"]["out"] )
		s["g"]["in2"].setInput( s["c"]["out"] )
		
		s["s"] = GafferRenderMan.RenderManShader()
		s["s"].loadShader( "matte" )
		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["in"].setInput( s["g"]["out"] )
		s["a"]["shader"].setInput( s["s"]["out"] )
		
		s["d"] = GafferScene.Displays()
		s["d"].addDisplay(
			"beauty",
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"quantize" : IECore.FloatVectorData( [ 0, 0, 0, 0 ] ),
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelyPlane",
				}
			)
		)
		s["d"]["in"].setInput( s["a"]["out"] )
		
		s["o"] = GafferScene.StandardOptions()
		s["o"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )
		s["o"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["o"]["in"].setInput( s["d"]["out"] )
		
		s["r"] = GafferRenderMan.InteractiveRenderManRender()
		s["r"]["in"].setInput( s["o"]["out"] )
		
		# start a render, give it time to finish, and check the output
		
		s["r"]["state"].setValue( s["r"].State.Running )
		
		time.sleep( 1 )
				
		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[0], IECore.Color3f( 1, 0.5, 0.25 ) )
		
		# adjust a parameter, give it time to update, and check the output
		
		s["l"]["parameters"]["lightcolor"].setValue( IECore.Color3f( 0.25, 0.5, 1 ) )
		
		time.sleep( 1 )
		
		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[2], IECore.Color3f( 0.25, 0.5, 1 ) )
		
		# pause it, adjust a parameter, wait, and check that nothing changed
		
		s["r"]["state"].setValue( s["r"].State.Paused )
		s["l"]["parameters"]["lightcolor"].setValue( IECore.Color3f( 1, 0.5, 0.25 ) )
		
		time.sleep( 1 )
		
		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[2], IECore.Color3f( 0.25, 0.5, 1 ) )
		
		# unpause it, wait, and check that the update happened
		
		s["r"]["state"].setValue( s["r"].State.Running )
		time.sleep( 1 )
		
		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[0], IECore.Color3f( 1, 0.5, 0.25 ) )
		
		# turn off light updates, adjust a parameter, wait, and check nothing happened
		
		s["r"]["updateLights"].setValue( False )
		s["l"]["parameters"]["lightcolor"].setValue( IECore.Color3f( 0.25, 0.5, 1 ) )

		time.sleep( 1 )
		
		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[0], IECore.Color3f( 1, 0.5, 0.25 ) )
		
		# turn light updates back on and check that it updates
		
		s["r"]["updateLights"].setValue( True )
		
		time.sleep( 1 )
		
		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[2], IECore.Color3f( 0.25, 0.5, 1 ) )
		
		# stop the render, tweak a parameter and check that nothing happened
		
		s["r"]["state"].setValue( s["r"].State.Stopped )
		s["l"]["parameters"]["lightcolor"].setValue( IECore.Color3f( 1, 0.5, 0.25 ) )
		time.sleep( 1 )
		
		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[2], IECore.Color3f( 0.25, 0.5, 1 ) )
	
	def testShaders( self ) :

		s = Gaffer.ScriptNode()
		
		s["p"] = GafferScene.Plane()
		s["p"]["transform"]["translate"].setValue( IECore.V3f( -0.1, -0.1, 0 ) )
		
		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 1 )
		
		s["l"] = GafferRenderMan.RenderManLight()
		s["l"].loadShader( "ambientlight" )
		
		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["p"]["out"] )
		s["g"]["in1"].setInput( s["c"]["out"] )
		s["g"]["in2"].setInput( s["l"]["out"] )
		
		s["s"] = GafferRenderMan.RenderManShader()
		s["s"].loadShader( "checker" )
		s["s"]["parameters"]["blackcolor"].setValue( IECore.Color3f( 1, 0.5, 0.25 ) )
		s["s"]["parameters"]["Ka"].setValue( 1 )
		s["s"]["parameters"]["frequency"].setValue( 1 )
		
		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["in"].setInput( s["g"]["out"] )
		s["a"]["shader"].setInput( s["s"]["out"] )
		
		s["d"] = GafferScene.Displays()
		s["d"].addDisplay(
			"beauty",
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"quantize" : IECore.FloatVectorData( [ 0, 0, 0, 0 ] ),
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelyPlane",
				}
			)
		)
		s["d"]["in"].setInput( s["a"]["out"] )
		
		s["o"] = GafferScene.StandardOptions()
		s["o"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )
		s["o"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["o"]["in"].setInput( s["d"]["out"] )
		
		s["r"] = GafferRenderMan.InteractiveRenderManRender()
		s["r"]["in"].setInput( s["o"]["out"] )
		
		# start a render, give it time to finish, and check the output
		
		s["r"]["state"].setValue( s["r"].State.Running )
		
		time.sleep( 1 )
				
		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c, IECore.Color3f( 1, 0.5, 0.25 ) )
		
		# adjust a shader parameter, wait, and check that it changed
		
		s["s"]["parameters"]["blackcolor"].setValue( IECore.Color3f( 1, 1, 1 ) )
		time.sleep( 1 )
		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c, IECore.Color3f( 1 ) )
		
		# turn off shader updates, do the same, and check that it hasn't changed
		
		s["r"]["updateShaders"].setValue( False )
		s["s"]["parameters"]["blackcolor"].setValue( IECore.Color3f( 0.5 ) )
		time.sleep( 1 )
		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c, IECore.Color3f( 1 ) )
		
		# turn shader updates back on, and check that it updates
		
		s["r"]["updateShaders"].setValue( True )
		time.sleep( 1 )
		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c, IECore.Color3f( 0.5 ) )
				
if __name__ == "__main__":
	unittest.main()
