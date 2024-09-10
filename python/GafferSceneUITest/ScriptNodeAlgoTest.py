##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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
#        promote products derived from this software without specifiscript prior
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

import IECore

import Gaffer
import GafferTest
import GafferUITest
import GafferScene
import GafferSceneUI

class ScriptNodeAlgoTest( GafferUITest.TestCase ) :

	def testSelectedPaths( self ) :

		script = Gaffer.ScriptNode()

		GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( script, IECore.PathMatcher( [ "/" ] ) )
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( script ), IECore.PathMatcher( [ "/" ] ) )

		GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( script, IECore.PathMatcher( [ "/", "/A" ] ) )
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( script ), IECore.PathMatcher( [ "/", "/A" ] ) )

		GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( script, IECore.PathMatcher( [ "/", "/A", "/A/C" ] ) )
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( script ), IECore.PathMatcher( [ "/", "/A", "/A/C" ] )  )

		GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( script, IECore.PathMatcher( [ "/A/C", "/A/B/D" ] ) )
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( script ), IECore.PathMatcher( [ "/A/C", "/A/B/D" ] )  )

	def testVisibleSet( self ) :

		script = Gaffer.ScriptNode()

		v = GafferScene.VisibleSet( expansions = IECore.PathMatcher( [ "/A" ] ) )
		GafferSceneUI.ScriptNodeAlgo.setVisibleSet( script, v )
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getVisibleSet( script ), v )

	def testSelectionIsCopied( self ) :

		script = Gaffer.ScriptNode()

		s = IECore.PathMatcher( [ "/a" ] )
		GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( script, s )
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( script ), s )

		s.addPath( "/a/b" )
		self.assertNotEqual( GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( script ), s )

		s = GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( script )
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( script ), s )

		s.addPath( "/a/b" )
		self.assertNotEqual( GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( script ), s )

	def testVisibleSetIsCopied( self ) :

		script = Gaffer.ScriptNode()

		v = GafferScene.VisibleSet( expansions = IECore.PathMatcher( [ "/a" ] ) )
		GafferSceneUI.ScriptNodeAlgo.setVisibleSet( script, v )
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getVisibleSet( script ), v )

		v.expansions.addPath( "/a/b" )
		self.assertNotEqual( GafferSceneUI.ScriptNodeAlgo.getVisibleSet( script ), v )

		v = GafferSceneUI.ScriptNodeAlgo.getVisibleSet( script )
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getVisibleSet( script ), v )

		v.expansions.addPath( "/a/b" )
		self.assertNotEqual( GafferSceneUI.ScriptNodeAlgo.getVisibleSet( script ), v )

	def testLastSelectedPath( self ) :

		script = Gaffer.ScriptNode()
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getLastSelectedPath( script ), "" )

		s = IECore.PathMatcher( [ "/a", "/b" ] )
		GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( script, s )
		self.assertTrue( s.match( GafferSceneUI.ScriptNodeAlgo.getLastSelectedPath( script ) ) & s.Result.ExactMatch )

		GafferSceneUI.ScriptNodeAlgo.setLastSelectedPath( script, "/c" )
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getLastSelectedPath( script ), "/c" )
		s = GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( script )
		self.assertEqual( s, IECore.PathMatcher( [ "/a", "/b", "/c" ] ) )

		GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( script, IECore.PathMatcher() )
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getLastSelectedPath( script ), "" )

	def testSignals( self ) :

		script1 = Gaffer.ScriptNode()
		script2 = Gaffer.ScriptNode()

		visibleSetCs1 = GafferTest.CapturingSlot( GafferSceneUI.ScriptNodeAlgo.visibleSetChangedSignal( script1 ) )
		visibleSetCs2 = GafferTest.CapturingSlot( GafferSceneUI.ScriptNodeAlgo.visibleSetChangedSignal( script2 ) )

		# Modifying one thing should signal for only that thing.

		visibleSet = GafferScene.VisibleSet( inclusions = IECore.PathMatcher( [ "/A" ] ) )
		GafferSceneUI.ScriptNodeAlgo.setVisibleSet( script1, visibleSet )
		self.assertEqual( len( visibleSetCs1 ), 1 )
		self.assertEqual( len( visibleSetCs2 ), 0 )

		# A no-op shouldn't signal.

		GafferSceneUI.ScriptNodeAlgo.setVisibleSet( script1, visibleSet )
		self.assertEqual( len( visibleSetCs1 ), 1 )
		self.assertEqual( len( visibleSetCs2 ), 0 )

	def testVisibleSetExpansionUtilities( self ) :

		# A
		# |__B
		#    |__D
		#    |__E
		# |__C
		#    |__F
		#    |__G

		script = Gaffer.ScriptNode()

		script["G"] = GafferScene.Sphere()
		script["G"]["name"].setValue( "G" )

		script["F"] = GafferScene.Sphere()
		script["F"]["name"].setValue( "F" )

		script["D"] = GafferScene.Sphere()
		script["D"]["name"].setValue( "D" )

		script["E"] = GafferScene.Sphere()
		script["E"]["name"].setValue( "E" )

		script["C"] = GafferScene.Group()
		script["C"]["name"].setValue( "C" )

		script["C"]["in"][0].setInput( script["F"]["out"] )
		script["C"]["in"][1].setInput( script["G"]["out"] )

		script["B"] = GafferScene.Group()
		script["B"]["name"].setValue( "B" )

		script["B"]["in"][0].setInput( script["D"]["out"] )
		script["B"]["in"][1].setInput( script["E"]["out"] )

		A = GafferScene.Group()
		A["name"].setValue( "A" )
		A["in"][0].setInput( script["B"]["out"] )
		A["in"][1].setInput( script["C"]["out"] )

		GafferSceneUI.ScriptNodeAlgo.expandInVisibleSet( script, IECore.PathMatcher( [ "/A/B", "/A/C" ] ) )
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getVisibleSet( script ).expansions, IECore.PathMatcher( [ "/", "/A", "/A/B", "/A/C" ] ) )

		GafferSceneUI.ScriptNodeAlgo.setVisibleSet( script, GafferScene.VisibleSet() )
		GafferSceneUI.ScriptNodeAlgo.expandInVisibleSet( script, IECore.PathMatcher( [ "/A/B", "/A/C" ] ), expandAncestors = False )
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getVisibleSet( script ).expansions, IECore.PathMatcher( [ "/A/B", "/A/C" ] ) )

		GafferSceneUI.ScriptNodeAlgo.setVisibleSet( script, GafferScene.VisibleSet( expansions = IECore.PathMatcher( [ "/" ] ) ) )
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getVisibleSet( script ).expansions, IECore.PathMatcher( [ "/" ] ) )
		newLeafs = GafferSceneUI.ScriptNodeAlgo.expandDescendantsInVisibleSet( script, IECore.PathMatcher( [ "/" ] ), A["out"] )
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getVisibleSet( script ).expansions, IECore.PathMatcher( [ "/", "/A", "/A/B", "/A/C" ] ) )
		self.assertEqual( newLeafs, IECore.PathMatcher( [ "/A/B/D", "/A/B/E", "/A/C/G", "/A/C/F" ] ) )

		GafferSceneUI.ScriptNodeAlgo.setVisibleSet( script, GafferScene.VisibleSet( expansions = IECore.PathMatcher( [ "/" ] ) ) )
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getVisibleSet( script ).expansions, IECore.PathMatcher( [ "/" ] ) )
		newLeafs = GafferSceneUI.ScriptNodeAlgo.expandDescendantsInVisibleSet( script, IECore.PathMatcher( [ "/" ] ), A["out"], depth = 1 )
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getVisibleSet( script ).expansions, IECore.PathMatcher( [ "/", "/A" ] ) )
		self.assertEqual( newLeafs, IECore.PathMatcher( [ "/A/B", "/A/C" ] ) )

		newLeafs = GafferSceneUI.ScriptNodeAlgo.expandDescendantsInVisibleSet( script, IECore.PathMatcher( [ "/A/C" ] ), A["out"], depth = 1 )
		self.assertEqual( GafferSceneUI.ScriptNodeAlgo.getVisibleSet( script ).expansions, IECore.PathMatcher( [ "/", "/A", "/A/C" ] ) )
		self.assertEqual( newLeafs, IECore.PathMatcher( [ "/A/C/G", "/A/C/F" ] ) )

if __name__ == "__main__":
	unittest.main()
