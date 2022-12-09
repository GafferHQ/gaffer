##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

import pathlib
import unittest

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class FilterProcessorTest( GafferSceneTest.SceneTestCase ) :

	def testLoadFromVersion0_27( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( pathlib.Path( __file__ ).parent / "scripts" / "filterProcessor-0.27.0.0.gfr" )
		s.load()

		self.assertEqual( len( s["FilterSwitch"]["in"] ), 3 )
		for c in s["FilterSwitch"]["in"] :
			self.assertIsInstance( c, GafferScene.FilterPlug )

		self.assertEqual( len( s["UnionFilter"]["in"] ), 3 )
		for c in s["UnionFilter"]["in"] :
			self.assertIsInstance( c, GafferScene.FilterPlug )

		self.assertEqual( s["FilterSwitch"]["in"][0].getInput(), s["PathFilter"]["out"] )
		self.assertEqual( s["FilterSwitch"]["in"][1].getInput(), s["PathFilter1"]["out"] )
		self.assertEqual( s["FilterSwitch"]["in"][2].getInput(), None )

		self.assertEqual( s["UnionFilter"]["in"][0].getInput(), s["FilterSwitch"]["out"] )
		self.assertEqual( s["UnionFilter"]["in"][1].getInput(), s["PathFilter2"]["out"] )
		self.assertEqual( s["UnionFilter"]["in"][2].getInput(), None )
		self.assertEqual( s["UnionFilter"]["in"][2].getValue(), IECore.PathMatcher.Result.NoMatch )

		self.assertEqual( s["ShaderAssignment"]["filter"].getInput(), s["UnionFilter"]["out"] )

	def testLoadBoxedFromVersion0_27( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( pathlib.Path( __file__ ).parent / "scripts" / "filterProcessorBoxed-0.27.0.0.gfr" )
		s.load()

		self.assertEqual( len( s["Box"]["FilterSwitch"]["in"] ), 3 )
		for c in s["Box"]["FilterSwitch"]["in"] :
			self.assertIsInstance( c, GafferScene.FilterPlug )

		self.assertEqual( len( s["Box"]["UnionFilter"]["in"] ), 3 )
		for c in s["Box"]["UnionFilter"]["in"] :
			self.assertIsInstance( c, GafferScene.FilterPlug )

		self.assertEqual( s["Box"]["FilterSwitch"]["in"][0].getInput(), s["Box"]["PathFilter"]["out"] )
		self.assertEqual( s["Box"]["FilterSwitch"]["in"][1].getInput(), s["Box"]["PathFilter1"]["out"] )
		self.assertEqual( s["Box"]["FilterSwitch"]["in"][2].getInput(), None )

		self.assertEqual( s["Box"]["UnionFilter"]["in"][0].getInput(), s["Box"]["FilterSwitch"]["out"] )
		self.assertEqual( s["Box"]["UnionFilter"]["in"][1].getInput(), s["Box"]["PathFilter2"]["out"] )
		self.assertEqual( s["Box"]["UnionFilter"]["in"][2].getInput(), None )
		self.assertEqual( s["Box"]["UnionFilter"]["in"][2].getValue(), IECore.PathMatcher.Result.NoMatch )

		self.assertEqual( s["Box"]["ShaderAssignment"]["filter"].getInput(), s["Box"]["UnionFilter"]["out"] )

if __name__ == "__main__":
	unittest.main()
