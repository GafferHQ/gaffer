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

import IECore

import Gaffer
import GafferTest

class NodeAlgoTest( GafferTest.TestCase ) :

	def test( self ) :
		
		node = GafferTest.AddNode()
		
		self.assertEqual( node["op1"].getValue(), 0 )
		self.assertFalse( Gaffer.NodeAlgo.hasUserDefault( node["op1"] ) )
		Gaffer.Metadata.registerPlugValue( GafferTest.AddNode.staticTypeId(), "op1", "userDefault", IECore.IntData( 7 ) )
		self.assertTrue( Gaffer.NodeAlgo.hasUserDefault( node["op1"] ) )
		Gaffer.NodeAlgo.applyUserDefaults( node )
		self.assertEqual( node["op1"].getValue(), 7 )
		
		# even if it's registered, it doesn't get applied outside of the NodeMenu UI
		node2 = GafferTest.AddNode()
		self.assertEqual( node2["op1"].getValue(), 0 )
		Gaffer.NodeAlgo.applyUserDefaults( node2 )
		self.assertEqual( node2["op1"].getValue(), 7 )
		
		# they can also be applied to the plug directly
		node2["op1"].setValue( 1 )
		Gaffer.NodeAlgo.applyUserDefault( node2["op1"] )
		self.assertEqual( node2["op1"].getValue(), 7 )
		
		# the userDefault can be unregistered by overriding with None
		node3 = GafferTest.AddNode()
		Gaffer.Metadata.registerPlugValue( GafferTest.AddNode.staticTypeId(), "op1", "userDefault", None )
		self.assertFalse( Gaffer.NodeAlgo.hasUserDefault( node3["op1"] ) )
		Gaffer.NodeAlgo.applyUserDefaults( node3 )
		self.assertEqual( node3["op1"].getValue(), 0 )
	
	def testCompoundPlug( self ) :
		
		node = GafferTest.CompoundPlugNode()
		
		self.assertEqual( node["p"]["s"].getValue(), "" )
		Gaffer.Metadata.registerPlugValue( GafferTest.CompoundPlugNode.staticTypeId(), "p.s", "userDefault", IECore.StringData( "from the metadata" ) )
		Gaffer.NodeAlgo.applyUserDefaults( node )
		self.assertEqual( node["p"]["s"].getValue(), "from the metadata" )
		
		# override the metadata for this particular instance
		Gaffer.Metadata.registerPlugValue( node["p"]["s"], "userDefault", IECore.StringData( "i am special" ) )
		Gaffer.NodeAlgo.applyUserDefaults( node )
		self.assertEqual( node["p"]["s"].getValue(), "i am special" )
		
		# this node still gets the original userDefault
		node2 = GafferTest.CompoundPlugNode()
		Gaffer.NodeAlgo.applyUserDefaults( node2 )
		self.assertEqual( node2["p"]["s"].getValue(), "from the metadata" )
	
	def testSeveral( self ) :	
		
		node = GafferTest.AddNode()
		node2 = GafferTest.AddNode()
		
		self.assertEqual( node["op1"].getValue(), 0 )
		self.assertEqual( node2["op1"].getValue(), 0 )
		
		Gaffer.Metadata.registerPlugValue( GafferTest.AddNode.staticTypeId(), "op1", "userDefault", IECore.IntData( 1 ) )
		Gaffer.Metadata.registerPlugValue( node2["op1"], "userDefault", IECore.IntData( 2 ) )
		Gaffer.NodeAlgo.applyUserDefaults( [ node, node2 ] )
		
		self.assertEqual( node["op1"].getValue(), 1 )
		self.assertEqual( node2["op1"].getValue(), 2 )

if __name__ == "__main__":
	unittest.main()

