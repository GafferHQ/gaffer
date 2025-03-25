##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

class ShuffleRenderPassesTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		renderPasses = GafferScene.RenderPasses()
		renderPasses["names"].setValue( IECore.StringVectorData( [ "c", "a", "b" ] ) )

		shuffle = GafferScene.ShuffleRenderPasses()
		shuffle["in"].setInput( renderPasses["out"] )
		self.assertEqual( shuffle["out"].globals()["option:renderPass:names"], IECore.StringVectorData( [ "c", "a", "b" ] ) )

		shuffle["shuffles"].addChild( Gaffer.ShufflePlug( "a", "d" ) )
		self.assertEqual( shuffle["out"].globals()["option:renderPass:names"], IECore.StringVectorData( [ "c", "a", "d", "b" ] ) )

		shuffle["shuffles"].addChild( Gaffer.ShufflePlug( "a", "ad" ) )
		self.assertEqual( shuffle["out"].globals()["option:renderPass:names"], IECore.StringVectorData( [ "c", "a", "ad", "d", "b" ] ) )

		shuffle["shuffles"][1]["enabled"].setValue( False )
		self.assertEqual( shuffle["out"].globals()["option:renderPass:names"], IECore.StringVectorData( [ "c", "a", "d", "b" ] ) )

		shuffle["shuffles"][0]["deleteSource"].setValue( True )
		self.assertEqual( shuffle["out"].globals()["option:renderPass:names"], IECore.StringVectorData( [ "c", "d", "b" ] ) )

		renderPasses["names"].setValue( IECore.StringVectorData( [ "c", "a", "b", "z" ] ) )
		self.assertEqual( shuffle["out"].globals()["option:renderPass:names"], IECore.StringVectorData( [ "c", "d", "b", "z" ] ) )

		shuffle["shuffles"][0]["deleteSource"].setValue( False )
		self.assertEqual( shuffle["out"].globals()["option:renderPass:names"], IECore.StringVectorData( [ "c", "a", "d", "b", "z" ] ) )

		shuffle["shuffles"][1]["enabled"].setValue( True )
		self.assertEqual( shuffle["out"].globals()["option:renderPass:names"], IECore.StringVectorData( [ "c", "a", "ad", "d", "b", "z" ] ) )

		shuffle["enabled"].setValue( False )
		self.assertEqual( shuffle["out"].globals(), shuffle["in"].globals() )

	def testNameRemapping( self ) :

		options = GafferScene.CustomOptions()
		options["options"].addChild( Gaffer.NameValuePlug( "test:sourceName", "${renderPass}" ) )

		renderPasses = GafferScene.RenderPasses()
		renderPasses["in"].setInput( options["out"] )
		renderPasses["names"].setValue( IECore.StringVectorData( [ "c", "a", "b" ] ) )

		shuffle = GafferScene.ShuffleRenderPasses()
		shuffle["in"].setInput( renderPasses["out"] )
		shuffle["shuffles"].addChild( Gaffer.ShufflePlug( "a", "d" ) )

		self.assertEqual( shuffle["out"].globals()["option:renderPass:names"], IECore.StringVectorData( [ "c", "a", "d", "b" ] ) )
		self.assertEqual( shuffle["__sourceName"].getValue(), "" )
		self.assertEqual( shuffle["out"].globals()["option:test:sourceName"].value, "" )

		with Gaffer.Context() as context :

			for renderPass in [ "", "a", "c", "d", "other" ] :
				context["renderPass"] = renderPass
				self.assertEqual( shuffle["__sourceName"].getValue(), renderPass if renderPass != "d" else "a" )
				self.assertEqual( shuffle["out"].globals()["option:test:sourceName"].value, renderPass if renderPass != "d" else "a" )

			shuffle["shuffles"][0]["source"].setValue( "c" )
			context["renderPass"] = "d"
			self.assertEqual( shuffle["__sourceName"].getValue(), "c" )
			self.assertEqual( shuffle["out"].globals()["option:test:sourceName"].value, "c" )

			shuffle["shuffles"][0]["source"].setValue( "*" )
			shuffle["shuffles"][0]["destination"].setValue( "${source}_test" )

			for source, destination in [
				( "", "" ),
				( "a", "a" ),
				( "a", "a_test" ),
				( "b", "b" ),
				( "b", "b_test" ),
				( "c", "c" ),
				( "c", "c_test" ),
				( "other", "other" ),
			] :
				context["renderPass"] = destination
				self.assertEqual( shuffle["__sourceName"].getValue(), source )
				self.assertEqual( shuffle["out"].globals()["option:test:sourceName"].value, source )

if __name__ == "__main__":
	unittest.main()
