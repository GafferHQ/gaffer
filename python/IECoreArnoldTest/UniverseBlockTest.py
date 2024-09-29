##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     * Neither the name of Image Engine Design nor the names of any
#       other contributors to this software may be used to endorse or
#       promote products derived from this software without specific prior
#       written permission.
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

from __future__ import with_statement

import os
import pathlib
import unittest
import ctypes
import subprocess

import arnold

import IECore
import IECoreArnold

class UniverseBlockTest( unittest.TestCase ) :

	def testWritable( self ) :

		def createBlock( writable, expectedUniverse = None ) :

			with IECoreArnold.UniverseBlock( writable ) as universe :

				self.assertIsNotNone( universe )

				if expectedUniverse is not None :
					self.assertEqual(
						ctypes.addressof( universe.contents ),
						ctypes.addressof( expectedUniverse.contents )
					)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			self.assertIsNotNone( universe )
			createBlock( False )

		with IECoreArnold.UniverseBlock( writable = False ) as universe :

			self.assertIsNotNone( universe )

			createBlock( True )
			createBlock( False, expectedUniverse = universe )

	def testMetadataLoading( self ) :

		metadataPath = pathlib.Path( __file__ ).parent / "metadata"
		if str( metadataPath ) not in os.environ["ARNOLD_PLUGIN_PATH"].split( os.pathsep ) :

			# Relaunch test in subprocess with our metadata on the plugin path.

			env = os.environ.copy()
			env["ARNOLD_PLUGIN_PATH"] = env["ARNOLD_PLUGIN_PATH"] + os.pathsep + str( metadataPath )

			try :
				subprocess.check_output(
					[ "gaffer" if os.name != "nt" else "gaffer.cmd", "test", "IECoreArnoldTest.UniverseBlockTest.testMetadataLoading" ],
					env = env, stderr = subprocess.STDOUT
				)
			except subprocess.CalledProcessError as e :
				self.fail( e.output )

		else :

			# Our metadata is on the plugin path. Check that it has been loaded.

			with IECoreArnold.UniverseBlock( writable = False ) :

				e = arnold.AiNodeEntryLookUp( "options" )

				s = arnold.AtStringStruct()
				i = ctypes.c_int()

				arnold.AiMetaDataGetStr( e, "", "cortex.testString", s )
				self.assertEqual( arnold.AtStringToStr( s ), "test" )

				arnold.AiMetaDataGetInt( e, "", "cortex.testInt", i )
				self.assertEqual( i.value, 25 )

				arnold.AiMetaDataGetStr( e, "AA_samples", "cortex.testString", s )
				self.assertEqual( arnold.AtStringToStr( s ), "test2" )

				arnold.AiMetaDataGetInt( e, "AA_samples", "cortex.testInt", i )
				self.assertEqual( i.value, 12 )

	@unittest.skipIf( os.name == "nt", "Kick not currently working on Windows.")
	def testKickNodes( self ) :

		# Running `kick -nodes` will load any plugins that might link to
		# `libIECoreArnold`. If UniverseBlock tries to reinitialise Arnold
		# in this situation, very bad things occur, so we must avoid it.

		output = subprocess.check_output( [ "kick", "-nodes" ], universal_newlines=True )
		self.assertNotIn( "AiBegin", output )
		self.assertNotIn( "AiEnd", output )
		self.assertNotIn( "is already installed", output )
		self.assertNotIn( "Node entry does not exist", output )
		self.assertIn( "ieDisplay", output )

if __name__ == "__main__":
	unittest.main()
