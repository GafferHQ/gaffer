##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

class GadgetTest( unittest.TestCase ) :

	def testTransform( self ) :
	
		g = GafferUI.TextGadget( "hello" )
		self.assertEqual( g.getTransform(), IECore.M44f() )
		
		t = IECore.M44f.createScaled( IECore.V3f( 2 ) ) 
		g.setTransform( t )
		self.assertEqual( g.getTransform(), t )

		c1 = GafferUI.LinearContainer()
		c1.addChild( g )
	
		c2 = GafferUI.LinearContainer()
		c2.addChild( c1 )
		t2 = IECore.M44f.createTranslated( IECore.V3f( 1, 2, 3 ) )
		c2.setTransform( t2 )
		
		self.assertEqual( g.fullTransform(), t * t2 )
		self.assertEqual( g.fullTransform( c1 ), t )
	
	def testToolTip( self ) :
	
		g = GafferUI.TextGadget( "hello" )
		
		self.assertEqual( g.getToolTip(), "" )
		g.setToolTip( "hi" )
		self.assertEqual( g.getToolTip(), "hi" )
	
	def testDerivationInPython( self ) :

		class MyGadget( GafferUI.Gadget ) :
		
			def __init__( self ) :
			
				GafferUI.Gadget.__init__( self )
				
			def bound( self ) :
			
				return IECore.Box3f( IECore.V3f( -20, 10, 2 ), IECore.V3f( 10, 15, 5 ) )
				
		mg = MyGadget()
		
		# we can't call the methods of the gadget directly in python to test the
		# bindings, as that doesn't prove anything (we're no exercising the virtual
		# method override code in the wrapper). instead cause c++ to call through
		# for us by adding our gadget to a parent and making calls to the parent.
		
		c = GafferUI.IndividualContainer()
		c.addChild( mg )
		
		self.assertEqual( c.bound().size(), mg.bound().size() )
	
if __name__ == "__main__":
	unittest.main()
	
