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

import Gaffer
import GafferUI
import GafferSceneUI
import GafferOSL
import GafferOSLTest
import GafferOSLUI

class OSLCodeUITest( GafferOSLTest.OSLTestCase ) :

	def testChangingOutputNodules( self ) :

		node = GafferOSL.OSLCode()
		nodeGadget1 = GafferUI.NodeGadget.create( node )

		self.assertTrue( isinstance( nodeGadget1.nodule( node["out"] ), GafferUI.StandardNodule ) )

		node["out"]["o"] = Gaffer.FloatPlug(
			direction = Gaffer.Plug.Direction.Out,
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
		)

		nodeGadget2 = GafferUI.NodeGadget.create( node )

		self.assertTrue( isinstance( nodeGadget1.nodule( node["out"] ), GafferUI.CompoundNodule ) )
		self.assertTrue( isinstance( nodeGadget1.nodule( node["out"]["o"] ), GafferUI.StandardNodule ) )
		self.assertTrue( isinstance( nodeGadget2.nodule( node["out"] ), GafferUI.CompoundNodule ) )
		self.assertTrue( isinstance( nodeGadget2.nodule( node["out"]["o"] ), GafferUI.StandardNodule ) )
		self.assertEqual( nodeGadget1.nodule( node["out"] ).bound(), nodeGadget2.nodule( node["out"] ).bound() )

		del node["out"]["o"]
		self.assertTrue( isinstance( nodeGadget1.nodule( node["out"] ), GafferUI.StandardNodule ) )
		self.assertTrue( isinstance( nodeGadget2.nodule( node["out"] ), GafferUI.StandardNodule ) )

	def testUISurvivesCompilationError( self ) :

		script = Gaffer.ScriptNode()

		script["node"] = GafferOSL.OSLCode()
		script["node"]["parameters"].addChild( Gaffer.StringPlug( "inString", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		script["node"]["parameters"].addChild( Gaffer.IntPlug( "inInt", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		script["node"]["parameters"].addChild( Gaffer.FloatPlug( "inFloat", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		script["node"]["out"].addChild( Gaffer.StringPlug( "outString", direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		script["node"]["out"].addChild( Gaffer.IntPlug( "outInt", direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		script["node"]["out"].addChild( Gaffer.Color3fPlug( "outColor", direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		# Make a shader that won't compile.

		script["node"]["code"].setValue( "i am a compilation error" )
		with self.assertRaisesRegex( Gaffer.ProcessException, ".*Syntax error.*" ) :
			script["node"]["name"].getValue()

		# And check that we can still create UIs for it without
		# throwing an exception.

		GafferUI.NodeUI.create( script["node"] )
		GafferUI.NodeGadget.create( script["node"] )
		GafferUI.GraphGadget( script )

if __name__ == "__main__":
	unittest.main()
