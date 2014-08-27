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

class SplinePlugTest( GafferTest.TestCase ) :

	def testConstructor( self ) :

		s = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 0, 0 ),
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
				( 1, 1 ),
			)
		)

		p = Gaffer.SplineffPlug( "a", defaultValue=s )

		self.assertEqual( p.getValue(), s )

		s2 = IECore.Splineff(
			IECore.CubicBasisf.linear(),
			(
				( 1, 1 ),
				( 1, 1 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 0, 0 ),
				( 0, 0 ),
			)
		)

		p.setValue( s2 )

		self.assertEqual( p.getValue(), s2 )

	def testSerialisation( self ) :

		s = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 0, 0 ),
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
				( 1, 1 ),
			)
		)

		p = Gaffer.SplineffPlug( "a", defaultValue=s, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
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

		defaultSpline = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 0, 0 ),
				( 0, 0 ),
				( 1, 1 ),
				( 1, 1 ),
			)
		)

		sn = Gaffer.ScriptNode()
		sn["n"] = Gaffer.Node()
		sn["n"]["p"] = Gaffer.SplineffPlug( "a", defaultValue=defaultSpline, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		self.assertEqual( sn["n"]["p"].getValue(), defaultSpline )

		valueSpline = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 0, 0 ),
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
				( 1, 1 ),
			)
		)

		sn["n"]["p"].setValue( valueSpline )
		self.assertEqual( sn["n"]["p"].getValue(), valueSpline )

		se = sn.serialise()

		sn = Gaffer.ScriptNode()
		sn.execute( se )

		self.assertEqual( sn["n"]["p"].getValue(), valueSpline )

	def testPointAccess( self ) :

		s = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 0, 0 ),
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
				( 1, 1 ),
			)
		)
		p = Gaffer.SplineffPlug( "a", defaultValue=s, flags=Gaffer.Plug.Flags.Dynamic )

		self.assertEqual( p.numPoints(), 4 )
		for i in range( p.numPoints() ) :
			self.assert_( p.pointXPlug( i ).isInstanceOf( Gaffer.FloatPlug.staticTypeId() ) )
			self.assert_( p.pointYPlug( i ).isInstanceOf( Gaffer.FloatPlug.staticTypeId() ) )
			self.assert_( p.pointXPlug( i ).parent().isSame( p.pointPlug( i ) ) )
			self.assert_( p.pointYPlug( i ).parent().isSame( p.pointPlug( i ) ) )

		# accessing nonexistent points should raise exceptions
		self.assertRaises( Exception, p.pointPlug, 4 )
		self.assertRaises( Exception, p.pointXPlug, 4 )
		self.assertRaises( Exception, p.pointYPlug, 4 )

	def testPointDeletion( self ) :

		s = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 0, 0 ),
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
				( 1, 1 ),
			)
		)
		p = Gaffer.SplineffPlug( "a", defaultValue=s, flags=Gaffer.Plug.Flags.Dynamic )

		self.assertEqual( p.numPoints(), 4 )
		for i in range( p.numPoints() ) :
			self.assert_( p.pointPlug( i ) )
			self.assert_( p.pointXPlug( i ) )
			self.assert_( p.pointYPlug( i ) )

		p.removePoint( 0 )

		self.assertEqual( p.numPoints(), 3 )
		for i in range( p.numPoints() ) :
			self.assert_( p.pointPlug( i ) )
			self.assert_( p.pointXPlug( i ) )
			self.assert_( p.pointYPlug( i ) )

		p.removeChild( p.pointPlug( 0 ) )

		self.assertEqual( p.numPoints(), 2 )
		for i in range( p.numPoints() ) :
			self.assert_( p.pointPlug( i ) )
			self.assert_( p.pointXPlug( i ) )
			self.assert_( p.pointYPlug( i ) )

	def testPointTampering( self ) :

		s = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 0, 0 ),
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
				( 1, 1 ),
			)
		)
		p = Gaffer.SplineffPlug( "a", defaultValue=s, flags=Gaffer.Plug.Flags.Dynamic )

		del p.pointPlug( 0 )["x"]
		del p.pointPlug( 0 )["y"]

		self.assertRaises( Exception, p.pointXPlug, 0 )
		self.assertRaises( Exception, p.pointYPlug, 0 )

	def testPlugSetSignal( self ) :

		s = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 0, 0 ),
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
				( 1, 1 ),
			)
		)
		p = Gaffer.SplineffPlug( "a", defaultValue=s, flags=Gaffer.Plug.Flags.Dynamic )
		n = Gaffer.Node()
		n["p"] = p

		self.__plugSetCount = 0
		def plugSet( plug ) :

			if plug.isSame( p ) :
				self.__plugSetCount += 1

		c = n.plugSetSignal().connect( plugSet )

		p.pointYPlug( 2 ).setValue( 1.0 )

		self.assertEqual( self.__plugSetCount, 1 )

		pointIndex = p.addPoint()

		self.assertEqual( self.__plugSetCount, 2 )

		p.removePoint( pointIndex )

		self.assertEqual( self.__plugSetCount, 3 )

	def testDefaultValue( self ) :

		s1 = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 0, 0 ),
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
				( 1, 1 ),
			)
		)

		s2 = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 1, 1 ),
				( 1, 1 ),
				( 0, 0 ),
				( 0, 0 ),
			)
		)

		p = Gaffer.SplineffPlug( "a", defaultValue=s1, flags=Gaffer.Plug.Flags.Dynamic )

		self.assertEqual( p.defaultValue(), s1 )
		self.assertEqual( p.getValue(), s1 )

		p.setValue( s2 )
		self.assertEqual( p.defaultValue(), s1 )
		self.assertEqual( p.getValue(), s2 )

		p.setToDefault()
		self.assertEqual( p.defaultValue(), s1 )
		self.assertEqual( p.getValue(), s1 )

	def testPlugFlags( self ) :

		s = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 0, 0 ),
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
				( 1, 1 ),
			)
		)

		p = Gaffer.SplineffPlug( "a", defaultValue=s )
		self.assertEqual( p.pointXPlug( 0 ).getFlags(), Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( p.pointYPlug( 0 ).getFlags(), Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

	def testConnection( self ) :

		s = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 0, 0 ),
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
				( 1, 1 ),
			)
		)

		p1 = Gaffer.SplineffPlug( defaultValue=s )
		p2 = Gaffer.SplineffPlug( defaultValue=s )

		p1.setInput( p2 )

		self.assertTrue( p1.getInput().isSame( p2 ) )
		self.assertTrue( p1["basis"].getInput().isSame( p2["basis"] ) )
		for i in range( 0, 4 ) :
			self.assertTrue( p1.pointPlug( i ).getInput().isSame( p2.pointPlug( i ) ) )

	def testCreateCounterpart( self ) :

		s = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 0, 0 ),
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
				( 1, 1 ),
			)
		)

		p1 = Gaffer.SplineffPlug( defaultValue=s )
		p2 = p1.createCounterpart( "p2", Gaffer.Plug.Direction.In )

		self.assertEqual( p2.getName(), "p2" )
		self.assertTrue( isinstance( p2, Gaffer.SplineffPlug ) )
		self.assertEqual( p2.numPoints(), p1.numPoints() )
		self.assertTrue( p2.getValue(), p1.getValue() )
		self.assertTrue( p2.defaultValue(), p1.defaultValue() )

	def testPromoteToBox( self ) :

		spline = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 0, 0 ),
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
				( 1, 1 ),
			)
		)

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.SplineffPlug( defaultValue=spline )

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )
		p = b.promotePlug( b["n"]["p"] )

		self.assertEqual( p.defaultValue(), b["n"]["p"].defaultValue() )
		self.assertEqual( p.numPoints(), b["n"]["p"].numPoints() )
		self.assertEqual( p.getValue().basis, b["n"]["p"].getValue().basis )
		self.assertEqual( len( p.getValue() ), len( b["n"]["p"].getValue() ) )
		self.assertEqual( p.getValue(), b["n"]["p"].getValue() )
		self.assertTrue( b["n"]["p"].getInput().isSame( p ) )

	def testSerialisationWithMorePointsThanDefault( self ) :

		s1 = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 0, 0 ),
				( 0, 0 ),
				( 1, 1 ),
				( 1, 1 ),
			)
		)

		s2 = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 0, 0 ),
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
				( 1, 1 ),
			)
		)

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.SplineffPlug( defaultValue=s1, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( s["n"]["p"].getValue(), s1 )
		s["n"]["p"].setValue( s2 )
		self.assertEqual( s["n"]["p"].getValue(), s2 )

		se = s.serialise()
		s = Gaffer.ScriptNode()
		s.execute( se )

		self.assertEqual( s["n"]["p"].getValue(), s2 )

	def testSerialisationWithLessPointsThanDefault( self ) :

		s1 = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 0, 0 ),
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
				( 1, 1 ),
			)
		)

		s2 = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 0, 0 ),
				( 0, 0 ),
				( 1, 1 ),
				( 1, 1 ),
			)
		)

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.SplineffPlug( defaultValue=s1, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( s["n"]["p"].getValue(), s1 )
		s["n"]["p"].setValue( s2 )
		self.assertEqual( s["n"]["p"].getValue(), s2 )

		se = s.serialise()
		s = Gaffer.ScriptNode()
		s.execute( se )

		self.assertEqual( s["n"]["p"].getValue(), s2 )

	def testEndPointMultiplicity( self ) :

		s1 = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			(
				( 0, 0 ),
				( 0, 0 ),
				( 1, 1 ),
				( 1, 1 ),
			)
		)

		s2 = IECore.Splineff(
			IECore.CubicBasisf.linear(),
			(
				( 0, 0 ),
				( 1, 1 ),
			)
		)

		p = Gaffer.SplineffPlug( defaultValue = s1 )
		self.assertEqual( p.getValue(), s1 )
		self.assertEqual( p["endPointMultiplicity"].defaultValue(), 2 )
		self.assertEqual( p["endPointMultiplicity"].getValue(), 2 )
		self.assertEqual( p.numPoints(), 2 )

		p.setValue( s2 )
		self.assertEqual( p.getValue(), s2 )
		self.assertEqual( p["endPointMultiplicity"].getValue(), 1 )
		self.assertEqual( p.numPoints(), 2 )

	def testDefaultConstructor( self ) :

		p = Gaffer.SplineffPlug()
		p.getValue()

if __name__ == "__main__":
	unittest.main()

