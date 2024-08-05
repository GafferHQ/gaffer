##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

class NameWidgetTest( GafferUITest.TestCase ) :

	def test( self ) :

		n = Gaffer.Node()
		w = GafferUI.NameWidget( n )

		self.assertEqual( w.getText(), n.getName() )

		n.setName( "somethingElse" )
		self.assertEqual( w.getText(), "somethingElse" )

	def testConstructWithoutGraphComponent( self ) :

		w = GafferUI.NameWidget( None )
		self.assertEqual( w.getText(), "" )

		n = Gaffer.Node()
		w.setGraphComponent( n )

		self.assertEqual( w.getText(), n.getName() )

	def testSetGraphComponentToNone( self ) :

		n = Gaffer.Node()
		w = GafferUI.NameWidget( n )
		self.assertEqual( w.getText(), n.getName() )

		w.setGraphComponent( None )
		self.assertEqual( w.getText(), "" )
		self.assertTrue( w.getGraphComponent() is None )

	def testEditability( self ) :

		node = Gaffer.Node()
		node["user"]["p1"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		node["user"]["p2"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		nodeNameWidget = GafferUI.NameWidget( node )
		plugNameWidget = GafferUI.NameWidget( node["user"]["p1"] )

		self.assertTrue( nodeNameWidget.getEditable() )
		self.assertTrue( plugNameWidget.getEditable() )

		Gaffer.Metadata.registerValue( node, "readOnly", True )

		self.assertFalse( nodeNameWidget.getEditable() )
		self.assertFalse( plugNameWidget.getEditable() )

		Gaffer.Metadata.registerValue( node, "readOnly", False )

		self.assertTrue( nodeNameWidget.getEditable() )
		self.assertTrue( plugNameWidget.getEditable() )

		Gaffer.Metadata.registerValue( node["user"]["p2"], "readOnly", True )

		self.assertTrue( nodeNameWidget.getEditable() )
		self.assertTrue( plugNameWidget.getEditable() )

		Gaffer.Metadata.registerValue( node["user"]["p1"], "readOnly", True )

		self.assertTrue( nodeNameWidget.getEditable() )
		self.assertFalse( plugNameWidget.getEditable() )

		nodeNameWidget.setGraphComponent( None )
		self.assertFalse( nodeNameWidget.getEditable() )

		plugNameWidget.setGraphComponent( None )
		self.assertFalse( plugNameWidget.getEditable() )

		noneWidget = GafferUI.NameWidget( graphComponent = None )
		self.assertFalse( noneWidget.getEditable() )

if __name__ == "__main__":
	unittest.main()
