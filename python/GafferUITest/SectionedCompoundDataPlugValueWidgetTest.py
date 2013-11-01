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

import IECore

import Gaffer
import GafferUI
import GafferUITest

class SectionedCompoundDataPlugValueWidgetTest( GafferUITest.TestCase ) :

	def test( self ) :
	
		class SectionedTestNode( Gaffer.Node ) :
		
			def __init__( self, name = "SectionedTestNode" ) :
			
				Gaffer.Node.__init__( self, name )
			
				self["p"] = Gaffer.CompoundDataPlug()
				self["p"].addMember( "test1", IECore.IntData( 10 ), "test1", Gaffer.Plug.Flags.Default )
				self["p"].addOptionalMember( "test2", IECore.IntData( 20 ), "test2", Gaffer.Plug.Flags.Default )
	
		IECore.registerRunTimeTyped( SectionedTestNode )
		
		GafferUI.PlugValueWidget.registerCreator(
	
			SectionedTestNode.staticTypeId(),
			"p",
			GafferUI.SectionedCompoundDataPlugValueWidget,
			sections = (
	
				{
					"label" : "One",
					"namesAndLabels" : (
						( "test1", "Test" ),
					),
				},
	
				{
					"label" : "One",
					"namesAndLabels" : (
						( "test2", "Test" ),
					),
				},
	
			),	

		)

		node = SectionedTestNode()
		nodeUI = GafferUI.StandardNodeUI( node )
		
		self.assertTrue( isinstance( nodeUI.plugValueWidget( node["p"] ), GafferUI.SectionedCompoundDataPlugValueWidget ) )
		
		for plugName in [ 
			"p",
			"p.test1",
			"p.test2",
			"p.test1.value",
			"p.test2.enabled",
			"p.test2.value",
		] :
			plug = node.descendant( plugName )
			self.assertTrue( nodeUI.plugValueWidget( plug, lazy=False ).getPlug().isSame( plug ) )
		
		for plugName in [ 
			"p.test1.name",
			"p.test2.name",
		] :
			# there aren't ui elements for the name plug
			plug = node.descendant( plugName )
			self.assertTrue( nodeUI.plugValueWidget( plug, lazy=False ) is None )
		
		nodeUI.setReadOnly( True )
		
		for plugName in [ 
			"p",
			"p.test1",
			"p.test2",
			"p.test1.value",
			"p.test2.enabled",
			"p.test2.value",
		] :
			plug = node.descendant( plugName )
			self.assertTrue( nodeUI.plugValueWidget( plug, lazy=True ).getReadOnly() )

		nodeUI.setReadOnly( False )

		for plugName in [ 
			"p",
			"p.test1",
			"p.test2",
			"p.test1.value",
			"p.test2.enabled",
			"p.test2.value",
		] :
			plug = node.descendant( plugName )
			self.assertFalse( nodeUI.plugValueWidget( plug, lazy=True ).getReadOnly() )
		
if __name__ == "__main__":
	unittest.main()
