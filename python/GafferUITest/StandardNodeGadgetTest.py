##########################################################################
#  
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import GafferUI
import GafferUITest

class StandardNodeGadgetTest( GafferUITest.TestCase ) :

	def testContents( self ) :
	
		n = Gaffer.Node()
		
		g = GafferUI.StandardNodeGadget( n )
		
		self.failUnless( isinstance( g.getContents(), GafferUI.NameGadget ) )
		self.assertEqual( g.getContents().getText(), n.getName() )
		
		t = GafferUI.TextGadget( "I'll choose my own label thanks" )
		g.setContents( t )
		
		self.failUnless( g.getContents().isSame( t ) )
	
	def testNestedNodules( self ) :
	
		class DeeplyNestedNode( Gaffer.Node ) :
		
			def __init__( self, name = "DeeplyNestedNode" ) :
			
				Gaffer.Node.__init__( self, name )
				
				self["c1"] = Gaffer.CompoundPlug()
				self["c1"]["i1"] = Gaffer.IntPlug()
				self["c1"]["c2"] = Gaffer.CompoundPlug()
				self["c1"]["c2"]["i2"] = Gaffer.IntPlug()
				self["c1"]["c2"]["c3"] = Gaffer.CompoundPlug()
				self["c1"]["c2"]["c3"]["i3"] = Gaffer.IntPlug()
				
		IECore.registerRunTimeTyped( DeeplyNestedNode )
				
		n = DeeplyNestedNode()
		
		def noduleCreator( plug ) :
			if isinstance( plug, Gaffer.CompoundPlug ) :
				return GafferUI.CompoundNodule( plug )
			else :
				return GafferUI.StandardNodule( plug )
			
		GafferUI.Nodule.registerNodule( DeeplyNestedNode.staticTypeId(), ".*", noduleCreator )
		
		g = GafferUI.StandardNodeGadget( n )
		
		self.assertTrue( g.nodule( n["c1"] ).plug().isSame( n["c1"] ) )
		self.assertTrue( g.nodule( n["c1"]["i1"] ).plug().isSame( n["c1"]["i1"] ) )
		self.assertTrue( g.nodule( n["c1"]["c2"] ).plug().isSame( n["c1"]["c2"] ) )
		self.assertTrue( g.nodule( n["c1"]["c2"]["i2"] ).plug().isSame( n["c1"]["c2"]["i2"] ) )
		self.assertTrue( g.nodule( n["c1"]["c2"]["c3"] ).plug().isSame( n["c1"]["c2"]["c3"] ) )
		self.assertTrue( g.nodule( n["c1"]["c2"]["c3"]["i3"] ).plug().isSame( n["c1"]["c2"]["c3"]["i3"] ) )
		
			
if __name__ == "__main__":
	unittest.main()
	
