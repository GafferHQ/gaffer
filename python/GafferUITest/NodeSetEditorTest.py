##########################################################################
#
#  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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

import Gaffer
import GafferUI
import GafferUITest

class NodeSetEditorTest( GafferUITest.TestCase ) :

	def testDefaultsToNodeSelection( self ) :

		s = Gaffer.ScriptNode()

		ne = GafferUI.NodeEditor( s )
		self.assertTrue( ne.getNodeSet().isSame( s.selection() ) )

	def testSetNodeSet( self ) :

		s = Gaffer.ScriptNode()

		n = Gaffer.StandardSet()
		n2 = Gaffer.StandardSet()

		ne = GafferUI.NodeEditor( s )
		ne.setNodeSet( n )
		self.assertTrue( ne.getNodeSet().isSame( n ) )
		ne.setNodeSet( n2 )
		self.assertTrue( ne.getNodeSet().isSame( n2 ) )

	def testSignals( self ) :

		s = Gaffer.ScriptNode()

		n1 = Gaffer.StandardSet()
		n2 = Gaffer.StandardSet()

		ne1 = GafferUI.NodeEditor( s )
		ne2 = GafferUI.NodeEditor( s )

		weakne1 = weakref.ref( ne1 )

		signalData = {
			'ne1nodeSetMirror' : None,
			'ne2nodeSetMirror' : None,
		}

		def nodeSetChangedCallback( editor ) :
			d = editor.getNodeSet()
			if editor is weakne1() :
				signalData['ne1nodeSetMirror'] = d
			else :
				signalData['ne2nodeSetMirror'] = d

		c1 = ne1.nodeSetChangedSignal().connect( nodeSetChangedCallback )

		c4 = ne2.nodeSetChangedSignal().connect( nodeSetChangedCallback )

		ne1.setNodeSet( n1 )
		ne2.setNodeSet( n2 )

		self.assertEqual( ne1.getNodeSet(), signalData['ne1nodeSetMirror'] )
		self.assertEqual( ne2.getNodeSet(), signalData['ne2nodeSetMirror'] )

		ne1.setNodeSet( n2 )
		self.assertEqual( ne1.getNodeSet(), signalData['ne1nodeSetMirror'] )
		self.assertEqual( ne2.getNodeSet(), signalData['ne2nodeSetMirror'] )

		ne2.setNodeSet( n1 )
		self.assertEqual( ne1.getNodeSet(), signalData['ne1nodeSetMirror'] )
		self.assertEqual( ne2.getNodeSet(), signalData['ne2nodeSetMirror'] )

if __name__ == "__main__":
	unittest.main()
