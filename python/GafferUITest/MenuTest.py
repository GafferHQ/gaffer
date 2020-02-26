##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

import functools
import unittest
import weakref

import IECore

import Gaffer
import GafferUI
import GafferUITest

class MenuTest( GafferUITest.TestCase ) :

	def test( self ) :

		definition = IECore.MenuDefinition(

			[
				( "/apple/pear/banana", { } ),
				( "/apple/pear/divider", { "divider" : True } ),
				( "/apple/pear/submarine", { } ),
				( "/dog/inactive", { "active" : False } ),
			]

		)

		menu = GafferUI.Menu( definition )

	def testLifetime( self ) :

		def f() :

			pass

		definition = IECore.MenuDefinition(

			[
				( "/apple/pear/banana", { } ),
				( "/apple/pear/divider", { "divider" : True } ),
				( "/apple/pear/submarine", { "command" : f } ),
				( "/dog/inactive", { "active" : False } ),
			]

		)

		menu = GafferUI.Menu( definition )
		menu._buildFully()

		w = weakref.ref( menu )
		del menu

		wd = weakref.ref( definition )
		del definition

		wf = weakref.ref( f )
		del f

		self.assertEqual( w(), None )
		self.assertEqual( wd(), None )
		self.assertEqual( wf(), None )

	def testAutomaticParenting( self ) :

		with GafferUI.ListContainer() as l :

			md = IECore.MenuDefinition()
			md.append( "/Something", { "divider" : True } )

			m = GafferUI.Menu( md )
			b = GafferUI.MenuButton( menu=m )

		self.assertEqual( len( l ), 1 )
		self.failUnless( l[0] is b )
		self.failUnless( b.getMenu() is m )

	def testBuildFully( self ) :

		callCounts = {
			"subMenuA" : 0,
			"subMenuB" : 0,
			"subMenuC" : 0,
		}

		def buildSubMenu( identifier ) :
			callCounts[ identifier ] += 1
			smd = IECore.MenuDefinition()
			smd.append( "/%s_itemA" % identifier, {} )
			return smd

		md = IECore.MenuDefinition()
		md.append( "/staticItem1", {} )
		md.append( "/subMenuA", { "subMenu" : functools.partial( buildSubMenu, "subMenuA" ) } )
		md.append( "/subMenuB", { "subMenu" : functools.partial( buildSubMenu, "subMenuB" ), "hasShortCut" : False } )
		md.append( "/subMenuC", { "subMenu" : functools.partial( buildSubMenu, "subMenuC" ), "hasShortCut" : True } )
		md.append( "/subMenuD/staticItemA", {} )

		# Full build

		m = GafferUI.Menu( md )
		m._buildFully()

		ma = m._qtWidget().actions()
		self.assertEqual( [ a.text() for a in ma ], [ "staticItem1", "subMenuA", "subMenuB", "subMenuC", "subMenuD" ] )
		self.assertEqual( [ a.text() for a in ma[1].menu().actions() ], [ "subMenuA_itemA" ] )
		self.assertEqual( [ a.text() for a in ma[2].menu().actions() ], [ "subMenuB_itemA" ] )
		self.assertEqual( [ a.text() for a in ma[3].menu().actions() ], [ "subMenuC_itemA" ] )
		self.assertEqual( [ a.text() for a in ma[4].menu().actions() ], [ "staticItemA" ] )
		self.assertEqual( callCounts, { "subMenuA" : 1, "subMenuB" : 1, "subMenuC" : 1 } )

		# For short cuts

		m = GafferUI.Menu( md )
		m._buildFully( forShortCut = True )

		ma = m._qtWidget().actions()
		self.assertEqual( [ a.text() for a in ma ], [ "staticItem1", "subMenuA", "subMenuC", "subMenuD" ] )
		self.assertEqual( [ a.text() for a in ma[1].menu().actions() ], [ "subMenuA_itemA" ] )
		self.assertEqual( [ a.text() for a in ma[2].menu().actions() ], [ "subMenuC_itemA" ] )
		self.assertEqual( [ a.text() for a in ma[3].menu().actions() ], [ "staticItemA" ] )
		self.assertEqual( callCounts, { "subMenuA" : 2, "subMenuB" : 1, "subMenuC" : 2 } )

if __name__ == "__main__":
	unittest.main()
