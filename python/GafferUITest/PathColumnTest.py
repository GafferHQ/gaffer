##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Limited. All rights reserved.
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

import imath

import IECore

import GafferUI
import GafferUITest

class PathColumnTest( GafferUITest.TestCase ) :

	def testCellDataDefaultConstructor( self ) :

		d = GafferUI.PathColumn.CellData()
		self.assertIsNone( d.value )
		self.assertIsNone( d.icon )
		self.assertIsNone( d.background )
		self.assertIsNone( d.toolTip )
		self.assertIsNone( d.sortValue )
		self.assertIsNone( d.foreground )

	def testCellDataKeywordConstructor( self ) :

		d = GafferUI.PathColumn.CellData(
			value = 10,
			icon = "test.png",
			background = imath.Color3f( 1 ),
			toolTip = "help!",
			sortValue = 1,
			foreground = imath.Color3f( 1 )
		)
		self.assertEqual( d.value, 10 )
		self.assertEqual( d.icon, "test.png" )
		self.assertEqual( d.background, imath.Color3f( 1 ) )
		self.assertEqual( d.toolTip, "help!" )
		self.assertEqual( d.sortValue, 1 )
		self.assertEqual( d.foreground, imath.Color3f( 1 ) )

	def testCellDataSetters( self ) :

		d = GafferUI.PathColumn.CellData()

		d.value = "test"
		self.assertEqual( d.value, "test" )

		d.icon = "test.png"
		self.assertEqual( d.icon, "test.png" )

		d.background = imath.Color4f( 1 )
		self.assertEqual( d.background, imath.Color4f( 1 ) )

		d.toolTip = "help!"
		self.assertEqual( d.toolTip, "help!" )

		d.sortValue = 2
		self.assertEqual( d.sortValue, 2 )

		d.foreground = imath.Color4f( 1 )
		self.assertEqual( d.foreground, imath.Color4f( 1 ) )

	def testSizeMode( self ) :

		p = GafferUI.PathColumn( sizeMode = GafferUI.PathColumn.SizeMode.Stretch )
		self.assertEqual( p.getSizeMode(), GafferUI.PathColumn.SizeMode.Stretch )

		p.setSizeMode( GafferUI.PathColumn.SizeMode.Interactive )
		self.assertEqual( p.getSizeMode(), GafferUI.PathColumn.SizeMode.Interactive )

	def testStandardPathColumnConstructors( self ) :

		c = GafferUI.StandardPathColumn( "label", "property" )
		self.assertEqual( c.property(), "property" )
		self.assertEqual( c.getSizeMode(), GafferUI.PathColumn.SizeMode.Default )
		self.assertEqual( c.headerData().value, "label" )

		c = GafferUI.StandardPathColumn(
			GafferUI.PathColumn.CellData( value = "label", toolTip = "help!" ),
			"property", GafferUI.PathColumn.SizeMode.Stretch
		)
		self.assertEqual( c.property(), "property" )
		self.assertEqual( c.getSizeMode(), GafferUI.PathColumn.SizeMode.Stretch )
		self.assertEqual( c.headerData().value, "label" )
		self.assertEqual( c.headerData().toolTip, "help!" )

	def testIconPathColumnConstructors( self ) :

		c = GafferUI.IconPathColumn( "label", "prefix", "property" )
		self.assertEqual( c.prefix(), "prefix" )
		self.assertEqual( c.property(), "property" )
		self.assertEqual( c.getSizeMode(), GafferUI.PathColumn.SizeMode.Default )
		self.assertEqual( c.headerData().value, "label" )

		c = GafferUI.IconPathColumn(
			GafferUI.PathColumn.CellData( value = "label", toolTip = "help!" ),
			"prefix", "property", GafferUI.PathColumn.SizeMode.Stretch
		)
		self.assertEqual( c.prefix(), "prefix" )
		self.assertEqual( c.property(), "property" )
		self.assertEqual( c.getSizeMode(), GafferUI.PathColumn.SizeMode.Stretch )
		self.assertEqual( c.headerData().value, "label" )
		self.assertEqual( c.headerData().toolTip, "help!" )

if __name__ == "__main__":
	unittest.main()
