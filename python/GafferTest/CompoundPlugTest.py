##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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
import gc

import IECore
import Gaffer
import GafferTest

class CompoundPlugTest( GafferTest.TestCase ) :

	def testContructor( self ) :

		p = Gaffer.CompoundPlug()
		self.assertEqual( p.getName(), "CompoundPlug" )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.In )

		p = Gaffer.V3fPlug( name="b", direction=Gaffer.Plug.Direction.Out )
		self.assertEqual( p.getName(), "b" )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.Out )

	def testDerivingInPython( self ) :

		class TestCompoundPlug( Gaffer.CompoundPlug ) :

			def __init__( self, name = "TestCompoundPlug", direction = Gaffer.Plug.Direction.In, flags = Gaffer.Plug.Flags.None ) :

				Gaffer.CompoundPlug.__init__( self, name, direction, flags )

			def acceptsChild( self, child ) :

				if not Gaffer.CompoundPlug.acceptsChild( self, child ) :
					return False

				return isinstance( child, Gaffer.IntPlug )

		IECore.registerRunTimeTyped( TestCompoundPlug )

		# check the constructor

		p = TestCompoundPlug()
		self.assertEqual( p.getName(), "TestCompoundPlug" )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( p.getFlags(), Gaffer.Plug.Flags.None )

		p = TestCompoundPlug( name = "p", direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( p.getName(), "p" )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.Out )
		self.assertEqual( p.getFlags(), Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		# check that acceptsChild can be overridden

		p = TestCompoundPlug()

		self.assertRaises( RuntimeError, p.addChild, Gaffer.FloatPlug() )

		p.addChild( Gaffer.IntPlug() )

		# check that the fact the plug has been wrapped solves the object identity problem

		p = TestCompoundPlug()
		n = Gaffer.Node()
		n["p"] = p

		self.failUnless( n["p"] is p )

	def testRunTimeTyped( self ) :

		p = Gaffer.CompoundPlug( "hello" )
		self.failUnless( p.isInstanceOf( Gaffer.CompoundPlug.staticTypeId() ) )

		self.assertEqual( IECore.RunTimeTyped.baseTypeId( p.typeId() ), Gaffer.ValuePlug.staticTypeId() )

	def testCreateCounterpart( self ) :

		c = Gaffer.CompoundPlug( "a", Gaffer.Plug.Direction.Out )
		c["b"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		c["c"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )

		c2 = c.createCounterpart( "aa", Gaffer.Plug.Direction.In )

		self.assertEqual( c2.getName(), "aa" )
		self.assertEqual( c2.direction(), Gaffer.Plug.Direction.In )

		self.assertEqual( c2["b"].direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( c2["c"].direction(), Gaffer.Plug.Direction.In )

	def testNonValuePlugChildren( self ) :

		c = Gaffer.CompoundPlug()
		p = Gaffer.Plug()

		self.assertTrue( c.acceptsChild( p ) )
		c["p"] = p
		self.assertTrue( p.parent().isSame( c ) )

if __name__ == "__main__":
	unittest.main()
