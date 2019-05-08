##########################################################################
#
#  Copyright (c) 2014, Esteban Tovagliari. All rights reserved.
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
import subprocess32 as subprocess

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferAppleseed
import GafferAppleseedTest

class AppleseedRenderTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__scriptFileName = self.temporaryDirectory() + "/test.gfr"

	def testExecute( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["render"] = GafferAppleseed.AppleseedRender()
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )
		s["render"]["in"].setInput( s["plane"]["out"] )

		s["expression"] = Gaffer.Expression()
		s["expression"].setExpression( "parent['render']['fileName'] = '" + self.temporaryDirectory() + "/test.%d.appleseed' % int( context['frame'] )" )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		subprocess.check_call(
			[ "gaffer", "execute", self.__scriptFileName, "-frames", "1-3" ]
		)

		for i in range( 1, 4 ) :
			self.failUnless( os.path.exists( self.temporaryDirectory() + "/test.%d.appleseed" % i ) )

	def testWaitForImage( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["options"] = GafferAppleseed.AppleseedOptions()
		s["options"]["in"].setInput( s["plane"]["out"] )
		s["options"]["options"]["aaSamples"]["value"].setValue( 1 )
		s["options"]["options"]["aaSamples"]["enabled"].setValue( True )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				self.temporaryDirectory() + "/test.exr",
				"exr",
				"rgba",
				{}
			)
		)
		s["outputs"]["in"].setInput( s["options"]["out"] )

		s["render"] = GafferAppleseed.AppleseedRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )

		s["render"]["fileName"].setValue( self.temporaryDirectory() + "/test.appleseed" )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		s["render"]["task"].execute()

		self.failUnless( os.path.exists( self.temporaryDirectory() + "/test.exr" ) )

	def testExecuteWithStringSubstitutions( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["render"] = GafferAppleseed.AppleseedRender()
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )
		s["render"]["in"].setInput( s["plane"]["out"] )
		s["render"]["fileName"].setValue( self.temporaryDirectory() + "/test.####.appleseed" )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		subprocess.check_call(
			[ "gaffer", "execute", self.__scriptFileName, "-frames", "1-3" ]
		)

		for i in range( 1, 4 ) :
			self.failUnless( os.path.exists( self.temporaryDirectory() + "/test.%04d.appleseed" % i ) )

	def testImageOutput( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["options"] = GafferAppleseed.AppleseedOptions()
		s["options"]["in"].setInput( s["plane"]["out"] )
		s["options"]["options"]["aaSamples"]["value"].setValue( 1 )
		s["options"]["options"]["aaSamples"]["enabled"].setValue( True )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				self.temporaryDirectory() + "/test.####.exr",
				"exr",
				"rgba",
				{}
			)
		)
		s["outputs"]["in"].setInput( s["options"]["out"] )

		s["render"] = GafferAppleseed.AppleseedRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )

		s["render"]["fileName"].setValue( self.temporaryDirectory() + "/test.####.appleseed" )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		c = Gaffer.Context()
		for i in range( 1, 4 ) :
			c.setFrame( i )
			with c :
				s["render"]["task"].execute()

		for i in range( 1, 4 ) :
			self.failUnless( os.path.exists( self.temporaryDirectory() + "/test.%04d.exr" % i ) )

	def testTypeNamePrefixes( self ) :

		self.assertTypeNamesArePrefixed( GafferAppleseed )
		self.assertTypeNamesArePrefixed( GafferAppleseedTest )

	def testDefaultNames( self ) :

		self.assertDefaultNamesAreCorrect( GafferAppleseed )
		self.assertDefaultNamesAreCorrect( GafferAppleseedTest )

	def testNodesConstructWithDefaultValues( self ) :

		self.assertNodesConstructWithDefaultValues( GafferAppleseed )
		self.assertNodesConstructWithDefaultValues( GafferAppleseedTest )

	def testDirectoryCreation( self ) :

		s = Gaffer.ScriptNode()
		s["variables"].addChild( Gaffer.NameValuePlug( "renderDirectory", self.temporaryDirectory() + "/renderTests",  Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["variables"].addChild( Gaffer.NameValuePlug( "appleseedDirectory", self.temporaryDirectory() + "/appleseedTests", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		s["plane"] = GafferScene.Plane()

		s["outputs"] = GafferScene.Outputs()
		s["outputs"]["in"].setInput( s["plane"]["out"] )
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				"$renderDirectory/test.####.exr",
				"exr",
				"rgba",
				{}
			)
		)

		s["render"] = GafferAppleseed.AppleseedRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )
		s["render"]["fileName"].setValue( "$appleseedDirectory/test.####.appleseed" )
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )

		self.assertFalse( os.path.exists( self.temporaryDirectory() + "/renderTests" ) )
		self.assertFalse( os.path.exists( self.temporaryDirectory() + "/appleseedTests" ) )
		self.assertFalse( os.path.exists( self.temporaryDirectory() + "/appleseedTests/test.0001.appleseed" ) )
		self.assertFalse( os.path.exists( self.__scriptFileName ) )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		with s.context() :
			s["render"]["task"].execute()

		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/renderTests" ) )
		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/appleseedTests" ) )
		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/appleseedTests/test.0001.appleseed" ) )
		self.assertTrue( os.path.exists( self.__scriptFileName ) )

		# check it can cope with everything already existing

		with s.context() :
			s["render"]["task"].execute()

		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/renderTests" ) )
		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/appleseedTests" ) )
		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/appleseedTests/test.0001.appleseed" ) )

	def testInternalConnectionsNotSerialised( self ) :

		s = Gaffer.ScriptNode()
		s["render"] = GafferAppleseed.AppleseedRender()
		self.assertFalse( "__adaptedIn" in s.serialise() )

	def testNoInput( self ) :

		render = GafferAppleseed.AppleseedRender()
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( os.path.join( self.temporaryDirectory(), "test.appleseed" ) )

		self.assertEqual( render["task"].hash(), IECore.MurmurHash() )
		render["task"].execute()
		self.assertFalse( os.path.exists( render["fileName"].getValue() ) )

	def testInputFromContextVariables( self ) :

		plane = GafferScene.Plane()

		variables = Gaffer.ContextVariables()
		variables.setup( GafferScene.ScenePlug() )
		variables["in"].setInput( plane["out"] )

		render = GafferAppleseed.AppleseedRender()
		render["in"].setInput( variables["out"] )
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( os.path.join( self.temporaryDirectory(), "test.appleseed" ) )

		self.assertNotEqual( render["task"].hash(), IECore.MurmurHash() )
		render["task"].execute()
		self.assertTrue( os.path.exists( render["fileName"].getValue() ) )

if __name__ == "__main__":
	unittest.main()
