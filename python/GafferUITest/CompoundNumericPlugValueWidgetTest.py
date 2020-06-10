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

import Gaffer
import GafferTest
import GafferUI

class CompoundNumericPlugValueWidgetTest( unittest.TestCase ) :

	def test( self ) :

		n = Gaffer.Node()
		n["v1"]= Gaffer.V3fPlug()
		n["v2"]= Gaffer.V3fPlug()

		w = GafferUI.CompoundNumericPlugValueWidget( n["v1"] )
		self.assertTrue( w.getPlug().isSame( n["v1"] ) )
		self.assertTrue( w._row()[0].getPlug().isSame( n["v1"][0] ) )
		self.assertTrue( w._row()[1].getPlug().isSame( n["v1"][1] ) )
		self.assertTrue( w._row()[2].getPlug().isSame( n["v1"][2] ) )

		w.setPlug( n["v2"] )
		self.assertTrue( w.getPlug().isSame( n["v2"] ) )
		self.assertTrue( w._row()[0].getPlug().isSame( n["v2"][0] ) )
		self.assertTrue( w._row()[1].getPlug().isSame( n["v2"][1] ) )
		self.assertTrue( w._row()[2].getPlug().isSame( n["v2"][2] ) )

	def testChildPlugValueWidget( self ) :

		n = Gaffer.Node()
		n["v1"] = Gaffer.V3fPlug()
		n["v2"] = Gaffer.V3fPlug()

		w = GafferUI.CompoundNumericPlugValueWidget( n["v1"] )

		for i in range( 0, 3 ) :
			self.assertTrue( w.childPlugValueWidget( n["v1"][i] ).getPlug().isSame( n["v1"][i] ) )
			self.assertTrue( w.childPlugValueWidget( n["v2"][i] ) is None )

	def testVisibleDimensionsMetadata( self ) :

		n = Gaffer.Node()
		n["v"] = Gaffer.V3fPlug()
		Gaffer.Metadata.registerValue( n["v"], "ui:visibleDimensions", 2 )

		w = GafferUI.CompoundNumericPlugValueWidget( n["v"] )

		self.assertTrue( w.childPlugValueWidget( n["v"][0] ).getVisible() )
		self.assertTrue( w.childPlugValueWidget( n["v"][1] ).getVisible() )
		self.assertFalse( w.childPlugValueWidget( n["v"][2] ).getVisible() )

	def testSetGetPlugs( self ) :

		n = Gaffer.Node()
		n["user"]["v1"] = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["user"]["v2"] = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		w = GafferUI.CompoundNumericPlugValueWidget( n["user"]["v1"] )
		self.assertEqual( w.getPlug(), n["user"]["v1"] )
		self.assertEqual( w.getPlugs(), { n["user"]["v1"] } )

		w.setPlug( n["user"]["v2"] )
		self.assertEqual( w.getPlug(), n["user"]["v2"] )
		self.assertEqual( w.getPlugs(), { n["user"]["v2"] } )

		w.setPlugs( { n["user"]["v1"] } )
		self.assertEqual( w.getPlug(), n["user"]["v1"] )
		self.assertEqual( w.getPlugs(), { n["user"]["v1"] } )

		for childPlug in n["user"]["v1"] :
			self.assertEqual(
				w.childPlugValueWidget( childPlug ).getPlug(),
				childPlug,
			)

	def testChangePlugDimensions( self ) :

		n = Gaffer.Node()
		n["user"]["p1"] = Gaffer.V2iPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["user"]["p2"] = Gaffer.V3iPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		w = GafferUI.CompoundNumericPlugValueWidget( n["user"]["p1"] )
		self.assertEqual( len( w._row() ), 2 )
		for childPlug in Gaffer.Plug.Range( w.getPlug() ) :
			self.assertEqual( w.childPlugValueWidget( childPlug ).getPlug(), childPlug )

		w.setPlug( n["user"]["p2"] )
		self.assertEqual( len( w._row() ), 3 )
		for childPlug in Gaffer.Plug.Range( w.getPlug() ) :
			self.assertEqual( w.childPlugValueWidget( childPlug ).getPlug(), childPlug )

		w.setPlug( n["user"]["p1"] )
		self.assertEqual( len( w._row() ), 2 )
		for childPlug in Gaffer.Plug.Range( w.getPlug() ) :
			self.assertEqual( w.childPlugValueWidget( childPlug ).getPlug(), childPlug )

	def testChildPlugValueWidgetForMultiplePlugs( self ) :

		n = Gaffer.Node()
		n["user"]["p1"] = Gaffer.V3iPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["user"]["p2"] = Gaffer.V3iPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		w = GafferUI.CompoundNumericPlugValueWidget( n["user"].children() )

		for plug in n["user"].children() :
			for childPlug in plug :
				self.assertIn( childPlug, w.childPlugValueWidget( childPlug ).getPlugs() )

	def testHighlighting( self ) :

		n = Gaffer.Node()
		n["user"]["p1"] = Gaffer.V3iPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		w = GafferUI.CompoundNumericPlugValueWidget( n["user"]["p1"] )

		w.setHighlighted( True )
		for childPlug in w.getPlug() :
			self.assertTrue( w.childPlugValueWidget( childPlug ).getHighlighted() )

		w.setHighlighted( False )
		for childPlug in w.getPlug() :
			self.assertFalse( w.childPlugValueWidget( childPlug ).getHighlighted() )

if __name__ == "__main__":
	unittest.main()
