##########################################################################
#
#  Copyright (c) 2018, Esteban Tovagliari. All rights reserved.
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

import sys
import unittest

import appleseed as asr

import IECore

import Gaffer
import GafferScene
import GafferTest
import GafferAppleseed

from .AppleseedTest import appleseedProjectSchemaPath

@unittest.skipIf( sys.platform == 'darwin', "Unknown segfault on Mac see #3234" )
class AppleseedCapsuleTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__scriptFileName = self.temporaryDirectory() + "/test.gfr"

	def testCapsules( self ) :

		s = Gaffer.ScriptNode()

		s["sphere"] = GafferScene.Sphere( "sphere" )
		s["sphere1"] = GafferScene.Sphere( "sphere1" )

		s["group"] = GafferScene.Group( "group" )
		s["group"]["in"][0].setInput( s["sphere"]["out"] )
		s["group"]["in"][1].setInput( s["sphere1"]["out"] )

		s["path_filter"] = GafferScene.PathFilter( "path_filter" )
		s["path_filter"]["paths"].setValue( IECore.StringVectorData( [ '*' ] ) )

		s["encapsulate"] = GafferScene.Encapsulate( "encapsulate" )
		s["encapsulate"]["in"].setInput( s["group"]["out"] )
		s["encapsulate"]["filter"].setInput( s["path_filter"]["out"] )

		s["duplicate"] = GafferScene.Duplicate( "duplicate" )
		s["duplicate"]["in"].setInput( s["encapsulate"]["out"] )
		s["duplicate"]["target"].setValue( 'group' )
		s["duplicate"]["copies"].setValue( 2 )

		s["render"] = GafferAppleseed.AppleseedRender()
		s["render"]["in"].setInput( s["duplicate"]["out"] )
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )

		projectFilename =  self.temporaryDirectory() + "/test.appleseed"

		s["render"]["fileName"].setValue( projectFilename )
		s["render"]["task"].execute()

		reader = asr.ProjectFileReader()
		options = asr.ProjectFileReaderOptions.OmitReadingMeshFiles
		project = reader.read( projectFilename, appleseedProjectSchemaPath(), options )
		scene = project.get_scene()
		mainAssembly = scene.assemblies().get_by_name( "assembly" )

		# Check that we have 3 instances of 1 capsule.
		self.assertEqual( len( mainAssembly.assemblies() ), 1)
		self.assertEqual( len( mainAssembly.assembly_instances() ), 3 )

		capsuleAssemblyName = mainAssembly.assemblies().keys()[0]
		capsuleAssembly = mainAssembly.assemblies()[capsuleAssemblyName]

		# Check that we have 2 instances of 1 sphere inside the capsule.
		self.assertEqual( len( capsuleAssembly.assemblies() ), 1)
		self.assertEqual( len( capsuleAssembly.assembly_instances() ), 2 )

if __name__ == "__main__":
	unittest.main()
