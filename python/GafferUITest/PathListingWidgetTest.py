##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import Gaffer
import GafferTest

import GafferUI
		
class PathListingWidgetTest( unittest.TestCase ) :

	def testExpandedPaths( self ) :
	
		d = {}
		for i in range( 0, 10 ) :
			dd = {}
			for j in range( 0, 10 ) :
				dd[str(j)] = j
			d[str(i)] = dd
		
		p = Gaffer.DictPath( d, "/" )
		
		w = GafferUI.PathListingWidget( p )
		self.assertEqual( len( w.getExpandedPaths() ), 0 )
				
		p1 = Gaffer.DictPath( d, "/1" )
		self.assertEqual( w.getPathExpanded( p1 ), False )
		w.setPathExpanded( p1, True )
		self.assertEqual( w.getPathExpanded( p1 ), True )		
		self.assertEqual( len( w.getExpandedPaths() ), 1 )
		self.assertEqual( str( list( w.getExpandedPaths() )[0] ), str( p1 ) )
		
		w.setPathExpanded( p1, False )
		self.assertEqual( w.getPathExpanded( p1 ), False )		
		self.assertEqual( len( w.getExpandedPaths() ), 0 )

		p2 = Gaffer.DictPath( d, "/2" )
		p3 = Gaffer.DictPath( d, "/3" )
		w.setExpandedPaths( [ p1, p2 ] )
		self.assertEqual( w.getPathExpanded( p1 ), True )
		self.assertEqual( w.getPathExpanded( p2 ), True )
		self.assertEqual( w.getPathExpanded( p3 ), False )
		self.assertEqual( w.getExpandedPaths(), [ p1, p2 ] )
		
		w.setPath( Gaffer.DictPath( {}, "/" ) )
		self.assertEqual( len( w.getExpandedPaths() ), 0 )
		
	def testExpansionSignalFrequency( self ) :
	
		d = {}
		for i in range( 0, 10 ) :
			dd = {}
			for j in range( 0, 10 ) :
				dd[str(j)] = j
			d[str(i)] = dd

		p = Gaffer.DictPath( d, "/" )
		w = GafferUI.PathListingWidget( p )
				
		c = GafferTest.CapturingSlot( w.expansionChangedSignal() )
		self.assertEqual( len( c ), 0 )
		
		w.setPathExpanded( Gaffer.DictPath( d, "/1" ), True )
		self.assertEqual( len( c ), 1 )
		w.setPathExpanded( Gaffer.DictPath( d, "/1" ), True )
		self.assertEqual( len( c ), 1 )
		
		w.setPathExpanded( Gaffer.DictPath( d, "/2" ), True )
		self.assertEqual( len( c ), 2 )
		
		e = w.getExpandedPaths()
		self.assertEqual( len( e ), 2 )

		w.setExpandedPaths( [] )
		self.assertEqual( len( c ), 3 )

		w.setExpandedPaths( e )
		self.assertEqual( len( c ), 4 )
		
	def testSelectionSignalFrequency( self ) :
	
		d = {
			"a" : {
				"e" : 10,
			},
			"b" : {
				"f" : "g",
			},
		}

		p = Gaffer.DictPath( d, "/" )
		w = GafferUI.PathListingWidget( p, allowMultipleSelection=True )
		
		c = GafferTest.CapturingSlot( w.selectionChangedSignal() )
		self.assertEqual( len( c ), 0 )

		w.setSelectedPaths( [ Gaffer.DictPath( d, "/a" ), Gaffer.DictPath( d, "/b" ) ] )
		self.assertEqual( set( [ str( p ) for p in w.getSelectedPaths() ] ), set( [ "/a", "/b" ] ) )
		
		self.assertEqual( len( c ), 1 )

	def testExpandedPathsWhenPathChanges( self ) :

		d = {
			"a" : {
				"e" : 10,
			},
			"b" : {
				"f" : "g",
			},
		}

		p = Gaffer.DictPath( d, "/" )
		p1 = Gaffer.DictPath( d, "/a" )
		w = GafferUI.PathListingWidget( p, displayMode = GafferUI.PathListingWidget.DisplayMode.Tree )

		self.assertEqual( w.getPathExpanded( p1 ), False )
		w.setPathExpanded( p1, True )
		self.assertEqual( w.getPathExpanded( p1 ), True )

		# fake a change to the path
		p.pathChangedSignal()( p )

		# because the PathListingWidget only updates on idle events, we have
		# to run the event loop to get it to process the path changed signal.
		def stop() :
			GafferUI.EventLoop.mainEventLoop().stop()
			return False

		GafferUI.EventLoop.addIdleCallback( stop )
		GafferUI.EventLoop.mainEventLoop().start()

		# once it has processed things, the expansion should be exactly as it was.
		self.assertEqual( w.getPathExpanded( p1 ), True )

	def testHeaderVisibility( self ) :
	
		with GafferUI.ListContainer() as c :
			w = GafferUI.PathListingWidget( Gaffer.DictPath( {}, "/" ) )

		self.assertTrue( w.getHeaderVisible() )
		
		w.setHeaderVisible( False )
		self.assertFalse( w.getHeaderVisible() )

		w.setHeaderVisible( True )
		self.assertTrue( w.getHeaderVisible() )

		c.setVisible( False )
		self.assertTrue( w.getHeaderVisible() )

		w.setHeaderVisible( False )
		self.assertFalse( w.getHeaderVisible() )

if __name__ == "__main__":
	unittest.main()
	
