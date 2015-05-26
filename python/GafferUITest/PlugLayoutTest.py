##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

class PlugLayoutTest( GafferUITest.TestCase ) :

	def testRenamingPlugs( self ) :

		n = Gaffer.Node()
		n["a"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		ui = GafferUI.PlugLayout( n )

		w = ui.plugValueWidget( n["a"], lazy=False )
		self.assertTrue( w is not None )
		self.assertTrue( w.getPlug().isSame( n["a"] ) )

		n["a"].setName( "b" )

		w2 = ui.plugValueWidget( n["b"], lazy=False )
		self.assertTrue( w2 is not None )
		self.assertTrue( w2 is w )
		self.assertTrue( w2.getPlug().isSame( n["b"] ) )

	def testLayoutOrder( self ) :

		n = Gaffer.Node()
		n["user"]["a"] = Gaffer.IntPlug()
		n["user"]["b"] = Gaffer.IntPlug()
		n["user"]["c"] = Gaffer.IntPlug()

		self.assertEqual(
			GafferUI.PlugLayout.layoutOrder( n["user"] ),
			[ n["user"]["a"], n["user"]["b"], n["user"]["c"] ],
		)

		Gaffer.Metadata.registerPlugValue( n["user"]["a"], "layout:index", 3 )
		Gaffer.Metadata.registerPlugValue( n["user"]["b"], "layout:index", 2 )
		Gaffer.Metadata.registerPlugValue( n["user"]["c"], "layout:index", 1 )

		self.assertEqual(
			GafferUI.PlugLayout.layoutOrder( n["user"] ),
			[ n["user"]["c"], n["user"]["b"], n["user"]["a"] ],
		)

	class CustomWidget( GafferUI.Widget ) :

		def __init__( self, node ) :

			GafferUI.Widget.__init__( self, GafferUI.Label( "Custom Widget" ) )

			self.node = node

	def testCustomWidgets( self ) :

		n = Gaffer.Node()
		Gaffer.Metadata.registerNodeValue( n, "layout:customWidget:test:widgetType", "GafferUITest.PlugLayoutTest.CustomWidget" )

		p = GafferUI.PlugLayout( n )

		self.assertTrue( isinstance( p.customWidget( "test", lazy = False ), self.CustomWidget ) )
		self.assertTrue( p.customWidget( "test" ).node.isSame( n ) )

	def testLazyBuilding( self ) :

		n = Gaffer.Node()
		n["a"] = Gaffer.IntPlug()

		with GafferUI.Window() as window :
			plugLayout = GafferUI.PlugLayout( n )

		self.assertTrue( plugLayout.plugValueWidget( n["a"], lazy = True ) is None )

		window.setVisible( True )

		self.assertTrue( plugLayout.plugValueWidget( n["a"], lazy = True ) is not None )

	def testSectionQueries( self ) :

		n = Gaffer.Node()
		n["user"]["a"] = Gaffer.IntPlug()
		n["user"]["b"] = Gaffer.IntPlug()
		n["user"]["c"] = Gaffer.IntPlug()

		self.assertEqual( GafferUI.PlugLayout.layoutSections( n["user"] ), [ "" ] )

		Gaffer.Metadata.registerPlugValue( n["user"]["a"], "layout:section", "A" )
		Gaffer.Metadata.registerPlugValue( n["user"]["b"], "layout:section", "B" )
		Gaffer.Metadata.registerPlugValue( n["user"]["c"], "layout:section", "C" )

		self.assertEqual( GafferUI.PlugLayout.layoutSections( n["user"] ), [ "A", "B", "C" ] )

		Gaffer.Metadata.registerPlugValue( n["user"]["a"], "layout:index", 3 )
		self.assertEqual( GafferUI.PlugLayout.layoutSections( n["user"] ), [ "B", "C", "A" ] )

	def testLayoutOrderSectionArgument( self ) :

		n = Gaffer.Node()
		n["user"]["a"] = Gaffer.IntPlug()
		n["user"]["b"] = Gaffer.IntPlug()
		n["user"]["c"] = Gaffer.IntPlug()

		self.assertEqual(
			GafferUI.PlugLayout.layoutOrder( n["user"], section = "" ),
			[ n["user"]["a"], n["user"]["b"], n["user"]["c"] ],
		)

		Gaffer.Metadata.registerPlugValue( n["user"]["a"], "layout:section", "AB" )
		Gaffer.Metadata.registerPlugValue( n["user"]["b"], "layout:section", "AB" )
		Gaffer.Metadata.registerPlugValue( n["user"]["c"], "layout:section", "C" )

		self.assertEqual(
			GafferUI.PlugLayout.layoutOrder( n["user"], section = "AB" ),
			[ n["user"]["a"], n["user"]["b"] ],
		)

		self.assertEqual(
			GafferUI.PlugLayout.layoutOrder( n["user"], section = "C" ),
			[ n["user"]["c"] ],
		)

if __name__ == "__main__":
	unittest.main()
