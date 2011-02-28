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

from PySide import QtGui
import IECore

import Gaffer
import GafferUI

class TestWidget( GafferUI.Widget ) :

	def __init__( self, s ) :
	
		GafferUI.Widget.__init__( self, QtGui.QLabel( s ) )
		
		self.s = s

class ListContainerTest( unittest.TestCase ) :

	def testConstruction( self ) :
	
		c = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		self.assertEqual( c.orientation(), GafferUI.ListContainer.Orientation.Vertical )
		self.assertEqual( len( c ), 0 )
		
		c = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
		self.assertEqual( c.orientation(), GafferUI.ListContainer.Orientation.Horizontal )
		self.assertEqual( len( c ), 0 )
	
	def testItems( self ) :
	
		c = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		self.assertEqual( len( c ), 0 )
		
		ca = TestWidget( "a" )
		cb = TestWidget( "b" )
		cc = TestWidget( "c" )
		self.assert_( ca.parent() is None )
		self.assert_( cb.parent() is None )
		self.assert_( cc.parent() is None )
		
		c.append( ca )
		self.assertEqual( len( c ), 1 )
		self.assertEqual( c[0], ca )
		self.assert_( ca.parent() is c )
	
		c.append( cb )
		self.assertEqual( len( c ), 2 )
		self.assertEqual( c[0], ca )
		self.assertEqual( c[1], cb )
		self.assert_( ca.parent() is c )
		self.assert_( cb.parent() is c )
	
		c.append( cc )
		self.assertEqual( len( c ), 3 )
		self.assertEqual( c[0], ca )
		self.assertEqual( c[1], cb )
		self.assertEqual( c[2], cc )
		self.assert_( ca.parent() is c )
		self.assert_( cb.parent() is c )
		self.assert_( cc.parent() is c )
		
		del c[0]
		self.assertEqual( len( c ), 2 )
		self.assert_( ca.parent() is None )
		self.assert_( cb.parent() is c )
		self.assert_( cc.parent() is c )
		self.assertEqual( c[0], cb )
		self.assertEqual( c[1], cc )
		
		c.remove( cc )
		self.assertEqual( len( c ), 1 )
		self.assert_( ca.parent() is None )
		self.assert_( cb.parent() is c )
		self.assert_( cc.parent() is None )
		self.assertEqual( c[0], cb )
		
	def testReparenting( self ) :
	
		c1 = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		self.assertEqual( len( c1 ), 0 )
		c2 = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		self.assertEqual( len( c2 ), 0 )
		
		ca = TestWidget( "a" )
		self.assert_( ca.parent() is None )
		
		c1.append( ca )
		self.assert_( ca.parent() is c1 )
		self.assertEqual( len( c1 ), 1 )
		self.assertEqual( len( c2 ), 0 )
		c2.append( ca )
		self.assert_( ca.parent() is c2 )
		self.assertEqual( len( c1 ), 0 )
		self.assertEqual( len( c2 ), 1 )
		
	def testSliceDel( self ) :
	
		c = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		
		ca = TestWidget( "a" )
		cb = TestWidget( "b" )
		cc = TestWidget( "c" )
		self.assert_( ca.parent() is None )
		self.assert_( cb.parent() is None )
		self.assert_( cc.parent() is None )
		
		c.append( ca )
		self.assert_( ca.parent() is c )
	
		c.append( cb )
		self.assert_( cb.parent() is c )
	
		c.append( cc )
		self.assert_( cc.parent() is c )
		
		self.assertEqual( len( c ), 3 )

		del c[0:2]
		self.assertEqual( len( c ), 1 )
		self.assert_( ca.parent() is None )
		self.assert_( cb.parent() is None )
		self.assert_( cc.parent() is c )
		
		
if __name__ == "__main__":
	unittest.main()
	
