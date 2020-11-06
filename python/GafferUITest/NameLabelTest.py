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

import Gaffer
import GafferUI
import GafferUITest

import six

class NameLabelTest( GafferUITest.TestCase ) :

	def test( self ) :

		n = Gaffer.Node()
		l = GafferUI.NameLabel( n )

		self.assertEqual( l.getText(), n.getName() )

		n.setName( "somethingElse" )
		self.assertEqual( l.getText(), "Something Else" )

	def testFormatter( self ) :

		n = Gaffer.Node()
		l = GafferUI.NameLabel( n )

		self.assertEqual( l.getText(), n.getName() )

		l.setFormatter( lambda x : ".".join( [ g.getName().upper() for g in x ] ) )
		n.setName( "somethingElse" )
		self.assertEqual( l.getText(), "SOMETHINGELSE" )

		l.setGraphComponent( None )
		self.assertEqual( l.getText(), "" )

	def testMultipleHierarchyComponents( self ) :

		n1 = Gaffer.Node( "n1" )
		n1["n2"] = Gaffer.Node()
		n1["n2"]["p"] = Gaffer.Plug()

		l = GafferUI.NameLabel( n1["n2"]["p"], numComponents=3 )

		self.assertEqual( l.getText(), "N1.N2.P" )

		n1.setName( "A" )
		self.assertEqual( l.getText(), "A.N2.P" )

		n1["n2"].setName( "B" )
		self.assertEqual( l.getText(), "A.B.P" )

		n1["B"]["p"].setName( "C" )
		self.assertEqual( l.getText(), "A.B.C" )

		l.setNumComponents( 1 )
		self.assertEqual( l.getText(), "C" )

		l.setNumComponents( 3 )
		self.assertEqual( l.getText(), "A.B.C" )

	def testParentChanges( self ) :

		n1 = Gaffer.Node( "n1" )
		n2 = Gaffer.Node( "n2" )
		p1 = Gaffer.Plug( "p1" )
		p2 = Gaffer.Plug( "p2" )

		l = GafferUI.NameLabel( p2, numComponents = 3 )
		self.assertEqual( l.getText(), "P2" )

		p1.addChild( p2 )
		self.assertEqual( l.getText(), "P1.P2" )

		p1.setName( "B" )
		self.assertEqual( l.getText(), "B.P2" )

		p2.setName( "C" )
		self.assertEqual( l.getText(), "B.C" )

		n2.addChild( p1 )
		self.assertEqual( l.getText(), "N2.B.C" )

		n1.addChild( n2 ) # should be irrelevant - we only want three levels
		self.assertEqual( l.getText(), "N2.B.C" )

		n2.setName( "A" )
		self.assertEqual( l.getText(), "A.B.C" )

		n1.addChild( p1 )
		self.assertEqual( l.getText(), "N1.B.C" )

		n1.addChild( p2 )
		self.assertEqual( l.getText(), "N1.C" )

		n1.setName( "AAA" )
		p2.setName( "BBB" )
		self.assertEqual( l.getText(), "AAA.BBB" )

	def testSetTextStopsTracking( self ) :

		n = Gaffer.Node( "n" )
		l = GafferUI.NameLabel( n )
		self.assertTrue( l.getText(), "N" )

		n.setName( "A" )
		self.assertTrue( l.getText(), "A" )

		l.setText( "woteva" )
		self.assertTrue( l.getText(), "woteva" )

		n.setName( "B" )
		self.assertTrue( l.getText(), "woteva" )

	def testMultipleComponents( self ) :

		n1 = Gaffer.Node( "n1" )
		n2 = Gaffer.Node( "n2" )

		l = GafferUI.NameLabel( { n1, n2 } )

		self.assertEqual( l.getGraphComponents(), { n1, n2 } )
		with six.assertRaisesRegex( self, RuntimeError, "getGraphComponent called with multiple GraphComponents" ) :
			l.getGraphComponent()

		self.assertTrue( l.getText(), "---" )

		n1["user"]["plug"] = Gaffer.Plug()
		n2["user"]["plug"] = Gaffer.Plug()

		l.setGraphComponents( set() )
		self.assertEqual( l.getText(), "" )

		l.setGraphComponents( { n1["user"]["plug"], n2["user"]["plug"] } )
		self.assertEqual( l.getText(), "Plug" )

		l.setNumComponents( 2 )
		self.assertTrue( l.getText(), "---" )

		l.setGraphComponent( None )
		self.assertEqual( l.getText(), "" )

if __name__ == "__main__":
	unittest.main()
