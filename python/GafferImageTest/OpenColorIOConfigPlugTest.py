##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

import Gaffer
import GafferDispatch
import GafferDispatchTest
import GafferImage
import GafferImageTest

class OpenColorIOConfigPlugTest( GafferImageTest.ImageTestCase ) :

	def testDefaultConfigPlug( self ) :

		script = Gaffer.ScriptNode()

		self.assertEqual( GafferImage.OpenColorIOAlgo.getConfig( script.context() ), "" )
		self.assertEqual( GafferImage.OpenColorIOAlgo.variables( script.context() ), [] )

		self.assertIsNone( GafferImage.OpenColorIOConfigPlug.acquireDefaultConfigPlug( script, createIfNecessary = False ) )

		plug = GafferImage.OpenColorIOConfigPlug.acquireDefaultConfigPlug( script )
		self.assertIsInstance( plug, GafferImage.OpenColorIOConfigPlug )
		self.assertTrue( plug.isSame( GafferImage.OpenColorIOConfigPlug.acquireDefaultConfigPlug( script ) ) )
		self.assertEqual( plug.getName(), "openColorIO" )

		self.assertEqual( GafferImage.OpenColorIOAlgo.getConfig( script.context() ), "" )
		self.assertEqual( GafferImage.OpenColorIOAlgo.variables( script.context() ), [] )

		plug["config"].setValue( "test.ocio" )
		self.assertEqual( GafferImage.OpenColorIOAlgo.getConfig( script.context() ), "test.ocio" )

		plug["variables"].addChild( Gaffer.NameValuePlug( "testA", "testValueA", defaultEnabled = True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		plug["variables"].addChild( Gaffer.NameValuePlug( "testB", "testValueB", defaultEnabled = True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		self.assertEqual( set( GafferImage.OpenColorIOAlgo.variables( script.context() ) ), { "testA", "testB" } )
		self.assertEqual( GafferImage.OpenColorIOAlgo.getVariable( script.context(), "testA" ), "testValueA" )
		self.assertEqual( GafferImage.OpenColorIOAlgo.getVariable( script.context(), "testB" ), "testValueB" )

		plug["variables"][0]["enabled"].setValue( False )
		self.assertEqual( GafferImage.OpenColorIOAlgo.variables( script.context() ), [ "testB" ] )
		self.assertEqual( GafferImage.OpenColorIOAlgo.getVariable( script.context(), "testB" ), "testValueB" )

		plug["variables"][1]["value"].setValue( "testValueB2" )
		self.assertEqual( GafferImage.OpenColorIOAlgo.variables( script.context() ), [ "testB" ] )
		self.assertEqual( GafferImage.OpenColorIOAlgo.getVariable( script.context(), "testB" ), "testValueB2" )

		plug["variables"][1]["name"].setValue( "testB2" )
		self.assertEqual( GafferImage.OpenColorIOAlgo.variables( script.context() ), [ "testB2" ] )
		self.assertEqual( GafferImage.OpenColorIOAlgo.getVariable( script.context(), "testB2" ), "testValueB2" )

		plug["variables"][0]["enabled"].setValue( True )
		self.assertEqual( set( GafferImage.OpenColorIOAlgo.variables( script.context() ) ), { "testA", "testB2" } )
		self.assertEqual( GafferImage.OpenColorIOAlgo.getVariable( script.context(), "testA" ), "testValueA" )
		self.assertEqual( GafferImage.OpenColorIOAlgo.getVariable( script.context(), "testB2" ), "testValueB2" )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		self.assertEqual( GafferImage.OpenColorIOAlgo.getConfig( script2.context() ), "test.ocio" )
		self.assertEqual( set( GafferImage.OpenColorIOAlgo.variables( script2.context() ) ), { "testA", "testB2" } )
		self.assertEqual( GafferImage.OpenColorIOAlgo.getVariable( script2.context(), "testA" ), "testValueA" )
		self.assertEqual( GafferImage.OpenColorIOAlgo.getVariable( script2.context(), "testB2" ), "testValueB2" )

	def testConfigAppliesDuringExecution( self ) :

		script = Gaffer.ScriptNode()
		plug = GafferImage.OpenColorIOConfigPlug.acquireDefaultConfigPlug( script )
		plug["config"].setValue( "test.ocio" )
		plug["variables"].addChild( Gaffer.NameValuePlug( "testA", "testValueA", defaultEnabled = True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		script["writer"] = GafferDispatchTest.TextWriter()
		script["writer"]["fileName"].setValue( self.temporaryDirectory() / "test.txt" )
		script["writer"]["text"].setValue( "${ocio:config}, ${ocio:stringVar:testA}" )

		dispatcher = GafferDispatch.LocalDispatcher()
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() / "testDispatch" )
		dispatcher["executeInBackground"].setValue( True )

		dispatcher.dispatch( [ script["writer"] ] )
		dispatcher.jobPool().waitForAll()

		with open( script["writer"]["fileName"].getValue() ) as f :
			self.assertEqual( f.readlines(), [ "test.ocio, testValueA" ] )

if __name__ == "__main__":
	unittest.main()
