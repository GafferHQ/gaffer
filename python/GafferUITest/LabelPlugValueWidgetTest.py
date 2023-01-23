##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

import Gaffer
import GafferUI
import GafferUITest

class LabelPlugValueWidgetTest( GafferUITest.TestCase ) :

	def testHasUserValue( self ) :

		node = Gaffer.Node()
		node["user"]["v"] = Gaffer.V2fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		# No user-made edits to the value.

		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"]["x"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"]["y"] ) )

		# Even if it happens to be at the default value, the existence of a connection
		# means that we consider the value to be user-provided. This differs from
		# `ValuePlug.isSetToDefault()` which allows input connections if they provide
		# a static (non-context-sensitive) value that matches the default value. For
		# `ValuePlug` we only care about things that impact computed results, but for
		# `LabelPlugValueWidget` we want to highlight any edits made by the user.

		node["user"]["v"]["x"].setInput( node["user"]["v"]["y"] )
		self.assertTrue( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"] ) )
		self.assertTrue( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"] ) )
		self.assertTrue( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"]["x"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"]["y"] ) )

		# And that applies even if a user default was registered on a parent plug.

		Gaffer.Metadata.registerValue( node["user"]["v"], "userDefault", imath.V2f( 0 ) )
		self.assertTrue( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"] ) )
		self.assertTrue( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"] ) )
		self.assertTrue( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"]["x"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"]["y"] ) )

		# If we remove the connection, we should be back to the default state.

		node["user"]["v"]["x"].setInput( None )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"]["x"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"]["y"] ) )

		# If the value differs to the user default, then that's a user-provided value,
		# even if `ValuePlug.isSetToDefault()` is True.

		Gaffer.Metadata.registerValue( node["user"]["v"], "userDefault", imath.V2f( 1, 2 ) )
		self.assertTrue( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"] ) )
		self.assertTrue( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"] ) )
		self.assertTrue( node["user"]["v"].isSetToDefault() )

		# But if the value of the plug matches the user default, then it hasn't been
		# edited by the user, regardless of what `ValuePlug.isSetToDefault()` might say.

		Gaffer.NodeAlgo.applyUserDefault( node["user"]["v"] )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"] ) )
		self.assertFalse( node["user"]["v"].isSetToDefault() )

		# And this all applies if we put the user default on the leaf plugs instead.

		Gaffer.Metadata.deregisterValue( node["user"]["v"], "userDefault" )
		self.assertTrue( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"] ) )
		self.assertTrue( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"] ) )

		Gaffer.Metadata.registerValue( node["user"]["v"]["x"], "userDefault", 1 )
		Gaffer.Metadata.registerValue( node["user"]["v"]["y"], "userDefault", 2 )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"] ) )
		self.assertFalse( node["user"]["v"].isSetToDefault() )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"]["x"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"]["y"] ) )

		# Output plugs are never considered to have user edits, because the user doesn't
		# provide their values directly.

		node["user"]["o"] = Gaffer.V2fPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"]["x"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"]["y"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["o"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["o"]["x"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["o"]["y"] ) )

		node["user"]["o"]["y"].setInput( node["user"]["o"]["x"] )

		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"]["x"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["v"]["y"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["o"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["o"]["x"] ) )
		self.assertFalse( GafferUI.LabelPlugValueWidget._hasUserValue( node["user"]["o"]["y"] ) )

if __name__ == "__main__":
	unittest.main()
