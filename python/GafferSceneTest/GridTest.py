##########################################################################
#
#  Copyright (c) 2014, John Haddon. All rights reserved.
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

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class GridTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		g = GafferScene.Grid()
		self.assertSceneValid( g["out"] )

		g["dimensions"].setValue( IECore.V2f( 100, 5 ) )
		self.assertSceneValid( g["out"] )

	def testChildNames( self ) :

		g = GafferScene.Grid()
		self.assertEqual( g["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "grid" ] ) )
		self.assertEqual( g["out"].childNames( "/grid" ), IECore.InternedStringVectorData( [ "gridLines", "centerLines", "borderLines" ] ) )

		cs = GafferTest.CapturingSlot( g.plugDirtiedSignal() )
		g["name"].setValue( "g" )
		self.assertTrue( g["out"]["childNames"] in [ x[0] for x in cs ] )

		self.assertTrue( g["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "g" ] ) )

	def testAttributes( self ) :

		g = GafferScene.Grid()

		a = g["out"].attributes( "/grid" )
		self.assertEqual( a["shader"], IECore.Shader( "Constant", "gl:surface", { "Cs" : IECore.Color3f( 1 ) } ) )

		g["centerPixelWidth"].setValue( 2 )
		a2 = g["out"].attributes( "/grid/centerLines" )
		self.assertEqual( a2, IECore.CompoundObject( { "gl:curvesPrimitive:glLineWidth" : IECore.FloatData( 2 ) } ) )

if __name__ == "__main__":
	unittest.main()
