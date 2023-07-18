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

import Gaffer
import GafferTest

class OptionalValuePlugTest( GafferTest.TestCase ) :

	def testConstruction( self ) :

		valuePlug = Gaffer.IntPlug()
		plug = Gaffer.OptionalValuePlug( "name", valuePlug, True )

		self.assertEqual( plug.getName(), "name" )
		self.assertEqual( plug.direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( len( plug ), 2 )

		self.assertIsInstance( plug["enabled"], Gaffer.BoolPlug )
		self.assertEqual( plug["enabled"].defaultValue(), True )
		self.assertEqual( plug["enabled"].direction(), Gaffer.Plug.Direction.In )
		self.assertTrue( plug["enabled"].isSame( plug[0] ) )

		self.assertTrue( plug["value"].isSame( valuePlug ) )
		self.assertTrue( plug["value"].isSame( plug[1] ) )

	def testAcceptsChild( self ) :

		plug = Gaffer.OptionalValuePlug( "name", Gaffer.IntPlug() )
		self.assertFalse( plug.acceptsChild( Gaffer.IntPlug() ) )

	def testCreateCounterpart( self ) :

		plug = Gaffer.OptionalValuePlug( "name", Gaffer.IntPlug() )
		plug["enabled"].setValue( True ) # Current values should be ignored by
		plug["value"].setValue( 10 )     # `createCounterpart()`.

		for direction in ( Gaffer.Plug.Direction.In, Gaffer.Plug.Direction.Out ) :

			with self.subTest( direction = direction ) :

				plug2 = plug.createCounterpart( "counter", direction )
				self.assertEqual( plug2.direction(), direction )
				self.assertTrue( plug2.isSetToDefault() )

				self.assertEqual( plug2["enabled"].direction(), direction )
				self.assertEqual( plug2["enabled"].defaultValue(), plug["enabled"].defaultValue() )

				self.assertEqual( plug2["value"].direction(), direction )
				self.assertIsInstance( plug2["value"], Gaffer.IntPlug )
				self.assertEqual( plug2["value"].defaultValue(), plug["value"].defaultValue() )

	def testSerialisation( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = Gaffer.Node()
		script["node"]["user"]["p"] = Gaffer.OptionalValuePlug( valuePlug = Gaffer.IntPlug(), enabledPlugDefaultValue = True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		script["node"]["user"]["p"]["enabled"].setValue( False )
		script["node"]["user"]["p"]["value"].setValue( 10 )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		self.assertEqual( script2["node"]["user"]["p"]["enabled"].defaultValue(), script["node"]["user"]["p"]["enabled"].defaultValue() )
		self.assertEqual( script2["node"]["user"]["p"]["enabled"].getValue(), script["node"]["user"]["p"]["enabled"].getValue() )
		self.assertEqual( script2["node"]["user"]["p"]["value"].defaultValue(), script["node"]["user"]["p"]["value"].defaultValue() )
		self.assertEqual( script2["node"]["user"]["p"]["value"].getValue(), script["node"]["user"]["p"]["value"].getValue() )

if __name__ == "__main__":
	unittest.main()
