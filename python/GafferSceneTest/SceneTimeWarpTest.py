##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import inspect
import imath

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class SceneTimeWarpTest( GafferSceneTest.SceneTestCase ) :

	def testConstruct( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.TimeWarp()
		s["n"].setup( GafferScene.ScenePlug() )

		self.assertEqual( s["n"]["speed"].getValue(), 1 )
		self.assertEqual( s["n"]["offset"].getValue(), 0 )

	def testAffects( self ) :

		n = Gaffer.TimeWarp()
		n.setup( GafferScene.ScenePlug() )

		c = GafferTest.CapturingSlot( n.plugDirtiedSignal() )
		n["speed"].setValue( 2 )

		found = False
		for cc in c :
			if cc[0].isSame( n["out"] ) :
				found = True
		self.assertTrue( found )

		del c[:]
		n["offset"].setValue( 2 )
		found = False
		for cc in c :
			if cc[0].isSame( n["out"] ) :
				found = True
		self.assertTrue( found )

	def testNoExtraInputs( self ) :

		p = GafferScene.Plane()
		n = Gaffer.TimeWarp()
		n.setup( GafferScene.ScenePlug() )
		n["in"].setInput( p["out"] )

		self.assertTrue( "in1" not in n )

	def testTimeContext( self ) :

		s = Gaffer.ScriptNode()

		s["cube"] = GafferScene.Cube()

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'parent["cube"]["dimensions"] = imath.V3f( context["frame"] )' )

		s["n"] = Gaffer.TimeWarp()
		s["n"].setup( GafferScene.ScenePlug() )
		s["n"]["in"].setInput( s["cube"]["out"] )
		s["n"]["speed"].setValue( 0 )
		s["n"]["offset"].setValue( 3 )
		self.assertEqual( s["n"]["out"].bound( "/cube" ), imath.Box3f( imath.V3f( -1.5 ), imath.V3f( 1.5 ) ) )

		s["e2"] = Gaffer.Expression()
		s["e2"].setExpression( inspect.cleandoc(
			"""
			assert( context.get( "scene:path", None ) is None )
			parent["n"]["offset"] = 5
			"""
		) )

		self.assertEqual( s["n"]["out"].bound( "/cube" ), imath.Box3f( imath.V3f( -2.5 ), imath.V3f( 2.5 ) ) )

if __name__ == "__main__":
	unittest.main()
