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

import Gaffer
import GafferUI
import GafferUITest

class ReferenceUITest( GafferUITest.TestCase ) :

	def testHiddenNodules( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()
		s["b"]["n"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		Gaffer.Metadata.registerValue( s["b"]["n"]["p"], "nodule:type", "" )

		p = Gaffer.PlugAlgo.promote( s["b"]["n"]["p"] )
		p.setName( "p" )

		g = GafferUI.GraphGadget( s )
		self.assertTrue( g.nodeGadget( s["b"] ).nodule( s["b"]["p"] ) is None )

		s["b"].exportForReference( self.temporaryDirectory() / "test.grf" )
		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() / "test.grf" )

		self.assertTrue( g.nodeGadget( s["r"] ).nodule( s["r"]["p"] ) is None )

	def testReadOnly( self ):

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["a1"] = Gaffer.Box()
		s["b"]["a1"]["p1"] = Gaffer.IntPlug( "boxPlug", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		Gaffer.PlugAlgo.promote( s["b"]["a1"]["p1"] )
		s["b"].exportForReference( self.temporaryDirectory() / "test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() / "test.grf" )

		self.assertTrue( Gaffer.MetadataAlgo.getChildNodesAreReadOnly( s["r"] ) )
		self.assertFalse( Gaffer.MetadataAlgo.readOnly( s["r"] ) )
		self.assertFalse( Gaffer.MetadataAlgo.readOnly( s["r"]["p1"] ) )
		self.assertTrue( Gaffer.MetadataAlgo.readOnly( s["r"]["a1"] ) )
		self.assertTrue( Gaffer.MetadataAlgo.readOnly( s["r"]["a1"]["p1"] ) )

		s.execute( s.serialise( parent = s["r"], filter = Gaffer.StandardSet( [ s["r"]["a1"] ] ) ) )

		self.assertTrue( "a1" in s )

		self.assertFalse( Gaffer.MetadataAlgo.readOnly( s["a1"] ) )
		self.assertFalse( Gaffer.MetadataAlgo.readOnly( s["a1"]["p1"] ) )


if __name__ == "__main__":
	unittest.main()
