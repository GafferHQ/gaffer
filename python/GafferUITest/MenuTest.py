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

		# We count calls to our dynamic sub menu generator under a variety of
		# sub menu and sub sub menu scenarios.

		callCounts = {
			"subMenuA" : 0,
			"subMenuB" : 0,
			"subMenuC" : 0,
			"subMenuD" : 0,
			"subMenuDSubMenu" : 0,
			"subMenuE" : 0,
			"subMenuESubMenu" : 0,
			"subMenuF" : 0,
			"subMenuFSubMenu" : 0,
			"subMenuI" : 0
		}

		def buildSubMenu( identifier, addChildSubMenu = False, childSubMenuHasShortCuts = True ) :
			callCounts[ identifier ] += 1
			smd = IECore.MenuDefinition()
			smd.append( "/%s_itemA" % identifier, {} )
			if addChildSubMenu :
				smd.append( "/%s_subMenu" % identifier, {
					"subMenu" : functools.partial( buildSubMenu, "%sSubMenu" % identifier, False ),
					"hasShortCuts" : childSubMenuHasShortCuts
				} )
			return smd

		md = IECore.MenuDefinition()
		md.append( "/staticItem1", {} )
		md.append( "/subMenuA", { "subMenu" : functools.partial( buildSubMenu, "subMenuA" ) } )
		md.append( "/subMenuB", { "subMenu" : functools.partial( buildSubMenu, "subMenuB" ), "hasShortCuts" : False } )
		md.append( "/subMenuC", { "subMenu" : functools.partial( buildSubMenu, "subMenuC" ), "hasShortCuts" : True } )
		# Sub sub menus under parents with/without short cuts
		md.append( "/subMenuD", { "subMenu" : functools.partial( buildSubMenu, "subMenuD", True ) } )
		md.append( "/subMenuE", { "subMenu" : functools.partial( buildSubMenu, "subMenuE", True, False ) } )
		md.append( "/subMenuF", { "subMenu" : functools.partial( buildSubMenu, "subMenuF", True ), "hasShortCuts" : False } )
		md.append( "/subMenuG/staticItemA", {} )
		# Indirect sub sub menu
		md.append( "/subMenuH/implicitSubMenu/dynamicSubMenu", { "subMenu" : functools.partial( buildSubMenu, "subMenuI" ), "hasShortCuts" : False } )

		# Full build

		m = GafferUI.Menu( md )
		m._buildFully()

		ma = m._qtWidget().actions()
		self.assertEqual( [ a.text() for a in ma ], [ "staticItem1", "subMenuA", "subMenuB", "subMenuC", "subMenuD", "subMenuE", "subMenuF", "subMenuG", "subMenuH" ] )
		self.assertEqual( [ a.text() for a in ma[1].menu().actions() ], [ "subMenuA_itemA" ] )
		self.assertEqual( [ a.text() for a in ma[2].menu().actions() ], [ "subMenuB_itemA" ] )
		self.assertEqual( [ a.text() for a in ma[3].menu().actions() ], [ "subMenuC_itemA" ] )
		self.assertEqual( [ a.text() for a in ma[4].menu().actions() ], [ "subMenuD_itemA", "subMenuD_subMenu" ] )
		self.assertEqual( [ a.text() for a in ma[4].menu().actions()[1].menu().actions() ], [ "subMenuDSubMenu_itemA" ] )
		self.assertEqual( [ a.text() for a in ma[5].menu().actions() ], [ "subMenuE_itemA", "subMenuE_subMenu" ] )
		self.assertEqual( [ a.text() for a in ma[5].menu().actions()[1].menu().actions() ], [ "subMenuESubMenu_itemA" ] )
		self.assertEqual( [ a.text() for a in ma[6].menu().actions() ], [ "subMenuF_itemA", "subMenuF_subMenu" ] )
		self.assertEqual( [ a.text() for a in ma[6].menu().actions()[1].menu().actions() ], [ "subMenuFSubMenu_itemA" ] )
		self.assertEqual( [ a.text() for a in ma[7].menu().actions() ], [ "staticItemA" ] )
		self.assertEqual( [ a.text() for a in ma[8].menu().actions() ], [ "implicitSubMenu" ] )
		self.assertEqual( [ a.text() for a in ma[8].menu().actions()[0].menu().actions() ], [ "dynamicSubMenu" ] )
		self.assertEqual( [ a.text() for a in ma[8].menu().actions()[0].menu().actions()[0].menu().actions() ], [ "subMenuI_itemA" ] )
		self.assertEqual( callCounts, { "subMenuA" : 1, "subMenuB" : 1, "subMenuC" : 1, "subMenuD" : 1, "subMenuDSubMenu" : 1, "subMenuE" : 1, "subMenuESubMenu" : 1, "subMenuF" : 1, "subMenuFSubMenu" : 1, "subMenuI" : 1 } )

		# For short cuts

		m = GafferUI.Menu( md )
		m._buildFully( forShortCuts = True )

		ma = m._qtWidget().actions()
		self.assertEqual( [ a.text() for a in ma ], [ "staticItem1", "subMenuA", "subMenuC", "subMenuD", "subMenuE", "subMenuG", "subMenuH" ] )
		self.assertEqual( [ a.text() for a in ma[1].menu().actions() ], [ "subMenuA_itemA" ] )
		self.assertEqual( [ a.text() for a in ma[2].menu().actions() ], [ "subMenuC_itemA" ] )
		self.assertEqual( [ a.text() for a in ma[3].menu().actions() ], [ "subMenuD_itemA", "subMenuD_subMenu" ] )
		self.assertEqual( [ a.text() for a in ma[3].menu().actions()[1].menu().actions() ], [ "subMenuDSubMenu_itemA" ] )
		self.assertEqual( [ a.text() for a in ma[4].menu().actions() ], [ "subMenuE_itemA" ] )
		self.assertEqual( [ a.text() for a in ma[5].menu().actions() ], [ "staticItemA" ] )
		self.assertEqual( [ a.text() for a in ma[6].menu().actions() ], [ "implicitSubMenu" ] )
		self.assertEqual( [ a.text() for a in ma[6].menu().actions()[0].menu().actions() ], [] )
		self.assertEqual( callCounts, { "subMenuA" : 2, "subMenuB" : 1, "subMenuC" : 2, "subMenuD" : 2, "subMenuDSubMenu" : 2, "subMenuE" : 2, "subMenuESubMenu" : 1, "subMenuF" : 1, "subMenuFSubMenu" : 1, "subMenuI" : 1 } )

if __name__ == "__main__":
	unittest.main()
