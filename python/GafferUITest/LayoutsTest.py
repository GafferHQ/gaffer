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

import os
import subprocess

import Gaffer
import GafferUI
import GafferUITest

class LayoutsTest( GafferUITest.TestCase ) :

	def testAcquire( self ) :

		a = Gaffer.ApplicationRoot( "testApp" )
		self.assertIsInstance( GafferUI.Layouts.acquire( a ), GafferUI.Layouts )
		self.assertIs( GafferUI.Layouts.acquire( a ), GafferUI.Layouts.acquire( a ) )

	def testAddAndRemove( self ) :

		a = Gaffer.ApplicationRoot( "testApp" )
		l = GafferUI.Layouts.acquire( a )
		self.assertEqual( l.names(), [] )

		l.add( "JustTheGraphEditor", "GafferUI.GraphEditor( script )" )
		self.assertEqual( l.names(), [ "JustTheGraphEditor" ] )

		l.add( "JustTheNodeEditor", "GafferUI.NodeEditor( script )" )
		self.assertEqual( l.names(), [ "JustTheGraphEditor", "JustTheNodeEditor" ] )

		l.remove( "JustTheGraphEditor" )
		self.assertEqual( l.names(), [ "JustTheNodeEditor" ] )

		l.remove( "JustTheNodeEditor" )
		self.assertEqual( l.names(), [] )

	def testPersistence( self ) :

		a = Gaffer.ApplicationRoot( "testApp" )
		l = GafferUI.Layouts.acquire( a )
		self.assertEqual( l.names(), [] )

		l.add( "JustTheGraphEditor", "GafferUI.GraphEditor( script )" )
		self.assertEqual( l.names(), [ "JustTheGraphEditor" ] )
		self.assertEqual( l.names( persistent = False ), [ "JustTheGraphEditor" ] )
		self.assertEqual( l.names( persistent = True ), [] )

		l.add( "JustTheNodeEditor", "GafferUI.NodeEditor( script )", persistent = True )
		self.assertEqual( l.names(), [ "JustTheGraphEditor", "JustTheNodeEditor" ] )
		self.assertEqual( l.names( persistent = False ), [ "JustTheGraphEditor" ] )
		self.assertEqual( l.names( persistent = True ), [ "JustTheNodeEditor" ] )

	def testNoPersistentLayoutsInDefaultConfigs( self ) :

		if "GAFFERUITEST_LAYOUTTEST_SUBPROCESS" not in os.environ :
			# Run test in subprocess, because we don't want to pollute the other
			# tests with the configs we load.
			try :
				env = os.environ.copy()
				env["GAFFERUITEST_LAYOUTTEST_SUBPROCESS"] = "1"
				subprocess.check_output(
					[ str( Gaffer.executablePath() ), "test", "GafferUITest.LayoutsTest.testNoPersistentLayoutsInDefaultConfigs" ],
					stderr = subprocess.STDOUT,
					env = env,
				)
			except subprocess.CalledProcessError as e :
				self.fail( e.output )
			return

		app = Gaffer.Application()

		# Load the GUI config, making sure we only use the standard
		# startup files, and not any others from the current environment
		# (the user running these tests may have their own personal configs).
		os.environ["GAFFER_STARTUP_PATHS"] = str( Gaffer.rootPath() / "startup" )
		app._executeStartupFiles( "gui" )

		layouts = GafferUI.Layouts.acquire( app )
		self.assertEqual( layouts.names( persistent = True ), [] )
		self.assertGreater( len( layouts.names() ), 0 )

	def testRestore( self ) :

		s = Gaffer.ScriptNode()
		c = GafferUI.CompoundEditor( s )

		editors = list((
			GafferUI.NodeEditor( s ),
			GafferUI.AnimationEditor( s ),
			GafferUI.GraphEditor( s ),
			GafferUI.PythonEditor( s )
		))

		editorTypes = [ type(e) for e in editors ]

		for e in editors[:2] :
			c.addEditor( e )

		p = c._createDetachedPanel()

		for e in editors[2:] :
			p.addEditor( e )

		self.assertEqual( len(c._detachedPanels()), 1 )
		self.assertEqual( c.editors(), editors )

		a = Gaffer.ApplicationRoot( "testApp" )
		l = GafferUI.Layouts.acquire( a )
		l.add( "ReprTest", repr(c), persistent = False )

		cc = l.create( "ReprTest", s )

		self.assertEqual( len(cc._detachedPanels()), 1 )

		ct = [ type(e) for e in cc.editors() ]
		self.assertEqual( ct, editorTypes )
		self.assertEqual( repr(cc.editors()), repr(editors) )

	def testNodeSetRestore( self ) :

		s = Gaffer.ScriptNode()
		c = GafferUI.CompoundEditor( s )

		editors = list((
			GafferUI.NodeEditor( s ),
			GafferUI.NodeEditor( s ),
			GafferUI.AnimationEditor( s ),
			GafferUI.NodeEditor( s )
		))

		editors[0].setNodeSet( Gaffer.NumericBookmarkSet( s, 1 ) )
		editors[1].setNodeSet( Gaffer.NumericBookmarkSet( s, 2 ) )
		editors[2].setNodeSet( Gaffer.NumericBookmarkSet( s, 3 ) )

		for e in editors :
			c.addEditor( e )

		a = Gaffer.ApplicationRoot( "testApp" )
		l = GafferUI.Layouts.acquire( a )
		l.add( "ReprNodeSetTest", repr(c), persistent = False )

		cc = l.create( "ReprNodeSetTest", s )

		editors = cc.editors()

		ns = editors[0].getNodeSet()
		self.assertTrue( isinstance( ns, Gaffer.NumericBookmarkSet ) )
		self.assertTrue( ns.getBookmark(), 1 )

		ns = editors[1].getNodeSet()
		self.assertTrue( isinstance( ns, Gaffer.NumericBookmarkSet ) )
		self.assertTrue( ns.getBookmark(), 2 )

		ns = editors[2].getNodeSet()
		self.assertTrue( isinstance( ns, Gaffer.NumericBookmarkSet ) )
		self.assertTrue( ns.getBookmark(), 3 )

		ns = editors[3].getNodeSet()
		self.assertTrue( isinstance( ns, Gaffer.StandardSet ) )

	def testMissingEditorType( self ) :

		applicationRoot = Gaffer.ApplicationRoot( "testApp" )
		layouts = GafferUI.Layouts.acquire( applicationRoot )

		# Register a layout containing an editor that doesn't exist.
		layouts.add( "MissingEditor", "GafferUI.NonexistentEditor( scriptNode )" )

		# Check that we can still create such a layout, and that
		# it has a proxy with the expected properties.
		script = Gaffer.ScriptNode()
		layout = layouts.create( "MissingEditor", script )
		self.assertIsInstance( layout, GafferUI.Editor )
		self.assertEqual( layout.getTitle(), "Nonexistent Editor" )

		# Save the layout again and check that the same applies.
		layouts.add( "MissingEditor2", layout )
		layout2 = layouts.create( "MissingEditor2", script )
		self.assertIsInstance( layout2, GafferUI.Editor )
		self.assertEqual( layout2.getTitle(), "Nonexistent Editor" )

	def testMissingEditorModule( self ) :

		applicationRoot = Gaffer.ApplicationRoot( "testApp" )
		layouts = GafferUI.Layouts.acquire( applicationRoot )

		# Register a layout containing an editor from a module that doesn't exist.
		layouts.add( "MissingEditor", "NonexistentGafferModule.NonexistentEditor( scriptNode )" )

		# Check that we can still create such a layout, and that
		# it has a proxy with the expected properties.
		script = Gaffer.ScriptNode()
		layout = layouts.create( "MissingEditor", script )
		self.assertIsInstance( layout, GafferUI.Editor )
		self.assertEqual( layout.getTitle(), "Nonexistent Editor" )

		# Save the layout again and check that the same applies.
		layouts.add( "MissingEditor2", layout )
		layout2 = layouts.create( "MissingEditor2", script )
		self.assertIsInstance( layout2, GafferUI.Editor )
		self.assertEqual( layout2.getTitle(), "Nonexistent Editor" )

if __name__ == "__main__":
	unittest.main()
