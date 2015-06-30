##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
import GafferScene
import GafferSceneTest

class SceneLoopTest( GafferSceneTest.SceneTestCase ) :

	def testDefaultName( self ) :

		s = GafferScene.SceneLoop()
		self.assertEqual( s.getName(), "SceneLoop" )

	def testLoop( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		script["loop"] = GafferScene.SceneLoop()
		script["loop"]["in"].setInput( script["sphere"]["out"] )

		script["filter"] = GafferScene.PathFilter()
		script["filter"]["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		script["transform"] = GafferScene.Transform()
		script["transform"]["transform"]["translate"]["x"].setValue( 1 )
		script["transform"]["in"].setInput( script["loop"]["previous"] )
		script["transform"]["filter"].setInput( script["filter"]["out"] )
		script["loop"]["next"].setInput( script["transform"]["out"] )

		script["loop"]["iterations"].setValue( 2 )
		self.assertEqual( script["loop"]["out"].transform( "/sphere" ), IECore.M44f.createTranslated( IECore.V3f( 2, 0, 0 ) ) )

		script["loop"]["iterations"].setValue( 4 )
		self.assertEqual( script["loop"]["out"].transform( "/sphere" ), IECore.M44f.createTranslated( IECore.V3f( 4, 0, 0 ) ) )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		script2["loop"]["iterations"].setValue( 3 )
		self.assertEqual( script2["loop"]["out"].transform( "/sphere" ), IECore.M44f.createTranslated( IECore.V3f( 3, 0, 0 ) ) )

		script2["loop"]["iterations"].setValue( 5 )
		self.assertEqual( script2["loop"]["out"].transform( "/sphere" ), IECore.M44f.createTranslated( IECore.V3f( 5, 0, 0 ) ) )

	def testEnabled( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		script["loop"] = GafferScene.SceneLoop()
		script["loop"]["in"].setInput( script["sphere"]["out"] )

		script["filter"] = GafferScene.PathFilter()
		script["filter"]["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		script["transform"] = GafferScene.Transform()
		script["transform"]["transform"]["translate"]["x"].setValue( 1 )
		script["transform"]["in"].setInput( script["loop"]["previous"] )
		script["transform"]["filter"].setInput( script["filter"]["out"] )
		script["loop"]["next"].setInput( script["transform"]["out"] )

		script["loop"]["iterations"].setValue( 2 )
		self.assertEqual( script["loop"]["out"].transform( "/sphere" ), IECore.M44f.createTranslated( IECore.V3f( 2, 0, 0 ) ) )

		script["loop"]["enabled"].setValue( False )
		self.assertEqual( script["loop"]["out"].transform( "/sphere" ), IECore.M44f() )

		self.assertScenesEqual( script["loop"]["out"], script["sphere"]["out"] )
		self.assertSceneHashesEqual( script["loop"]["out"], script["sphere"]["out"] )

		self.assertTrue( script["loop"].correspondingInput( script["loop"]["out"] ).isSame( script["loop"]["in"] ) )

if __name__ == "__main__":
	unittest.main()
