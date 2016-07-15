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

import IECore

import Gaffer
import GafferScene
import GafferRenderMan
import GafferRenderManTest

class RenderManLightTest( GafferRenderManTest.RenderManTestCase ) :

	def test( self ) :

		n = GafferRenderMan.RenderManLight()
		n.loadShader( "pointlight" )

		lightObject = n["out"].object( "/light" )
		self.assertTrue( isinstance( lightObject, IECore.NullObject ) )

		light = n["out"].attributes( "/light" )["ri:light"][-1]
		self.assertTrue( isinstance( light, IECore.Shader ) )
		self.assertEqual( light.parameters["intensity"].value, 1 )

		n["parameters"]["intensity"].setValue( 10 )
		light = n["out"].attributes( "/light" )["ri:light"][-1]
		self.assertEqual( light.parameters["intensity"].value, 10 )

	@unittest.skipIf( "TRAVIS" in os.environ, "No license available on Travis" )
	def testRender( self ) :

		s = Gaffer.ScriptNode()

		s["l"] = GafferRenderMan.RenderManLight()
		s["l"].loadShader( "pointlight" )
		s["l"]["parameters"]["lightcolor"].setValue( IECore.Color3f( 1, 0.5, 0.25 ) )
		s["l"]["transform"]["translate"]["z"].setValue( 1 )

		s["p"] = GafferScene.Plane()

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 1 )

		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["l"]["out"] )
		s["g"]["in"][1].setInput( s["p"]["out"] )
		s["g"]["in"][2].setInput( s["c"]["out"] )

		s["s"] = GafferRenderMan.RenderManShader()
		s["s"].loadShader( "matte" )
		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["in"].setInput( s["g"]["out"] )
		s["a"]["shader"].setInput( s["s"]["out"] )

		s["d"] = GafferScene.Outputs()
		s["d"].addOutput( "beauty", IECore.Display( self.temporaryDirectory() + "/testRenderManLight.exr", "exr", "rgba", { "quantize" : IECore.FloatVectorData( [ 0, 0, 0, 0 ] ) } ) )
		s["d"]["in"].setInput( s["a"]["out"] )

		s["o"] = GafferScene.StandardOptions()
		s["o"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )
		s["o"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["o"]["in"].setInput( s["d"]["out"] )

		s["r"] = GafferRenderMan.RenderManRender()
		s["r"]["ribFileName"].setValue( self.temporaryDirectory() + "/testRenderManLight.rib" )
		s["r"]["in"].setInput( s["o"]["out"] )

		# must save the script for the procedural to load it
		# in the render process. if we were using a dispatcher,
		# that would have saved the script for us, but we're
		# calling execute() directly so it is our responsibility.
		s["fileName"].setValue( self.temporaryDirectory() + "/testRenderManLight.gfr" )
		s.save()

		s["r"].execute()

		i = IECore.EXRImageReader( self.temporaryDirectory() + "/testRenderManLight.exr" ).read()
		e = IECore.ImagePrimitiveEvaluator( i )
		r = e.createResult()
		e.pointAtUV( IECore.V2f( 0.5 ), r )

		self.assertEqual( r.floatPrimVar( e.R() ), 1 )
		self.assertEqual( r.floatPrimVar( e.G() ), 0.5 )
		self.assertEqual( r.floatPrimVar( e.B() ), 0.25 )

if __name__ == "__main__":
	unittest.main()
