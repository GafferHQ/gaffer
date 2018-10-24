##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

class SubGraphTest( GafferTest.TestCase ) :

	def testDerivingInPython( self ) :

		class MySubGraph( Gaffer.SubGraph ) :

			def __init__( self, name = "MySubGraph" ) :

				Gaffer.SubGraph.__init__( self, name )

		IECore.registerRunTimeTyped( MySubGraph )

		Gaffer.Metadata.registerNode(

			MySubGraph,

			"description",
			"""
			If you're retrieving this, the subclassing has worked.
			""",

		)

		n = MySubGraph()
		self.assertEqual(
			Gaffer.Metadata.value( n, "description" ),
			"If you're retrieving this, the subclassing has worked."
		)

	def testCorrespondingInputWithBoxIO( self ) :

		b = Gaffer.Box()

		b["a"] = GafferTest.AddNode()
		b["i"] = Gaffer.BoxIn()
		b["i"].setup( b["a"]["op1"] )
		b["a"]["op1"].setInput( b["i"].plug() )
		self.assertEqual( b["a"]["op1"].source(), b["i"].promotedPlug() )

		b["s"] = Gaffer.Switch()
		b["s"].setup( b["i"].plug() )
		b["s"]["in"][0].setInput( b["i"].plug() )
		b["s"]["in"][1].setInput( b["a"]["sum"] )

		Gaffer.PlugAlgo.promote( b["s"]["enabled"] )

		b["o"] = Gaffer.BoxOut()
		b["o"].setup( b["s"]["out"] )
		b["o"].plug().setInput( b["s"]["out"] )

		self.assertEqual( b.correspondingInput( b["o"].promotedPlug() ), b["i"].promotedPlug() )

	def testCorrespondingInputWithUnconnectedBoxOut( self ) :

		b = Gaffer.Box()
		b["o"] = Gaffer.BoxOut()
		b["o"].setup( Gaffer.IntPlug( "p" ) )

		self.assertIsNone( b.correspondingInput( b["out"] ) )

	def testCorrespondingInputWithUnconnectedInternalInput( self ) :

		b = Gaffer.Box()
		b["n"] = GafferTest.AddNode()

		b["o"] = Gaffer.BoxOut()
		b["o"].setup( b["n"]["sum"] )
		b["o"]["in"].setInput( b["n"]["sum"] )

		Gaffer.PlugAlgo.promote( b["n"]["enabled"] )

		self.assertIsNone( b.correspondingInput( b["out"] ) )

	def testCorrespondingInputWithBoxOutAndDots( self ) :

		b = Gaffer.Box()
		b["n"] = GafferTest.AddNode()

		b["i"] = Gaffer.BoxIn()
		b["i"].setup( b["n"]["sum"] )
		b["n"]["op1"].setInput( b["i"]["out"] )

		b["d1"] = Gaffer.Dot()
		b["d1"].setup( b["n"]["sum"] )
		b["d1"]["in"].setInput( b["i"]["out"] )

		b["d2"] = Gaffer.Dot()
		b["d2"].setup( b["n"]["sum"] )
		b["d2"]["in"].setInput( b["d1"]["out"] )

		b["o"] = Gaffer.BoxOut()
		b["o"].setup( b["n"]["sum"] )
		b["o"]["in"].setInput( b["n"]["sum"] )
		b["o"]["passThrough"].setInput( b["d2"]["out"] )

		self.assertEqual( b.correspondingInput( b["o"].promotedPlug() ), b["i"].promotedPlug() )

if __name__ == "__main__":
	unittest.main()
