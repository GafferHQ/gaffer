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

import IECore

import Gaffer
import GafferTest

class SerialisationTest( GafferTest.TestCase ) :

	class SerialisationTestNode( Gaffer.Node ) :

		def __init__( self, name = "SerialisationTestNode", initArgument = 10 ) :

			Gaffer.Node.__init__( self, name )

			self.initArgument = initArgument

			self["childNodeNeedingSerialisation"] = GafferTest.AddNode()
			self["childNodeNotNeedingSerialisation"] = GafferTest.AddNode()

	IECore.registerRunTimeTyped( SerialisationTestNode )

	def testCustomSerialiser( self ) :

		class CustomSerialiser( Gaffer.Serialisation.Serialiser ) :

			def moduleDependencies( self, node ) :

				return ( "GafferTest", )

			def constructor( self, node ) :

				return ( "GafferTest.SerialisationTest.SerialisationTestNode( \"%s\", %d )" % ( node.getName(), node.initArgument ) )

			def postConstructor( self, node, identifier, serialisation ) :

				return identifier + ".postConstructorWasHere = True\n"

			def postHierarchy( self, node, identifier, serialisation ) :

				return identifier + ".postHierarchyWasHere = True\n"

			def postScript( self, node, identifier, serialisation ) :

				return identifier + ".postScriptWasHere = True\n"

			def childNeedsSerialisation( self, child ) :

				if isinstance( child, Gaffer.Node ) :
					return child.getName() == "childNodeNeedingSerialisation"
				elif isinstance( child, Gaffer.Plug ) :
					return child.getFlags( Gaffer.Plug.Flags.Serialisable )

				return False

			def childNeedsConstruction( self, child ) :

				if isinstance( child, Gaffer.Node ) :
					return False
				elif isinstance( child, Gaffer.Plug ) :
					return child.getFlags( Gaffer.Plug.Flags.Dynamic )

				return False

		customSerialiser = CustomSerialiser()
		Gaffer.Serialisation.registerSerialiser( self.SerialisationTestNode, customSerialiser )

		s = Gaffer.ScriptNode()
		s["n"] = self.SerialisationTestNode( "a", initArgument=20 )
		s["n"]["childNodeNeedingSerialisation"]["op1"].setValue( 101 )
		s["n"]["childNodeNotNeedingSerialisation"]["op1"].setValue( 101 )
		s["n"]["dynamicPlug"] = Gaffer.FloatPlug( defaultValue = 10, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		self.assertTrue( Gaffer.Serialisation.acquireSerialiser( s["n"] ).isSame( customSerialiser ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( isinstance( s2["n"], self.SerialisationTestNode ) )
		self.assertEqual( s["n"].keys(), s2["n"].keys() )

		self.assertEqual( s2["n"].initArgument, 20 )
		self.assertEqual( s2["n"]["childNodeNeedingSerialisation"]["op1"].getValue(), 101 )
		self.assertEqual( s2["n"]["childNodeNotNeedingSerialisation"]["op1"].getValue(), 0 )
		self.assertEqual( s2["n"]["dynamicPlug"].getValue(), 10 )
		self.assertEqual( s2["n"].postConstructorWasHere, True )
		self.assertEqual( s2["n"].postHierarchyWasHere, True )
		self.assertEqual( s2["n"].postScriptWasHere, True )

if __name__ == "__main__":
	unittest.main()

