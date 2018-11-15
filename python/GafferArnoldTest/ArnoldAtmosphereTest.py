##########################################################################
#
#  Copyright (c) 2018, John Haddon. All rights reserved.
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

import IECoreScene

import GafferTest
import GafferSceneTest
import GafferArnold

class ArnoldAtmosphereTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		a = GafferArnold.ArnoldAtmosphere()
		self.assertNotIn( "option:ai:atmosphere", a["out"]["globals"].getValue() )

		s = GafferArnold.ArnoldShader()
		s.loadShader( "atmosphere_volume" )

		cs = GafferTest.CapturingSlot( a.plugDirtiedSignal() )
		a["shader"].setInput( s["out"] )
		self.assertIn( a["out"]["globals"], { x[0] for x in cs } )

		atmosphereOption = a["out"]["globals"].getValue()["option:ai:atmosphere"]
		self.assertIsInstance( atmosphereOption, IECoreScene.ShaderNetwork )
		self.assertEqual( atmosphereOption.outputShader().name, "atmosphere_volume" )
		self.assertEqual( atmosphereOption.outputShader().parameters["density"].value, 0.0 )

		del cs[:]
		s["parameters"]["density"].setValue( 0.25 )
		self.assertIn( a["out"]["globals"], { x[0] for x in cs } )

		atmosphereOption = a["out"]["globals"].getValue()["option:ai:atmosphere"]
		self.assertIsInstance( atmosphereOption, IECoreScene.ShaderNetwork )
		self.assertEqual( atmosphereOption.outputShader().name, "atmosphere_volume" )
		self.assertEqual( atmosphereOption.outputShader().parameters["density"].value, 0.25 )

if __name__ == "__main__":
	unittest.main()
