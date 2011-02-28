##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

class SplitContainerTest( unittest.TestCase ) :

	def testChild( self ) :
	
		p = GafferUI.Splittable()
		self.assertEqual( p.getChild(), None )
		self.assertEqual( p.isSplit(), False )
		p.setChild( GafferUI.ScriptEditor( Gaffer.ScriptNode() ) )
		self.assertEqual( p.isSplit(), False )
		self.assert_( isinstance( p.getChild(), GafferUI.ScriptEditor ) )
		p.setChild( None )
		self.assertEqual( p.getChild(), None )
		
		s1 = GafferUI.ScriptEditor( Gaffer.ScriptNode() )
		s2 = GafferUI.ScriptEditor( Gaffer.ScriptNode() )
		self.assert_( s1.parent() is None )
		self.assert_( s2.parent() is None )
		
		self.assertEqual( p.isSplit(), False )
		p.setChild( s1 )
		self.assertEqual( p.isSplit(), False )
		self.assert_( p.getChild() is s1 )
		self.assert_( s1.parent() is p )
		self.assert_( s2.parent() is None )
		
		self.assertEqual( p.isSplit(), False )
		p.setChild( s2 )
		self.assertEqual( p.isSplit(), False )
		self.assert_( p.getChild() is s2 )
		self.assert_( s1.parent() is None )
		self.assert_( s2.parent() is p )

	def testSplit( self ) :
	
		p = GafferUI.Splittable()
		self.assertEqual( p.isSplit(), False )
		self.assertEqual( p.splitDirection(), p.SplitDirection.None )
		self.assertEqual( p.getChild(), None )
		
		p.split( p.SplitDirection.Vertical )
		self.assertEqual( p.isSplit(), True )
		self.assertEqual( p.splitDirection(), p.SplitDirection.Vertical )

		self.assertRaises( Exception, p.getChild )		
		self.assertRaises( Exception, p.split )
		self.assertRaises( Exception, p.setChild, GafferUI.ScriptEditor( Gaffer.ScriptNode() ) )
		
	def testSplitKeepingChild( self ) :
	
		p = GafferUI.Splittable()
		self.assertEqual( p.isSplit(), False )
		self.assertEqual( p.splitDirection(), p.SplitDirection.None )
		self.assertEqual( p.getChild(), None )
		
		s = GafferUI.ScriptEditor( Gaffer.ScriptNode() )
		p.setChild( s )
		self.assert_( p.getChild() is s )
		self.assert_( s.parent() is p )
		self.assertEqual( p.isSplit(), False )
		self.assertEqual( p.splitDirection(), p.SplitDirection.None )
	
		p.split( p.SplitDirection.Vertical, 1 )
		self.assertEqual( p.isSplit(), True )
		self.assert_( isinstance( p.subPanel( 0 ), GafferUI.Splittable ) )
		self.assert_( isinstance( p.subPanel( 1 ), GafferUI.Splittable ) )
		self.assertEqual( p.subPanel( 0 ).isSplit(), False )
		self.assertEqual( p.subPanel( 1 ).isSplit(), False )	
		self.assertEqual( p.subPanel( 0 ).getChild(), None )
		self.assertEqual( p.subPanel( 1 ).getChild(), s )
		self.assert_( s.parent() is p.subPanel( 1 ) )

	def testChildTransfer( self ) :
	
		p1 = GafferUI.Splittable()
		p2 = GafferUI.Splittable()
		
		s = GafferUI.ScriptEditor( Gaffer.ScriptNode() )
		
		self.assertEqual( p1.getChild(), None )
		self.assertEqual( p2.getChild(), None )
		
		p1.setChild( s )
		self.assertEqual( p1.getChild(), s )
		self.assertEqual( p2.getChild(), None )
		
		p2.setChild( s )
		self.assertEqual( p1.getChild(), None )
		self.assertEqual( p2.getChild(), s )	
		
	def testSplitAndRejoin( self ) :
	
		p = GafferUI.Splittable()
		self.assertEqual( p.isSplit(), False )
		self.assertEqual( p.splitDirection(), p.SplitDirection.None )
		self.assertEqual( p.getChild(), None )
				
		p.split( GafferUI.Splittable.SplitDirection.Horizontal, 1 )
		self.assertEqual( p.isSplit(), True )
		self.assertEqual( p.splitDirection(), p.SplitDirection.Horizontal )	
		
		p.join( 0 )
		self.assertEqual( p.isSplit(), False )
		self.assertEqual( p.splitDirection(), p.SplitDirection.None )
		self.assertEqual( p.getChild(), None )
	
	def testSplitAndRejoinWithChild( self ) :
	
		p = GafferUI.Splittable()
		s = GafferUI.ScriptEditor( Gaffer.ScriptNode() )
		p.setChild( s )
		
		p.split( p.SplitDirection.Vertical, 1 )
		self.assert_( p.isSplit() )
		self.assert_( s.parent().parent() is p )
		
		p.join( 1 )
		self.assertEqual( p.isSplit(), False )
		self.assert_( p.getChild() is s )
		self.assert_( s.parent() is p )
	
	def testSplitAndRejoinWithSplit( self ) :
	
		p = GafferUI.Splittable()
		p.split( p.SplitDirection.Vertical )
		self.assert_( p.isSplit(), True )
		
		pl = p.subPanel( 0 )
		pl.split( p.SplitDirection.Horizontal )
		self.assert_( p.isSplit(), True )
		
		p.join( 0 )
		self.assert_( p.isSplit(), True )
		self.assert_( p.splitDirection(), p.SplitDirection.Horizontal )
	
if __name__ == "__main__":
	unittest.main()
	
