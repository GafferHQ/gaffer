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

import PyOpenColorIO

import Gaffer
import GafferImage
import GafferImageTest

class OpenColorIOAlgoTest( GafferImageTest.ImageTestCase ) :

	def testAccessors( self ) :

		c = Gaffer.Context()
		self.assertEqual( GafferImage.OpenColorIOAlgo.getConfig( c ), "" )

		studioConfig = "ocio://studio-config-v1.0.0_aces-v1.3_ocio-v2.1"
		GafferImage.OpenColorIOAlgo.setConfig( c, studioConfig )
		self.assertEqual( GafferImage.OpenColorIOAlgo.getConfig( c ), studioConfig )

		self.assertEqual( GafferImage.OpenColorIOAlgo.getVariable( c, "test" ), "" )
		self.assertEqual( GafferImage.OpenColorIOAlgo.variables( c ), [] )
		GafferImage.OpenColorIOAlgo.addVariable( c, "test", "value" )
		self.assertEqual( GafferImage.OpenColorIOAlgo.getVariable( c, "test" ), "value" )
		self.assertEqual( GafferImage.OpenColorIOAlgo.variables( c ), [ "test" ] )
		GafferImage.OpenColorIOAlgo.removeVariable( c, "test" )
		self.assertEqual( GafferImage.OpenColorIOAlgo.getVariable( c, "test" ), "" )
		self.assertEqual( GafferImage.OpenColorIOAlgo.variables( c ), [] )

	def testCurrentConfig( self ) :

		defaultConfig = GafferImage.OpenColorIOAlgo.currentConfig()
		self.assertIsInstance( defaultConfig, PyOpenColorIO.Config )
		self.assertEqual( defaultConfig.getCacheID(), PyOpenColorIO.GetCurrentConfig().getCacheID() )

		with Gaffer.Context() as c :

			GafferImage.OpenColorIOAlgo.setConfig( c, ( self.openColorIOPath() / "context.ocio" ).as_posix() )
			customConfig = GafferImage.OpenColorIOAlgo.currentConfig()
			self.assertIsInstance( customConfig, PyOpenColorIO.Config )
			self.assertEqual( customConfig.getCacheID(), PyOpenColorIO.Config.CreateFromFile( c["ocio:config"] ).getCacheID() )

			GafferImage.OpenColorIOAlgo.setConfig( c, "" )
			defaultConfig2 = GafferImage.OpenColorIOAlgo.currentConfig()
			self.assertIsInstance( defaultConfig2, PyOpenColorIO.Config )
			self.assertEqual( defaultConfig2.getCacheID(), PyOpenColorIO.GetCurrentConfig().getCacheID() )
			self.assertIs( defaultConfig2, defaultConfig )

	def testCurrentConfigAndContext( self ) :

		defaultConfig, defaultContext = GafferImage.OpenColorIOAlgo.currentConfigAndContext()
		self.assertIsInstance( defaultConfig, PyOpenColorIO.Config )
		self.assertEqual( defaultConfig.getCacheID(), PyOpenColorIO.GetCurrentConfig().getCacheID() )
		self.assertIsInstance( defaultContext, PyOpenColorIO.Context )
		self.__assertContextsEqual( defaultContext, PyOpenColorIO.GetCurrentConfig().getCurrentContext() )

		with Gaffer.Context() as c :

			GafferImage.OpenColorIOAlgo.setConfig( c, ( self.openColorIOPath() / "context.ocio" ).as_posix() )
			GafferImage.OpenColorIOAlgo.addVariable( c, "LUT", "srgb.spi1d" )

			customConfig, customContext = GafferImage.OpenColorIOAlgo.currentConfigAndContext()
			expectedConfig = PyOpenColorIO.Config.CreateFromFile( GafferImage.OpenColorIOAlgo.getConfig( c ) )
			self.assertEqual( customConfig.getCacheID(), expectedConfig.getCacheID() )
			self.assertEqual(
				dict( customContext.getStringVars() ),
				dict( expectedConfig.getCurrentContext().getStringVars(), LUT = "srgb.spi1d" )
			)

	def testCurrentConfigAndContextHash( self ) :

		with Gaffer.Context() as c :

			h1 = GafferImage.OpenColorIOAlgo.currentConfigAndContextHash()

			GafferImage.OpenColorIOAlgo.setConfig( c, str( self.openColorIOPath() / "context.ocio" ) )
			h2 = GafferImage.OpenColorIOAlgo.currentConfigAndContextHash()

			GafferImage.OpenColorIOAlgo.addVariable( c, "LUT", "srgb.spi1d" )
			h3 = GafferImage.OpenColorIOAlgo.currentConfigAndContextHash()

		self.assertEqual( len( { h1, h2, h3 } ), 3 )

	def testWorkingSpace( self ) :

		c = Gaffer.Context()
		self.assertEqual( GafferImage.OpenColorIOAlgo.getWorkingSpace( c ), PyOpenColorIO.ROLE_SCENE_LINEAR )

		GafferImage.OpenColorIOAlgo.setWorkingSpace( c, "test" )
		self.assertEqual( GafferImage.OpenColorIOAlgo.getWorkingSpace( c ), "test" )

	def __assertContextsEqual( self, a, b ) :

		self.assertEqual( a.getSearchPath(), b.getSearchPath() )
		self.assertEqual( a.getWorkingDir(), b.getWorkingDir() )
		for av, bv in zip( a.getStringVars(), b.getStringVars() ) :
			self.assertEqual( av, bv )

if __name__ == "__main__":
	unittest.main()
