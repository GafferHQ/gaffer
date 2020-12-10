##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferScene
import GafferSceneTest

import IECore

class FilterPlugTest( GafferSceneTest.SceneTestCase ) :

	def testAcceptsInput( self ) :

		filterPlug1 = GafferScene.FilterPlug()
		filterPlug2 = GafferScene.FilterPlug()

		# We want to accept inputs from FilterPlugs.
		self.assertTrue( filterPlug1.acceptsInput( filterPlug2 ) )

		# But not from IntPlugs.
		plug = Gaffer.IntPlug()
		self.assertFalse( filterPlug1.acceptsInput( plug ) )

		# Even if they are on a box.
		box = Gaffer.Box()
		box["p"] = Gaffer.IntPlug()
		self.assertFalse( filterPlug1.acceptsInput( box["p"] ) )

		# Or a dot.
		dot = Gaffer.Dot()
		dot.setup( Gaffer.IntPlug() )
		self.assertFalse( filterPlug1.acceptsInput( dot["out"] ) )

	def testMatch( self ) :

		p = GafferScene.FilterPlug()

		with self.assertRaises( Exception ) :
			p.match( None )

		c = GafferScene.Cube()
		c["sets"].setValue( "cubeSet" )

		ctx = Gaffer.Context()
		ctx[ "scene:path" ] = IECore.InternedStringVectorData( [ "cube" ] )
		with ctx :

			f = GafferScene.SetFilter()
			p.setInput( f["out"] )

			f["setExpression"].setValue( "cubeSet" )
			self.assertEqual( p.match( c["out"] ), IECore.PathMatcher.Result.ExactMatch )
			f["setExpression"].setValue( "otherSet" )
			self.assertEqual( p.match( c["out"] ), IECore.PathMatcher.Result.NoMatch )

			f = GafferScene.PathFilter()
			p.setInput( f["out"] )

			f["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )
			self.assertEqual( p.match( c["out"] ), IECore.PathMatcher.Result.ExactMatch )
			f["paths"].setValue( IECore.StringVectorData( [ "/other" ] ) )
			self.assertEqual( p.match( c["out"] ), IECore.PathMatcher.Result.NoMatch )

if __name__ == "__main__":
	unittest.main()
