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

import Gaffer
import GafferUI
import GafferUITest

class StandardNodeUITest( GafferUITest.TestCase ) :

	def testPlugValueWidgetAccess( self ) :

		n = Gaffer.Node()
		n["c"] = Gaffer.Plug()
		n["c"]["i"] = Gaffer.IntPlug()
		n["c"]["s"] = Gaffer.StringPlug()

		Gaffer.Metadata.registerValue( n["c"], "plugValueWidget:type", "GafferUI.LayoutPlugValueWidget" )

		u = GafferUI.StandardNodeUI( n )

		self.assertTrue( isinstance( u.plugValueWidget( n["c"] ), GafferUI.PlugValueWidget ) )
		self.assertTrue( u.plugValueWidget( n["c"] ).getPlug().isSame( n["c"] ) )

		self.assertTrue( isinstance( u.plugValueWidget( n["c"]["i"] ), GafferUI.PlugValueWidget ) )
		self.assertTrue( u.plugValueWidget( n["c"]["i"] ).getPlug().isSame( n["c"]["i"] ) )

	def testSetReadOnlyForUserPlugs( self ) :

		n = Gaffer.Node()
		n["user"]["a"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		u = GafferUI.StandardNodeUI( n )
		self.assertEqual( u.plugValueWidget( n["user"]["a"] ).getReadOnly(), False )

		u.setReadOnly( True )
		self.assertEqual( u.plugValueWidget( n["user"]["a"] ).getReadOnly(), True )

		u = GafferUI.StandardNodeUI( n )
		w = u.plugValueWidget( n["user"]["a"] )

		u.setReadOnly( True )
		self.assertEqual( w.getReadOnly(), True )

if __name__ == "__main__":
	unittest.main()
