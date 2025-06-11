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
#      * Neither the name of Image Engine Design Inc nor the names of
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

import arnold

import os
import pathlib

import IECoreScene

import GafferScene
import GafferSceneTest

class USDProceduralTest( GafferSceneTest.SceneTestCase ) :

	def testEnvironment( self ) :

		self.assertIn(
			str( pathlib.Path( os.path.expandvars( "$ARNOLD_ROOT" ) ) / "plugins" / "usd" / "usdArnold" / "resources" ),
			os.environ["PXR_PLUGINPATH_NAME"].split( os.pathsep )
		)

	@unittest.skipIf( [ int( x ) for x in arnold.AiGetVersion()[:2] ] < [ 7, 4 ], "Not fully supported by earlier Arnold versions" )
	def testLoad( self ) :

		s = GafferScene.SceneReader()
		s["fileName"].setValue( pathlib.Path( __file__ ).parent / "usdFiles" / "arnoldProcedural.usda" )

		self.assertSceneValid( s["out"] )

		for name in [ "ArnoldAlembic", "ArnoldProceduralCustom", "ArnoldUsd" ] :
			with self.subTest( name = name ) :
				self.assertTrue( name in s["out"].childNames( "/" ) )
				self.assertIsInstance( s["out"].object( f"/{name}" ), IECoreScene.ExternalProcedural )
				self.assertIn( "filename", s["out"].object( f"/{name}" ).parameters() )

if __name__ == "__main__":
	unittest.main()
