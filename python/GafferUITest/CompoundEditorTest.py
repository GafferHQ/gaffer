##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import weakref

import imath

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

class CompoundEditorTest( GafferUITest.TestCase ) :

	def testAddEditorLifetime( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		c = GafferUI.CompoundEditor( s )
		e = GafferUI.GraphEditor( s )
		c.addEditor( e )

		wc = weakref.ref( c )
		we = weakref.ref( e )

		del c
		del e

		self.assertEqual( wc(), None )
		self.assertEqual( we(), None )

	def testEditorsLifetime( self ) :

		s = Gaffer.ScriptNode()
		c = GafferUI.CompoundEditor( s )

		n = GafferUI.NodeEditor( s )
		c.addEditor( n )

		wc = weakref.ref( c )
		wn = weakref.ref( n )

		e = c.editors()
		self.assertTrue( e[0] is n )

		del e
		del c
		del n

		self.assertEqual( wc(), None )
		self.assertEqual( wn(), None )

	def testDetachedPanelsLifetime( self ) :

		s = Gaffer.ScriptNode()
		c = GafferUI.CompoundEditor( s )

		p = c._createDetachedPanel()

		wp = weakref.ref( p )

		ps = c._detachedPanels()
		self.assertTrue( ps[0] is p )

		del ps
		del p
		del c

		self.assertEqual( wp(), None )

	def testDetachedPanelInheritsDisplayTransform( self ) :

		class CapturingEditor( GafferUI.Editor ) :

			def __init__( self, scriptNode, **kw ) :

				GafferUI.Editor.__init__( self, GafferUI.Label(), scriptNode, **kw )
				self.displayTransformChanges = []

			def _displayTransformChanged( self ) :

				GafferUI.Editor._displayTransformChanged( self )
				self.displayTransformChanges.append( self.displayTransform() )

		displayTransform1 = lambda x : x * 1
		displayTransform2 = lambda x : x * 2

		script = Gaffer.ScriptNode()
		editor = GafferUI.CompoundEditor( script )
		scriptWindow = GafferUI.ScriptWindow.acquire( script )
		scriptWindow.setDisplayTransform( displayTransform1 )
		scriptWindow.setLayout( editor )
		self.assertIs( editor.displayTransform(), displayTransform1 )

		panel = editor._createDetachedPanel()
		capturingEditor = CapturingEditor( script )
		panel.addEditor( capturingEditor )
		self.assertIs( panel.displayTransform(), displayTransform1 )
		self.assertIs( capturingEditor.displayTransform(), displayTransform1 )
		self.assertEqual( capturingEditor.displayTransformChanges, [ displayTransform1 ] )

		scriptWindow.setDisplayTransform( displayTransform2 )
		self.assertIs( editor.displayTransform(), displayTransform2 )
		self.assertIs( panel.displayTransform(), displayTransform2 )
		self.assertIs( capturingEditor.displayTransform(), displayTransform2 )
		self.assertEqual( capturingEditor.displayTransformChanges, [ displayTransform1, displayTransform2 ] )

	def testReprLifetime( self ) :

		s = Gaffer.ScriptNode()
		c = GafferUI.CompoundEditor( s )

		wc = weakref.ref( c )
		repr( c )

		del c

		self.assertEqual( wc(), None )

	def testWindowStateCompatibility ( self ) :

		s = Gaffer.ScriptNode()
		c = GafferUI.CompoundEditor( s )

		sw = GafferUI.ScriptWindow.acquire( s )
		sw.setLayout( c )
		sw.setVisible( True )

		d = eval( c._serializeWindowState() )

		self.assertIsInstance( d, dict )
		self.assertIsInstance( d["fullScreen"], bool )
		self.assertIsInstance( d["maximized"], bool )
		self.assertIsInstance( d["screen"], int )
		self.assertIsInstance( d["bound"], imath.Box2f )

if __name__ == "__main__":
	unittest.main()
