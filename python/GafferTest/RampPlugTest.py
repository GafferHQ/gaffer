##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import IECore

import Gaffer
import GafferTest

class RampPlugTest( GafferTest.TestCase ) :

	def testConstructor( self ) :

		s = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		p = Gaffer.RampffPlug( "a", defaultValue=s )

		self.assertEqual( p.getValue(), s )

		s2 = IECore.Rampff(
			(
				( 1, 1 ),
				( 1, 1 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 0, 0 ),
				( 0, 0 ),
			),
			IECore.RampInterpolation.Linear
		)

		p.setValue( s2 )

		self.assertEqual( p.getValue(), s2 )

	def testSerialisation( self ) :

		s = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		p = Gaffer.RampffPlug( "a", defaultValue=s, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( p.getValue(), s )

		sn = Gaffer.ScriptNode()
		sn["n"] = Gaffer.Node()
		sn["n"]["p"] = p

		se = sn.serialise()
		sn = Gaffer.ScriptNode()
		sn.execute( se )

		self.assertEqual( sn["n"]["p"].getValue(), s )
		self.assertEqual( len( sn["n"]["p"].pointPlug( 0 ) ), 2 )
		self.assertEqual( sn["n"]["p"].pointPlug( 0 ).keys(), [ "x", "y" ] )

	def testSerialisationWithNonDefaultValue( self ) :

		defaultSpline = IECore.Rampff(
			(
				( 0, 0 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		sn = Gaffer.ScriptNode()
		sn["n"] = Gaffer.Node()
		sn["n"]["p"] = Gaffer.RampffPlug( "a", defaultValue=defaultSpline, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		self.assertEqual( sn["n"]["p"].getValue(), defaultSpline )

		valueSpline = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		sn["n"]["p"].setValue( valueSpline )
		self.assertEqual( sn["n"]["p"].getValue(), valueSpline )

		se = sn.serialise()

		sn = Gaffer.ScriptNode()
		sn.execute( se )

		self.assertEqual( sn["n"]["p"].getValue(), valueSpline )

	def testPointAccess( self ) :

		s = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)
		p = Gaffer.RampffPlug( "a", defaultValue=s, flags=Gaffer.Plug.Flags.Dynamic )

		self.assertEqual( p.numPoints(), 4 )
		for i in range( p.numPoints() ) :
			self.assertTrue( p.pointXPlug( i ).isInstanceOf( Gaffer.FloatPlug.staticTypeId() ) )
			self.assertTrue( p.pointYPlug( i ).isInstanceOf( Gaffer.FloatPlug.staticTypeId() ) )
			self.assertTrue( p.pointXPlug( i ).parent().isSame( p.pointPlug( i ) ) )
			self.assertTrue( p.pointYPlug( i ).parent().isSame( p.pointPlug( i ) ) )

		# accessing nonexistent points should raise exceptions
		self.assertRaises( Exception, p.pointPlug, 4 )
		self.assertRaises( Exception, p.pointXPlug, 4 )
		self.assertRaises( Exception, p.pointYPlug, 4 )

	def testPointDeletion( self ) :

		s = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)
		p = Gaffer.RampffPlug( "a", defaultValue=s, flags=Gaffer.Plug.Flags.Dynamic )

		self.assertEqual( p.numPoints(), 4 )
		for i in range( p.numPoints() ) :
			self.assertIsNotNone( p.pointPlug( i ) )
			self.assertIsNotNone( p.pointXPlug( i ) )
			self.assertIsNotNone( p.pointYPlug( i ) )

		p.removePoint( 0 )

		self.assertEqual( p.numPoints(), 3 )
		for i in range( p.numPoints() ) :
			self.assertIsNotNone( p.pointPlug( i ) )
			self.assertIsNotNone( p.pointXPlug( i ) )
			self.assertIsNotNone( p.pointYPlug( i ) )

		p.removeChild( p.pointPlug( 0 ) )

		self.assertEqual( p.numPoints(), 2 )
		for i in range( p.numPoints() ) :
			self.assertIsNotNone( p.pointPlug( i ) )
			self.assertIsNotNone( p.pointXPlug( i ) )
			self.assertIsNotNone( p.pointYPlug( i ) )

	def testPointTampering( self ) :

		s = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)
		p = Gaffer.RampffPlug( "a", defaultValue=s, flags=Gaffer.Plug.Flags.Dynamic )

		del p.pointPlug( 0 )["x"]
		del p.pointPlug( 0 )["y"]

		self.assertRaises( Exception, p.pointXPlug, 0 )
		self.assertRaises( Exception, p.pointYPlug, 0 )

	def testPlugSetSignal( self ) :

		s = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)
		p = Gaffer.RampffPlug( "a", defaultValue=s, flags=Gaffer.Plug.Flags.Dynamic )
		n = Gaffer.Node()
		n["p"] = p

		self.__plugSetCount = 0
		def plugSet( plug ) :

			if plug.isSame( p ) :
				self.__plugSetCount += 1

		n.plugSetSignal().connect( plugSet )

		p.pointYPlug( 2 ).setValue( 1.0 )

		self.assertEqual( self.__plugSetCount, 1 )

		pointIndex = p.addPoint()

		self.assertEqual( self.__plugSetCount, 2 )

		p.removePoint( pointIndex )

		self.assertEqual( self.__plugSetCount, 3 )

	def testDefaultValue( self ) :

		s1 = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		s2 = IECore.Rampff(
			(
				( 1, 1 ),
				( 0, 0 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		p = Gaffer.RampffPlug( "a", defaultValue=s1, flags=Gaffer.Plug.Flags.Dynamic )

		self.assertEqual( p.defaultValue(), s1 )
		self.assertEqual( p.getValue(), s1 )
		self.assertTrue( p.isSetToDefault() )
		for cp in Gaffer.ValuePlug.RecursiveRange( p ) :
			self.assertTrue( cp.isSetToDefault() )

		p.setValue( s2 )
		self.assertEqual( p.defaultValue(), s1 )
		self.assertEqual( p.getValue(), s2 )
		self.assertFalse( p.isSetToDefault() )

		p.setToDefault()
		self.assertEqual( p.defaultValue(), s1 )
		self.assertEqual( p.getValue(), s1 )
		self.assertTrue( p.isSetToDefault() )
		for cp in Gaffer.ValuePlug.RecursiveRange( p ) :
			self.assertTrue( cp.isSetToDefault() )

	def testResetDefault( self ) :

		s1 = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		s2 = IECore.Rampff(
			(
				( 1, 1 ),
				( 0, 0 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		script = Gaffer.ScriptNode()
		script["n"] = Gaffer.Node()
		script["n"]["user"]["p"] = Gaffer.RampffPlug( "a", defaultValue = s1, flags = Gaffer.Plug.Flags.Dynamic )

		def assertPreconditions() :

			self.assertEqual( script["n"]["user"]["p"].getValue(), s1 )
			self.assertEqual( script["n"]["user"]["p"].defaultValue(), s1 )
			for p in Gaffer.ValuePlug.RecursiveRange( script["n"] ) :
				self.assertTrue( p.isSetToDefault() )

		assertPreconditions()

		with Gaffer.UndoScope( script ) :
			script["n"]["user"]["p"].setValue( s2 )
			script["n"]["user"]["p"].resetDefault()

		def assertPostconditions() :

			self.assertEqual( script["n"]["user"]["p"].getValue(), s2 )
			self.assertEqual( script["n"]["user"]["p"].defaultValue(), s2 )
			for p in Gaffer.ValuePlug.RecursiveRange( script["n"] ) :
				self.assertTrue( p.isSetToDefault() )

		script.undo()
		assertPreconditions()

		script.redo()
		assertPostconditions()

	def testPlugFlags( self ) :

		s = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		p = Gaffer.RampffPlug( "a", defaultValue=s )
		self.assertEqual( p.pointXPlug( 0 ).getFlags(), Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( p.pointYPlug( 0 ).getFlags(), Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

	def testConnection( self ) :

		s = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		p1 = Gaffer.RampffPlug( defaultValue=s )
		p2 = Gaffer.RampffPlug( defaultValue=s )

		p1.setInput( p2 )

		self.assertTrue( p1.getInput().isSame( p2 ) )
		self.assertTrue( p1["interpolation"].getInput().isSame( p2["interpolation"] ) )
		for i in range( 0, 4 ) :
			self.assertTrue( p1.pointPlug( i ).getInput().isSame( p2.pointPlug( i ) ) )

	def testCreateCounterpart( self ) :

		s = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		p1 = Gaffer.RampffPlug( defaultValue=s )
		p2 = p1.createCounterpart( "p2", Gaffer.Plug.Direction.In )

		self.assertEqual( p2.getName(), "p2" )
		self.assertTrue( isinstance( p2, Gaffer.RampffPlug ) )
		self.assertEqual( p2.numPoints(), p1.numPoints() )
		self.assertTrue( p2.isSetToDefault() )
		self.assertEqual( p2.defaultValue(), p1.defaultValue() )

	def testPromoteToBox( self ) :

		spline = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.RampffPlug( defaultValue=spline )

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )
		p = Gaffer.PlugAlgo.promote( b["n"]["p"] )

		self.assertEqual( p.defaultValue(), b["n"]["p"].defaultValue() )
		self.assertEqual( p.numPoints(), b["n"]["p"].numPoints() )
		self.assertEqual( p.getValue().interpolation, b["n"]["p"].getValue().interpolation )
		self.assertEqual( len( p.getValue().points() ), len( b["n"]["p"].getValue().points() ) )
		self.assertEqual( p.getValue(), b["n"]["p"].getValue() )
		self.assertTrue( b["n"]["p"].getInput().isSame( p ) )

	def testPromoteToBoxWithExtraPoints( self ) :

		spline = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.RampffPlug( defaultValue=spline )
		i = s["n"]["p"].addPoint()
		s["n"]["p"][i]["x"].setValue( 0.1 )
		s["n"]["p"][i]["y"].setValue( 0.2 )

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )
		p = Gaffer.PlugAlgo.promote( b["n"]["p"] )

		self.assertEqual( p.defaultValue(), b["n"]["p"].defaultValue() )
		self.assertEqual( p.numPoints(), b["n"]["p"].numPoints() )
		self.assertEqual( p.getValue().interpolation, b["n"]["p"].getValue().interpolation )
		self.assertEqual( len( p.getValue().points() ), len( b["n"]["p"].getValue().points() ) )
		self.assertEqual( p.getValue(), b["n"]["p"].getValue() )
		self.assertTrue( b["n"]["p"].getInput().isSame( p ) )

	def testSerialisationWithMorePointsThanDefault( self ) :

		s1 = IECore.Rampff(
			(
				( 0, 0 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		s2 = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.RampffPlug( defaultValue=s1, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( s["n"]["p"].getValue(), s1 )
		s["n"]["p"].setValue( s2 )
		self.assertEqual( s["n"]["p"].getValue(), s2 )

		se = s.serialise()
		s = Gaffer.ScriptNode()
		s.execute( se )

		self.assertEqual( s["n"]["p"].getValue(), s2 )

	def testSerialisationWithLessPointsThanDefault( self ) :

		s1 = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		s2 = IECore.Rampff(
			(
				( 0, 0 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.RampffPlug( defaultValue=s1, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( s["n"]["p"].getValue(), s1 )
		s["n"]["p"].setValue( s2 )
		self.assertEqual( s["n"]["p"].getValue(), s2 )

		se = s.serialise()
		s = Gaffer.ScriptNode()
		s.execute( se )

		self.assertEqual( s["n"]["p"].getValue(), s2 )

	def testDefaultConstructor( self ) :

		p = Gaffer.RampffPlug()
		p.getValue()

	def testTruncatedDefaultValue( self ) :

		defaultValue = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.5, 0.5 ),
				( 0.5, 0.5 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		# This tricky value could fool a naive implementation
		# of isSetToDefault().
		truncatedDefaultValue = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.5, 0.5 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		p = Gaffer.RampffPlug( "a", defaultValue=defaultValue, flags=Gaffer.Plug.Flags.Dynamic )

		p.setValue( truncatedDefaultValue )
		self.assertEqual( p.defaultValue(), defaultValue )
		self.assertEqual( p.getValue(), truncatedDefaultValue )
		self.assertFalse( p.isSetToDefault() )

	def testConnectionSerialisation( self ) :

		s = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		script = Gaffer.ScriptNode()
		script["n"] = Gaffer.Node()
		script["n"]["user"]["p1"] = Gaffer.RampffPlug( defaultValue=s, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		script["n"]["user"]["p2"] = Gaffer.RampffPlug( defaultValue=s, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		script["n"]["user"]["p2"].setInput( script["n"]["user"]["p1"] )

		def assertConnection( script ) :

			self.assertTrue( script["n"]["user"]["p2"].getInput().isSame( script["n"]["user"]["p1"] ) )
			self.assertTrue( script["n"]["user"]["p2"]["interpolation"].getInput().isSame( script["n"]["user"]["p1"]["interpolation"] ) )
			for i in range( 0, 4 ) :
				self.assertTrue( script["n"]["user"]["p2"].pointPlug( i ).getInput().isSame( script["n"]["user"]["p1"].pointPlug( i ) ) )

		assertConnection( script )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		assertConnection( script2 )

	def testPartialConnectionSerialisation( self ) :

		s = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		script = Gaffer.ScriptNode()
		script["n"] = Gaffer.Node()
		script["n"]["user"]["s"] = Gaffer.RampffPlug( defaultValue=s, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		script["n"]["user"]["x"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		script["n"]["user"]["y"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		script["n"]["user"]["s"].pointXPlug( 0 ).setInput( script["n"]["user"]["x"] )
		script["n"]["user"]["s"].pointYPlug( 2 ).setInput( script["n"]["user"]["y"] )

		def assertConnection( script ) :

			self.assertTrue( script["n"]["user"]["s"].getInput() is None )
			self.assertTrue( script["n"]["user"]["s"]["interpolation"].getInput() is None )
			for i in range( 0, 4 ) :

				if i == 0 :
					self.assertTrue( script["n"]["user"]["s"].pointXPlug( i ).getInput().isSame( script["n"]["user"]["x"] ) )
				else :
					self.assertTrue( script["n"]["user"]["s"].pointXPlug( i ).getInput() is None )

				if i == 2 :
					self.assertTrue( script["n"]["user"]["s"].pointYPlug( i ).getInput().isSame( script["n"]["user"]["y"] ) )
				else :
					self.assertTrue( script["n"]["user"]["s"].pointYPlug( i ).getInput() is None )

		assertConnection( script )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		assertConnection( script2 )

	def testDefaultHash( self ) :

		s1 = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		s2 = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 0.5, 0.95 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		self.assertEqual( Gaffer.RampffPlug().defaultHash(), Gaffer.RampffPlug().defaultHash() )
		self.assertNotEqual( Gaffer.RampffPlug().defaultHash(), Gaffer.RampffPlug( defaultValue = s1 ).defaultHash() )

		p = Gaffer.RampffPlug( defaultValue = s1 )
		h = p.defaultHash()
		p.setValue( s2 )
		self.assertEqual( p.defaultHash(), h )

	def testIsSetToDefaultAndConnections( self ) :

		definition = IECore.Rampff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			IECore.RampInterpolation.CatmullRom
		)

		plug = Gaffer.RampffPlug( defaultValue = definition )
		self.assertTrue( plug.isSetToDefault() )

		# Static (not computed) input providing the same value as default.

		staticInput = plug.pointPlug( 1 ).createCounterpart( "input", Gaffer.Plug.Direction.In )
		plug.pointPlug( 1 ).setInput( staticInput )
		self.assertTrue( plug.isSetToDefault() )

		# Computed input that happens to provide the same value as default.
		# This is treated as non-default, because it could differ by context
		# and `ValuePlug::isSetToDefault()` is documented as never triggering
		# computes.

		computedInput = GafferTest.AddNode()
		plug.pointPlug( 0 )["x"].setInput( computedInput["sum"] )
		self.assertFalse( plug.isSetToDefault() )

if __name__ == "__main__":
	unittest.main()
