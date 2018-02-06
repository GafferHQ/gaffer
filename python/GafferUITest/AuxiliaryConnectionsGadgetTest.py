##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

class AuxiliaryConnectionsGadgetTest( GafferUITest.TestCase ) :

	def testRemovedNodesDontHaveAuxiliaryConnections( self ) :

		s = Gaffer.ScriptNode()

		n1 = Gaffer.Node()
		n2 = Gaffer.Node()

		n1["o"] = Gaffer.Plug( direction=Gaffer.Plug.Direction.Out )
		n2["i"] = Gaffer.Plug()

		Gaffer.Metadata.registerPlugValue( n1["o"], "nodule:type", "" )
		Gaffer.Metadata.registerPlugValue( n2["i"], "nodule:type", "" )

		n2["i"].setInput( n1["o"] )

		s["n1"] = n1
		s["n2"] = n2

		g = GafferUI.GraphGadget( s )
		self.assertTrue( g.auxiliaryConnectionsGadget().hasConnection( n1, n2 ) )
		self.assertFalse( g.auxiliaryConnectionsGadget().hasConnection( n2, n1 ) )

		with Gaffer.UndoScope( s ) :
			del s["n1"]

		self.assertFalse( g.auxiliaryConnectionsGadget().hasConnection( n1, n2 ) )
		self.assertFalse( g.auxiliaryConnectionsGadget().hasConnection( n2, n1 ) )

		s.undo()
		self.assertTrue( g.auxiliaryConnectionsGadget().hasConnection( n1, n2 ) )
		self.assertFalse( g.auxiliaryConnectionsGadget().hasConnection( n2, n1 ) )

		del s["n2"]
		self.assertFalse( g.auxiliaryConnectionsGadget().hasConnection( n1, n2 ) )
		self.assertFalse( g.auxiliaryConnectionsGadget().hasConnection( n2, n1 ) )

	def testRemovePlugWithAuxiliaryInputConnection( self ) :

		script = Gaffer.ScriptNode()

		script["n1"] = Gaffer.Node()
		script["n2"] = Gaffer.Node()

		script["n1"]["o"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		script["n2"]["i"] = Gaffer.IntPlug()

		Gaffer.Metadata.registerPlugValue( script["n1"]["o"], "nodule:type", "" )
		Gaffer.Metadata.registerPlugValue( script["n2"]["i"], "nodule:type", "" )

		script["n2"]["i"].setInput( script["n1"]["o"] )

		g = GafferUI.GraphGadget( script )

		self.assertTrue( g.auxiliaryConnectionsGadget().hasConnection( script["n1"], script["n2"] ) )

		with Gaffer.UndoScope( script ) :
			del script["n2"]["i"]

		self.assertFalse( g.auxiliaryConnectionsGadget().hasConnection( script["n1"], script["n2"] ) )

		script.undo()

		self.assertTrue( g.auxiliaryConnectionsGadget().hasConnection( script["n1"], script["n2"] ) )

	def testRemovePlugWithAuxiliaryOutputConnection( self ) :

		script = Gaffer.ScriptNode()

		script["n1"] = Gaffer.Node()
		script["n2"] = Gaffer.Node()

		script["n1"]["o"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		script["n2"]["i"] = Gaffer.IntPlug()

		Gaffer.Metadata.registerPlugValue( script["n1"]["o"], "nodule:type", "" )
		Gaffer.Metadata.registerPlugValue( script["n2"]["i"], "nodule:type", "" )

		script["n2"]["i"].setInput( script["n1"]["o"] )

		g = GafferUI.GraphGadget( script )

		self.assertTrue( g.auxiliaryConnectionsGadget().hasConnection( script["n1"], script["n2"] ) )

		with Gaffer.UndoScope( script ) :
			del script["n1"]["o"]

		self.assertFalse( g.auxiliaryConnectionsGadget().hasConnection( script["n1"], script["n2"] ) )

		script.undo()

		self.assertTrue( g.auxiliaryConnectionsGadget().hasConnection( script["n1"], script["n2"] ) )

	def testMovePlugWithAuxiliaryInputConnection( self ) :

		script = Gaffer.ScriptNode()

		script["n1"] = Gaffer.Node()
		script["n1"]["p"] = Gaffer.Plug()
		Gaffer.Metadata.registerPlugValue( script["n1"]["p"], "nodule:type", "" )

		script["n2"] = Gaffer.Node()
		script["n2"]["p"] = Gaffer.Plug()
		Gaffer.Metadata.registerPlugValue( script["n2"]["p"], "nodule:type", "" )

		script["n2"]["p"].setInput( script["n1"]["p"] )

		g = GafferUI.GraphGadget( script )
		acg = g.auxiliaryConnectionsGadget()
		self.assertTrue( acg.hasConnection( script["n1"], script["n2"] ) )

		script["n3"] = Gaffer.Node()
		script["n3"]["p"] = script["n2"]["p"]

		self.assertFalse( acg.hasConnection( script["n1"], script["n2"] ) )
		self.assertTrue( acg.hasConnection( script["n1"], script["n3"] ) )

	def testMovePlugWithAuxiliaryInputConnectionOutsideGraph( self ) :

		script = Gaffer.ScriptNode()

		script["n1"] = Gaffer.Node()
		script["n1"]["p"] = Gaffer.Plug()
		Gaffer.Metadata.registerPlugValue( script["n1"]["p"], "nodule:type", "" )

		script["n2"] = Gaffer.Node()
		script["n2"]["p"] = Gaffer.Plug()
		script["n2"]["p"].setInput( script["n1"]["p"] )
		Gaffer.Metadata.registerPlugValue( script["n2"]["p"], "nodule:type", "" )

		g = GafferUI.GraphGadget( script )
		self.assertTrue( g.auxiliaryConnectionsGadget().hasConnection( script["n1"], script["n2"] ) )

		n3 = Gaffer.Node()
		n3["p"] = script["n2"]["p"]

		self.assertFalse( g.auxiliaryConnectionsGadget().hasConnection( script["n1"], script["n2"] ) )

	def testAddNoduleToPlugsWithAuxiliaryConnection( self ) :

		script = Gaffer.ScriptNode()

		script["n1"] = Gaffer.Node()
		script["n1"]["p"] = Gaffer.Plug()
		Gaffer.Metadata.registerPlugValue( script["n1"]["p"], "nodule:type", "" )

		script["n2"] = Gaffer.Node()
		script["n2"]["p"] = Gaffer.Plug()
		Gaffer.Metadata.registerPlugValue( script["n2"]["p"], "nodule:type", "" )

		script["n2"]["p"].setInput( script["n1"]["p"] )

		g = GafferUI.GraphGadget( script )
		acg = g.auxiliaryConnectionsGadget()

		self.assertTrue( acg.hasConnection( script["n1"], script["n2"] ) )

		Gaffer.Metadata.registerPlugValue( script["n1"]["p"], "nodule:type", "GafferUI::StandardNodule" )

		self.assertTrue( acg.hasConnection( script["n1"], script["n2"] ) )

		Gaffer.Metadata.registerPlugValue( script["n2"]["p"], "nodule:type", "GafferUI::StandardNodule" )

		self.assertFalse( acg.hasConnection( script["n1"], script["n2"] ) )

	def testIgnoreConnectionsFromSelf( self ) :

		script = Gaffer.ScriptNode()
		script["n"] = Gaffer.Node()
		script["n"]["p1"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		script["n"]["p2"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		script["n"]["p2"].setInput( script["n"]["p1"] )

		g = GafferUI.GraphGadget( script )
		self.assertFalse( g.auxiliaryConnectionsGadget().hasConnection( script["n"], script["n"] ) )

if __name__ == "__main__":
	unittest.main()
