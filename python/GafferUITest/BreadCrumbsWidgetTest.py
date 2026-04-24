##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
import GafferUI
import GafferUITest

class BreadCrumbsWidgetTest( GafferUITest.TestCase ) :

	def __assertWidgets( self, widgets, path ) :

		self.assertEqual( len( widgets ), 2 + len( path ) * 2 )

		self.assertIsInstance( widgets[0], GafferUI.Button )
		self.assertEqual( widgets[0].getText(), "" )
		self.assertIsInstance( widgets[1], GafferUI.Label )
		self.assertEqual( widgets[1].getText(), "/" )

		for i, p in enumerate( path ) :
			self.assertIsInstance( widgets[i * 2 + 2], GafferUI.Button )
			self.assertEqual( widgets[i * 2 + 2].getText(), p )
			self.assertIsInstance( widgets[i * 2 + 3], GafferUI.Label )
			self.assertEqual( widgets[i * 2 + 3].getText(), "/" )

	def testPathWidgets( self ) :

		path = Gaffer.DictPath( { "parent" : { "child": "contents" }, "brother" : "contents" }, "/" )

		crumbs = GafferUI.BreadCrumbsWidget( path )

		self.__assertWidgets( crumbs._BreadCrumbsWidget__pathButtonContainer, path )

		path.setFromString( "/parent" )
		self.__assertWidgets( crumbs._BreadCrumbsWidget__pathButtonContainer, path )

		path.append( "child" )
		self.__assertWidgets( crumbs._BreadCrumbsWidget__pathButtonContainer, path )

		path.setFromString( "/brother" )
		self.__assertWidgets( crumbs._BreadCrumbsWidget__pathButtonContainer, path )

	def testTextEntry( self ) :

		path = Gaffer.DictPath( { "parent" : { "child": { "grandChild" : "contents" } }, "brother" : "contents" }, "/" )

		crumbs = GafferUI.BreadCrumbsWidget( path )

		t = crumbs._BreadCrumbsWidget__textWidget
		self.assertEqual( t.getText(), "" )

		t.setText( "parent/" )
		self.assertEqual( t.getText(), "" )
		self.assertEqual( str( path ), "/parent" )

		t.setText( "child.grandChild/" )
		self.assertEqual( t.getText(), "" )
		self.assertEqual( str( path ), "/parent/child/grandChild" )

		t.setText( "brother" )
		self.assertEqual( t.getText(), "brother" )
		self.assertEqual( str( path ), "/parent/child/grandChild" )

		path.setFromString( "/" )
		t.setText( "brother/" )
		self.assertEqual( t.getText(), "" )
		self.assertEqual( str( path ), "/brother" )

	def testFilter( self ) :

		filter = Gaffer.MatchPatternPathFilter( [ "a*" ] )
		path = Gaffer.DictPath( { "abc" : "contents", "xyz" : "contents" }, "/", filter = filter )

		crumbs = GafferUI.BreadCrumbsWidget( path )

		t = crumbs._BreadCrumbsWidget__textWidget

		t.setText( "abc/" )
		self.assertEqual( t.getText(), "" )
		self.assertEqual( str( path ), "/abc" )

		path.setFromString( "/" )

		t.setText( "xyz/" )
		self.assertEqual( t.getText(), "xyz/" )
		self.assertEqual( str( path ), "/" )


if __name__ == "__main__" :
	unittest.main()
