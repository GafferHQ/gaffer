##########################################################################
#
#  Copyright (c) 2014, John Haddon. All rights reserved.
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

import os.path

import Gaffer
import GafferTest

class ModuleTest( GafferTest.TestCase ) :

	def testNamespacePollution( self ) :

		import GafferScene

		self.assertRaises( AttributeError, getattr, GafferScene, "IECore" )
		self.assertRaises( AttributeError, getattr, GafferScene, "Gaffer" )
		self.assertRaises( AttributeError, getattr, GafferScene, "GafferScene" )
		self.assertRaises( AttributeError, getattr, GafferScene, "GafferImage" )

	def testDoesNotImportUI( self ) :

		self.assertModuleDoesNotImportUI( "GafferScene" )
		self.assertModuleDoesNotImportUI( "GafferSceneTest" )

	def testLoadScriptsFrom0_55( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.join( os.path.dirname( __file__ ), "scripts", "parentAndCopy-0.55.0.0.gfr" ) )
		s.load()

		self.assertEqual( s["Parent"]["in"].getInput(), s["Plane"]["out"] )
		self.assertEqual( s["Parent"]["child"].getInput(), s["Sphere"]["out"] )

		self.assertEqual( s["CopyAttributes"]["in"][0].getInput(), s["Parent"]["out"] )
		self.assertEqual( s["CopyAttributes"]["in"][1].getInput(), s["Sphere"]["out"] )
		self.assertEqual( s["CopyAttributes"]["copyFrom"].getValue(), "/sphere" )

		self.assertEqual( s["CopyOptions"]["in"].getInput(), s["CopyAttributes"]["out"] )
		self.assertEqual( s["CopyOptions"]["source"].getInput(), s["StandardOptions"]["out"] )
		self.assertEqual( s["CopyOptions"]["options"].getValue(), "a b c" )

if __name__ == "__main__":
	unittest.main()
