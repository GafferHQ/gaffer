##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import IECore

import GafferTest
import GafferScene
import GafferSceneTest
import GafferOSL
import GafferArnold

class ArnoldDisplacementTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "noise" )

		d = GafferArnold.ArnoldDisplacement()
		d["map"].setInput( n["out"] )
		d["height"].setValue( 2.5 )
		d["padding"].setValue( 25 )
		d["zeroValue"].setValue( .25 )
		d["autoBump"].setValue( True )

		na = n.attributes()
		da = d.attributes()

		self.assertEqual(
			da,
			IECore.CompoundObject( {
				"ai:disp_map" : na["ai:surface"],
				"ai:disp_height" : IECore.FloatData( 2.5 ),
				"ai:disp_padding" : IECore.FloatData( 25 ),
				"ai:disp_zero_value" : IECore.FloatData( .25 ),
				"ai:disp_autobump" : IECore.BoolData( True ),
			} )
		)

		d["enabled"].setValue( False )
		self.assertEqual( d.attributes(), IECore.CompoundObject() )

	def testDirtyPropagation( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "noise" )

		d = GafferArnold.ArnoldDisplacement()
		cs = GafferTest.CapturingSlot( d.plugDirtiedSignal() )

		d["height"].setValue( 10 )
		self.assertTrue( d["out"] in [ x[0] for x in cs ] )

		del cs[:]
		d["map"].setInput( n["out"] )
		self.assertTrue( d["out"] in [ x[0] for x in cs ] )

	def testOSLShaderInput( self ) :

		n = GafferOSL.OSLShader()
		n.loadShader( "Pattern/Noise" )

		d = GafferArnold.ArnoldDisplacement()

		d["map"].setInput( n["out"] )
		self.assertTrue( d["map"].getInput().isSame( n["out"] ) )

		na = n.attributes()
		da = d.attributes()

		self.assertEqual(
			da,
			IECore.CompoundObject( {
				"ai:disp_map" : na["osl:shader"],
				"ai:disp_height" : IECore.FloatData( 1 ),
				"ai:disp_padding" : IECore.FloatData( 0 ),
				"ai:disp_zero_value" : IECore.FloatData( 0 ),
			} )
		)

	def testNoInput( self ) :

		d = GafferArnold.ArnoldDisplacement()
		self.assertTrue( "ai:disp_map" not in d.attributes() )

	def testAssignment( self ) :

		s = GafferScene.Sphere()

		n = GafferArnold.ArnoldShader()
		n.loadShader( "noise" )

		d = GafferArnold.ArnoldDisplacement()
		d["map"].setInput( n["out"] )
		d["height"].setValue( 2.5 )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		a = GafferScene.ShaderAssignment()
		a["in"].setInput( s["out"] )
		a["shader"].setInput( d["out"] )
		a["filter"].setInput( f["out"] )

		self.assertEqual(
			a["out"].attributes( "/sphere" )["ai:disp_height"],
			IECore.FloatData( 2.5 )
		)

		d["height"].setValue( 5 )

		self.assertEqual(
			a["out"].attributes( "/sphere" )["ai:disp_height"],
			IECore.FloatData( 5 )
		)

if __name__ == "__main__":
	unittest.main()
