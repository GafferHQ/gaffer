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

from __future__ import with_statement

import unittest
import weakref

import IECore

import Gaffer
import GafferUI
import GafferTest
import GafferUITest

class StandardGraphLayoutTest( GafferUITest.TestCase ) :

	def testConnectNode( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["add1"] = GafferTest.AddNode()
		s["add2"] = GafferTest.AddNode()
		
		ng = GafferUI.NodeGraph( s )
		g = ng.graphGadget()
		
		# check we can connect to a top level plug
		g.getLayout().connectNode( g, s["add2"], Gaffer.StandardSet( [ s["add1"] ] ) )
		self.assertTrue( s["add2"]["op1"].getInput().isSame( s["add1"]["sum"] ) )
	
		# check we can connect to a nested plug, but only provided it is represented
		# in the node graph by a nodule for that exact plug.
	
		s["compound"] = GafferTest.CompoundPlugNode()
		g.getLayout().connectNode( g, s["compound"], Gaffer.StandardSet( [ s["add2"] ] ) )
		self.assertEqual( s["compound"]["p"]["f"].getInput(), None )
		
		GafferUI.Nodule.registerNodule( GafferTest.CompoundPlugNode.staticTypeId(), "p", GafferUI.CompoundNodule )
		
		s["compound2"] = GafferTest.CompoundPlugNode()
		g.getLayout().connectNode( g, s["compound2"], Gaffer.StandardSet( [ s["add2"] ] ) )
		self.assertTrue( s["compound2"]["p"]["f"].getInput().isSame( s["add2"]["sum"] ) )
		
		# check we can connect from a nested plug, but only provided it is represented
		# in the node graph by a nodule for that exact plug.
		
		s["add3"] = GafferTest.AddNode()
		
		g.getLayout().connectNode( g, s["add3"], Gaffer.StandardSet( [ s["compound2"] ] ) )
		self.assertEqual( s["add3"]["op1"].getInput(), None )
		
		GafferUI.Nodule.registerNodule( GafferTest.CompoundPlugNode.staticTypeId(), "o", GafferUI.CompoundNodule )
		
		s["compound3"] = GafferTest.CompoundPlugNode()
		
		g.getLayout().connectNode( g, s["add3"], Gaffer.StandardSet( [ s["compound3"] ] ) )
		self.assertTrue( s["add3"]["op1"].getInput().isSame( s["compound3"]["o"]["f"] ) )
	
	def testConnectNodes( self ) :
	
		s = Gaffer.ScriptNode()

		s["add1"] = GafferTest.AddNode()
		s["add2"] = GafferTest.AddNode()
		s["add3"] = GafferTest.AddNode()
		
		s["add3"]["op1"].setInput( s["add2"]["sum"] )
		
		g = GafferUI.GraphGadget( s )
		g.getLayout().connectNodes( g, Gaffer.StandardSet( [ s["add3"], s["add2"] ] ), Gaffer.StandardSet( [ s["add1"] ] ) )
		
		self.assertTrue( s["add2"]["op1"].getInput().isSame( s["add1"]["sum"] ) )
	
	def testConnectNodeInStream( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["add1"] = GafferTest.AddNode()
		s["add2"] = GafferTest.AddNode()
		s["add3"] = GafferTest.AddNode()
		
		s["add2"]["op1"].setInput( s["add1"]["sum"] )
		
		g = GafferUI.GraphGadget( s )
		g.getLayout().connectNode( g, s["add3"], Gaffer.StandardSet( [ s["add1"] ] ) )
		
		self.assertTrue( s["add3"]["op1"].getInput().isSame( s["add1"]["sum"] ) )
		self.assertTrue( s["add2"]["op1"].getInput().isSame( s["add3"]["sum"] ) )
	
	def testConnectNodeInStreamWithMultipleOutputs( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["add1"] = GafferTest.AddNode()
		s["add2"] = GafferTest.AddNode()
		s["add3"] = GafferTest.AddNode()
		s["add4"] = GafferTest.AddNode()
		
		s["add2"]["op1"].setInput( s["add1"]["sum"] )
		s["add3"]["op1"].setInput( s["add1"]["sum"] )
		
		g = GafferUI.GraphGadget( s )
		g.getLayout().connectNode( g, s["add4"], Gaffer.StandardSet( [ s["add1"] ] ) )
		
		self.assertTrue( s["add2"]["op1"].getInput().isSame( s["add4"]["sum"] ) )
		self.assertTrue( s["add3"]["op1"].getInput().isSame( s["add4"]["sum"] ) )
		
	def testConnectNodeToMultipleInputsDoesntInsertInStream( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["add1"] = GafferTest.AddNode()
		s["add2"] = GafferTest.AddNode()
		s["add3"] = GafferTest.AddNode()
		s["add4"] = GafferTest.AddNode()
		
		s["add3"]["op1"].setInput( s["add1"]["sum"] )
		s["add3"]["op2"].setInput( s["add2"]["sum"] )
		
		g = GafferUI.GraphGadget( s )
		g.getLayout().connectNode( g, s["add4"], Gaffer.StandardSet( [ s["add1"], s["add2"] ] ) )
		
		self.assertTrue( s["add4"]["op1"].getInput().isSame( s["add1"]["sum"] ) )
		self.assertTrue( s["add4"]["op2"].getInput().isSame( s["add2"]["sum"] ) )

		self.assertEqual( len( s["add4"]["sum"].outputs() ), 0 )

if __name__ == "__main__":
	unittest.main()
	
