##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import os
import unittest

import IECore

import Gaffer
import GafferTest
import GafferDispatch
import GafferDispatchTest

class WedgeTest( GafferTest.TestCase ) :

	def __dispatcher( self, frameRange = None ) :

		result = GafferDispatch.LocalDispatcher( jobPool = GafferDispatch.LocalDispatcher.JobPool() )
		result["jobsDirectory"].setValue( self.temporaryDirectory() / "jobs" )

		if frameRange is not None :
			result["framesMode"].setValue( result.FramesMode.CustomRange )
			result["frameRange"].setValue( frameRange )

		return result

	def testStringList( self ) :

		script = Gaffer.ScriptNode()

		script["writer"] = GafferDispatchTest.TextWriter()
		script["writer"]["fileName"].setValue( self.temporaryDirectory() / "${name}.txt" )

		script["wedge"] = GafferDispatch.Wedge()
		script["wedge"]["preTasks"][0].setInput( script["writer"]["task"] )
		script["wedge"]["variable"].setValue( "name" )
		script["wedge"]["mode"].setValue( int( GafferDispatch.Wedge.Mode.StringList ) )
		script["wedge"]["strings"].setValue( IECore.StringVectorData( [ "tom", "dick", "harry" ] ) )

		script["dispatcher"] = self.__dispatcher()
		script["dispatcher"]["tasks"][0].setInput( script["wedge"]["task"] )
		script["dispatcher"]["task"].execute()

		self.assertEqual(
			set( self.temporaryDirectory().glob( "*.txt" ) ),
			{
				self.temporaryDirectory() / "tom.txt",
				self.temporaryDirectory() / "dick.txt",
				self.temporaryDirectory() / "harry.txt",
			}
		)

	def testIntList( self ) :

		script = Gaffer.ScriptNode()

		script["writer"] = GafferDispatchTest.TextWriter()
		script["writer"]["fileName"].setValue( self.temporaryDirectory() / "${wedge:value}.txt" )

		script["wedge"] = GafferDispatch.Wedge()
		script["wedge"]["preTasks"][0].setInput( script["writer"]["task"] )
		script["wedge"]["mode"].setValue( int( GafferDispatch.Wedge.Mode.IntList ) )
		script["wedge"]["ints"].setValue( IECore.IntVectorData( [ 1, 21, 44 ] ) )

		script["dispatcher"] = self.__dispatcher()
		script["dispatcher"]["tasks"][0].setInput( script["wedge"]["task"] )
		script["dispatcher"]["task"].execute()

		self.assertEqual(
			set( self.temporaryDirectory().glob( "*.txt" ) ),
			{
				self.temporaryDirectory() / "1.txt",
				self.temporaryDirectory() / "21.txt",
				self.temporaryDirectory() / "44.txt",
			}
		)

	def testFloatList( self ) :

		script = Gaffer.ScriptNode()

		script["writer"] = GafferDispatchTest.TextWriter()
		script["writer"]["fileName"].setValue( self.temporaryDirectory() / "${wedge:index}.txt" )
		script["writer"]["text"].setValue( "${wedge:value}" )

		script["wedge"] = GafferDispatch.Wedge()
		script["wedge"]["preTasks"][0].setInput( script["writer"]["task"] )
		script["wedge"]["mode"].setValue( int( GafferDispatch.Wedge.Mode.FloatList ) )
		script["wedge"]["floats"].setValue( IECore.FloatVectorData( [ 1.25, 2.75, 44.0 ] ) )

		script["dispatcher"] = self.__dispatcher()
		script["dispatcher"]["tasks"][0].setInput( script["wedge"]["task"] )
		script["dispatcher"]["task"].execute()

		self.assertEqual(
			set( self.temporaryDirectory().glob( "*.txt" ) ),
			{
				self.temporaryDirectory() / "0.txt",
				self.temporaryDirectory() / "1.txt",
				self.temporaryDirectory() / "2.txt",
			}
		)

		self.assertEqual( next( open( self.temporaryDirectory() / "0.txt", encoding = "utf-8" ) ), "1.25" )
		self.assertEqual( next( open( self.temporaryDirectory() / "1.txt", encoding = "utf-8" ) ), "2.75" )
		self.assertEqual( next( open( self.temporaryDirectory() / "2.txt", encoding = "utf-8" ) ), "44" )

	def testIntRange( self ) :

		script = Gaffer.ScriptNode()

		script["writer"] = GafferDispatchTest.TextWriter()
		script["writer"]["fileName"].setValue( self.temporaryDirectory() / "${number}.txt" )

		script["wedge"] = GafferDispatch.Wedge()
		script["wedge"]["preTasks"][0].setInput( script["writer"]["task"] )
		script["wedge"]["variable"].setValue( "number" )
		script["wedge"]["mode"].setValue( int( GafferDispatch.Wedge.Mode.IntRange ) )
		script["wedge"]["intMin"].setValue( 3 )
		script["wedge"]["intMax"].setValue( 7 )
		script["wedge"]["intStep"].setValue( 2 )

		script["dispatcher"] = self.__dispatcher()
		script["dispatcher"]["tasks"][0].setInput( script["wedge"]["task"] )
		script["dispatcher"]["task"].execute()

		self.assertEqual(
			set( self.temporaryDirectory().glob( "*.txt" ) ),
			{
				self.temporaryDirectory() / "3.txt",
				self.temporaryDirectory() / "5.txt",
				self.temporaryDirectory() / "7.txt",
			}
		)

	def testFloatRange( self ) :

		script = Gaffer.ScriptNode()

		script["writer"] = GafferDispatchTest.TextWriter()
		script["writer"]["fileName"].setValue( self.temporaryDirectory() / "${wedge:index}.txt" )
		script["writer"]["text"].setValue( "${wedge:value}" )

		script["wedge"] = GafferDispatch.Wedge()
		script["wedge"]["preTasks"][0].setInput( script["writer"]["task"] )
		script["wedge"]["mode"].setValue( int( GafferDispatch.Wedge.Mode.FloatRange ) )
		script["wedge"]["floatMin"].setValue( 0 )
		script["wedge"]["floatMax"].setValue( 1 )
		script["wedge"]["floatSteps"].setValue( 5 )

		script["dispatcher"] = self.__dispatcher()
		script["dispatcher"]["tasks"][0].setInput( script["wedge"]["task"] )
		script["dispatcher"]["task"].execute()

		self.assertEqual(
			set( self.temporaryDirectory().glob( "*.txt" ) ),
			{
				self.temporaryDirectory() / "0.txt",
				self.temporaryDirectory() / "1.txt",
				self.temporaryDirectory() / "2.txt",
				self.temporaryDirectory() / "3.txt",
				self.temporaryDirectory() / "4.txt",
			}
		)

		self.assertEqual( next( open( self.temporaryDirectory() / "0.txt", encoding = "utf-8" ) ), "0" )
		self.assertEqual( next( open( self.temporaryDirectory() / "1.txt", encoding = "utf-8" ) ), "0.25" )
		self.assertEqual( next( open( self.temporaryDirectory() / "2.txt", encoding = "utf-8" ) ), "0.5" )
		self.assertEqual( next( open( self.temporaryDirectory() / "3.txt", encoding = "utf-8" ) ), "0.75" )
		self.assertEqual( next( open( self.temporaryDirectory() / "4.txt", encoding = "utf-8" ) ), "1" )

	def testFloatByPointOne( self ) :

		script = Gaffer.ScriptNode()

		script["writer"] = GafferDispatchTest.TextWriter()
		script["writer"]["fileName"].setValue( self.temporaryDirectory() / "${wedge:index}.txt" )
		script["writer"]["text"].setValue( "${wedge:value}" )

		script["wedge"] = GafferDispatch.Wedge()
		script["wedge"]["preTasks"][0].setInput( script["writer"]["task"] )
		script["wedge"]["mode"].setValue( int( GafferDispatch.Wedge.Mode.FloatRange ) )
		script["wedge"]["floatMin"].setValue( 0 )
		script["wedge"]["floatMax"].setValue( 1 )
		script["wedge"]["floatSteps"].setValue( 11 )

		script["dispatcher"] = self.__dispatcher()
		script["dispatcher"]["tasks"][0].setInput( script["wedge"]["task"] )
		script["dispatcher"]["task"].execute()

		self.assertEqual(
			set( self.temporaryDirectory().glob( "*.txt" ) ),
			{
				self.temporaryDirectory() / "0.txt",
				self.temporaryDirectory() / "1.txt",
				self.temporaryDirectory() / "2.txt",
				self.temporaryDirectory() / "3.txt",
				self.temporaryDirectory() / "4.txt",
				self.temporaryDirectory() / "5.txt",
				self.temporaryDirectory() / "6.txt",
				self.temporaryDirectory() / "7.txt",
				self.temporaryDirectory() / "8.txt",
				self.temporaryDirectory() / "9.txt",
				self.temporaryDirectory() / "10.txt",
			}
		)

		self.assertAlmostEqual( float( next( open( self.temporaryDirectory() / "0.txt", encoding = "utf-8" ) ) ), 0 )
		self.assertAlmostEqual( float( next( open( self.temporaryDirectory() / "1.txt", encoding = "utf-8" ) ) ), 0.1 )
		self.assertAlmostEqual( float( next( open( self.temporaryDirectory() / "2.txt", encoding = "utf-8" ) ) ), 0.2 )
		self.assertAlmostEqual( float( next( open( self.temporaryDirectory() / "3.txt", encoding = "utf-8" ) ) ), 0.3 )
		self.assertAlmostEqual( float( next( open( self.temporaryDirectory() / "4.txt", encoding = "utf-8" ) ) ), 0.4 )
		self.assertAlmostEqual( float( next( open( self.temporaryDirectory() / "5.txt", encoding = "utf-8" ) ) ), 0.5 )
		self.assertAlmostEqual( float( next( open( self.temporaryDirectory() / "6.txt", encoding = "utf-8" ) ) ), 0.6 )
		self.assertAlmostEqual( float( next( open( self.temporaryDirectory() / "7.txt", encoding = "utf-8" ) ) ), 0.7 )
		self.assertAlmostEqual( float( next( open( self.temporaryDirectory() / "8.txt", encoding = "utf-8" ) ) ), 0.8 )
		self.assertAlmostEqual( float( next( open( self.temporaryDirectory() / "9.txt", encoding = "utf-8" ) ) ), 0.9 )
		self.assertAlmostEqual( float( next( open( self.temporaryDirectory() / "10.txt", encoding = "utf-8" ) ) ), 1 )

	def testColorRange( self ) :

		script = Gaffer.ScriptNode()

		script["writer"] = GafferDispatchTest.TextWriter()
		script["writer"]["fileName"].setValue( self.temporaryDirectory() / "${wedge:index}.txt" )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( 'c = context["wedge:value"]; parent["writer"]["text"] = "%.1f %.1f %.1f" % ( c[0], c[1], c[2] )' )

		script["wedge"] = GafferDispatch.Wedge()
		script["wedge"]["preTasks"][0].setInput( script["writer"]["task"] )
		script["wedge"]["mode"].setValue( int( GafferDispatch.Wedge.Mode.ColorRange ) )
		script["wedge"]["colorSteps"].setValue( 3 )

		script["dispatcher"] = self.__dispatcher()
		script["dispatcher"]["tasks"][0].setInput( script["wedge"]["task"] )
		script["dispatcher"]["task"].execute()

		self.assertEqual(
			set( self.temporaryDirectory().glob( "*.txt" ) ),
			{
				self.temporaryDirectory() / "0.txt",
				self.temporaryDirectory() / "1.txt",
				self.temporaryDirectory() / "2.txt",
			}
		)

		self.assertEqual( next( open( self.temporaryDirectory() / "0.txt", encoding = "utf-8" ) ), "0.0 0.0 0.0" )
		self.assertEqual( next( open( self.temporaryDirectory() / "1.txt", encoding = "utf-8" ) ), "0.5 0.5 0.5" )
		self.assertEqual( next( open( self.temporaryDirectory() / "2.txt", encoding = "utf-8" ) ), "1.0 1.0 1.0" )

	def test2DRange( self ) :

		script = Gaffer.ScriptNode()

		script["writer"] = GafferDispatchTest.TextWriter()
		script["writer"]["fileName"].setValue( self.temporaryDirectory() / "${wedge:x}.${wedge:y}.txt" )

		script["wedgeX"] = GafferDispatch.Wedge()
		script["wedgeX"]["preTasks"][0].setInput( script["writer"]["task"] )
		script["wedgeX"]["variable"].setValue( "wedge:x" )
		script["wedgeX"]["mode"].setValue( int( GafferDispatch.Wedge.Mode.IntRange ) )
		script["wedgeX"]["intMin"].setValue( 1 )
		script["wedgeX"]["intMax"].setValue( 3 )
		script["wedgeX"]["intStep"].setValue( 1 )

		script["wedgeY"] = GafferDispatch.Wedge()
		script["wedgeY"]["preTasks"][0].setInput( script["wedgeX"]["task"] )
		script["wedgeY"]["variable"].setValue( "wedge:y" )
		script["wedgeY"]["mode"].setValue( int( GafferDispatch.Wedge.Mode.IntRange ) )
		script["wedgeY"]["intMin"].setValue( 1 )
		script["wedgeY"]["intMax"].setValue( 2 )
		script["wedgeY"]["intStep"].setValue( 1 )

		script["dispatcher"] = self.__dispatcher()
		script["dispatcher"]["tasks"][0].setInput( script["wedgeY"]["task"] )
		script["dispatcher"]["task"].execute()

		self.assertEqual(
			set( self.temporaryDirectory().glob( "*.txt" ) ),
			{
				self.temporaryDirectory() / "1.1.txt",
				self.temporaryDirectory() / "1.2.txt",
				self.temporaryDirectory() / "2.1.txt",
				self.temporaryDirectory() / "2.2.txt",
				self.temporaryDirectory() / "3.1.txt",
				self.temporaryDirectory() / "3.2.txt",
			}
		)

	def testContext( self ) :

		script = Gaffer.ScriptNode()

		script["writer"] = GafferDispatchTest.TextWriter()
		script["writer"]["fileName"].setValue( self.temporaryDirectory() / "${name}.####.txt" )

		script["wedge"] = GafferDispatch.Wedge()
		script["wedge"]["preTasks"][0].setInput( script["writer"]["task"] )
		script["wedge"]["variable"].setValue( "name" )
		script["wedge"]["mode"].setValue( int( GafferDispatch.Wedge.Mode.StringList ) )
		script["wedge"]["strings"].setValue( IECore.StringVectorData( [ "tom", "dick", "harry" ] ) )

		script["dispatcher"] = self.__dispatcher( frameRange = "21-22" )
		script["dispatcher"]["tasks"][0].setInput( script["wedge"]["task"] )
		script["dispatcher"]["task"].execute()

		self.assertEqual(
			set( self.temporaryDirectory().glob( "*.txt" ) ),
			{
				self.temporaryDirectory() / "tom.0021.txt",
				self.temporaryDirectory() / "tom.0022.txt",
				self.temporaryDirectory() / "dick.0021.txt",
				self.temporaryDirectory() / "dick.0022.txt",
				self.temporaryDirectory() / "harry.0021.txt",
				self.temporaryDirectory() / "harry.0022.txt",
			}
		)

	def testUpstreamConstant( self ) :

		script = Gaffer.ScriptNode()

		script["constant"] = GafferDispatchTest.LoggingTaskNode()

		script["writer"] = GafferDispatchTest.TextWriter()
		script["writer"]["preTasks"][0].setInput( script["constant"]["task"] )
		script["writer"]["fileName"].setValue( self.temporaryDirectory() / "${name}.txt" )

		script["wedge"] = GafferDispatch.Wedge()
		script["wedge"]["preTasks"][0].setInput( script["writer"]["task"] )
		script["wedge"]["variable"].setValue( "name" )
		script["wedge"]["mode"].setValue( int( GafferDispatch.Wedge.Mode.StringList ) )
		script["wedge"]["strings"].setValue( IECore.StringVectorData( [ "tom", "dick", "harry" ] ) )

		script["dispatcher"] = self.__dispatcher()
		script["dispatcher"]["tasks"][0].setInput( script["wedge"]["task"] )
		script["dispatcher"]["task"].execute()

		self.assertEqual(
			set( self.temporaryDirectory().glob( "*.txt" ) ),
			{
				self.temporaryDirectory() / "tom.txt",
				self.temporaryDirectory() / "dick.txt",
				self.temporaryDirectory() / "harry.txt",
			}
		)

		# Even though the constant node is upstream from the wedge,
		# it should only execute once because it doesn't reference
		# the wedge variable at all.
		self.assertEqual( len( script["constant"].log ), 1 )

if __name__ == "__main__":
	unittest.main()
