##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Limited. All rights reserved.
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

import GafferUI
import GafferUITest
import GafferSceneTest
import GafferSceneUI

class InspectorColumnTest( GafferUITest.TestCase ) :

	def testInspectorColumnConstructors( self ) :

		light = GafferSceneTest.TestLight()

		inspector = GafferSceneUI.Private.AttributeInspector( light["out"], None, "gl:visualiser:scale" )

		c = GafferSceneUI.Private.InspectorColumn( inspector, "label", "help!" )
		self.assertEqual( c.inspector(), inspector )
		self.assertEqual( c.getSizeMode(), GafferUI.PathColumn.SizeMode.Default )
		self.assertEqual( c.headerData().value, "Label" )
		self.assertEqual( c.headerData().toolTip, "help!" )

		c = GafferSceneUI.Private.InspectorColumn( inspector, "Fancy ( Label )", "" )
		self.assertEqual( c.inspector(), inspector )
		self.assertEqual( c.getSizeMode(), GafferUI.PathColumn.SizeMode.Default )
		self.assertEqual( c.headerData().value, "Fancy ( Label )" )
		self.assertEqual( c.headerData().toolTip, "" )

		c = GafferSceneUI.Private.InspectorColumn( inspector )
		self.assertEqual( c.inspector(), inspector )
		self.assertEqual( c.getSizeMode(), GafferUI.PathColumn.SizeMode.Default )
		self.assertEqual( c.headerData().value, "Gl:visualiser:scale" )
		self.assertEqual( c.headerData().toolTip, "" )

		c = GafferSceneUI.Private.InspectorColumn(
			inspector,
			GafferUI.PathColumn.CellData( value = "Fancy ( Label )", toolTip = "help!" ),
			GafferUI.PathColumn.SizeMode.Stretch
		)
		self.assertEqual( c.inspector(), inspector )
		self.assertEqual( c.getSizeMode(), GafferUI.PathColumn.SizeMode.Stretch )
		self.assertEqual( c.headerData().value, "Fancy ( Label )" )
		self.assertEqual( c.headerData().toolTip, "help!" )

if __name__ == "__main__":
	unittest.main()
