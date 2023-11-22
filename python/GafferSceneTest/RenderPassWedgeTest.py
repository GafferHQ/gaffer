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

import inspect
import unittest

import IECore

import Gaffer
import GafferTest
import GafferDispatch
import GafferDispatchTest
import GafferScene

class RenderPassWedgeTest( GafferTest.TestCase ) :

	def __dispatcher( self, frameRange = None ) :

		result = GafferDispatch.LocalDispatcher()
		result["jobsDirectory"].setValue( self.temporaryDirectory() / "jobs" )

		if frameRange is not None :
			result["framesMode"].setValue( result.FramesMode.CustomRange )
			result["frameRange"].setValue( frameRange )

		return result

	def testPassNames( self ) :

		script = Gaffer.ScriptNode()

		script["writer"] = GafferDispatchTest.TextWriter()
		script["writer"]["fileName"].setValue( self.temporaryDirectory() / "${renderPass}.txt" )

		script["wedge"] = GafferScene.RenderPassWedge()
		script["wedge"]["preTasks"][0].setInput( script["writer"]["task"] )

		script["passes"] = GafferScene.RenderPasses()
		script["passes"]["names"].setValue( IECore.StringVectorData( [ "tom", "dick", "harry" ] ) )

		script["wedge"]["in"].setInput( script["passes"]["out"] )

		self.__dispatcher().dispatch( [ script["wedge"] ] )

		self.assertEqual(
			set( self.temporaryDirectory().glob( "*.txt" ) ),
			{
				self.temporaryDirectory() / "tom.txt",
				self.temporaryDirectory() / "dick.txt",
				self.temporaryDirectory() / "harry.txt",
			}
		)

	def testSkipDisabledPasses( self ) :

		script = Gaffer.ScriptNode()

		script["writer"] = GafferDispatchTest.TextWriter()
		script["writer"]["fileName"].setValue( self.temporaryDirectory() / "${renderPass}.txt" )

		script["wedge"] = GafferScene.RenderPassWedge()
		script["wedge"]["preTasks"][0].setInput( script["writer"]["task"] )

		script["passes"] = GafferScene.RenderPasses()
		script["passes"]["names"].setValue( IECore.StringVectorData( [ "tom", "dick", "harry" ] ) )

		script["disablePass"] = GafferScene.CustomOptions()
		script["disablePass"]["in"].setInput( script["passes"]["out"] )
		script["disablePass"]["options"].addChild( Gaffer.NameValuePlug( "renderPass:enabled", Gaffer.BoolPlug( "value", defaultValue = False ), True, "member1" ) )

		# disable harry
		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression(
			inspect.cleandoc(
				"""
				parent["disablePass"]["options"]["member1"]["value"] = context.get( "renderPass", "" ) != "harry"
				"""
			)
		)

		script["wedge"]["in"].setInput( script["disablePass"]["out"] )

		self.__dispatcher().dispatch( [ script["wedge"] ] )

		self.assertEqual(
			set( self.temporaryDirectory().glob( "*.txt" ) ),
			{
				self.temporaryDirectory() / "tom.txt",
				self.temporaryDirectory() / "dick.txt",
			}
		)

	def testContext( self ) :

		script = Gaffer.ScriptNode()

		script["writer"] = GafferDispatchTest.TextWriter()
		script["writer"]["fileName"].setValue( self.temporaryDirectory() / "${renderPass}.####.txt" )

		script["wedge"] = GafferScene.RenderPassWedge()
		script["wedge"]["preTasks"][0].setInput( script["writer"]["task"] )

		script["passes"] = GafferScene.RenderPasses()
		script["passes"]["names"].setValue( IECore.StringVectorData( [ "tom", "dick", "harry" ] ) )

		script["wedge"]["in"].setInput( script["passes"]["out"] )

		self.__dispatcher( frameRange = "21-22" ).dispatch( [ script["wedge"] ] )

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
		script["writer"]["fileName"].setValue( self.temporaryDirectory() / "${renderPass}.txt" )

		script["wedge"] = GafferScene.RenderPassWedge()
		script["wedge"]["preTasks"][0].setInput( script["writer"]["task"] )

		script["passes"] = GafferScene.RenderPasses()
		script["passes"]["names"].setValue( IECore.StringVectorData( [ "tom", "dick", "harry" ] ) )

		script["wedge"]["in"].setInput( script["passes"]["out"] )

		self.__dispatcher().dispatch( [ script["wedge"] ] )

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
		# the wedged `pass` variable at all.
		self.assertEqual( len( script["constant"].log ), 1 )

	def testPassNamesEvaluationUsesScriptStartFrame( self ) :

		script = Gaffer.ScriptNode()

		script["writer"] = GafferDispatchTest.TextWriter()

		script["wedge"] = GafferScene.RenderPassWedge()
		script["wedge"]["preTasks"][0].setInput( script["writer"]["task"] )

		script["passes"] = GafferScene.RenderPasses()
		script["wedge"]["in"].setInput( script["passes"]["out"] )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression(
			inspect.cleandoc(
				"""
				parent["passes"]["names"] = IECore.StringVectorData( [ "{}".format( int( context.getFrame() ) ) ] )
				"""
			)
		)

		for f in [ 1, 3, 5 ] :

			script["frameRange"]["start"].setValue( f )
			startFrame = str( f )

			with Gaffer.ContextMonitor( script["passes"] ) as monitor :
				with Gaffer.Context( script.context() ) as c :
					for i in range( 1, 10 ) :
						c.setFrame( i )
						self.assertEqual( script["wedge"]["names"].getValue(), IECore.StringVectorData( [ startFrame ] ) )

			self.assertEqual( monitor.combinedStatistics().numUniqueValues( "frame" ), 1 )

			testDirectory = self.temporaryDirectory() / startFrame
			script["writer"]["fileName"].setValue( testDirectory / "${renderPass}.####.txt" )

			with Gaffer.ContextMonitor( script["passes"] ) as monitor :
				with Gaffer.Context( script.context() ) as c :
					self.__dispatcher( frameRange = "21-22" ).dispatch( [ script["wedge"] ] )

			self.assertEqual( monitor.combinedStatistics().numUniqueValues( "frame" ), 1 )

			self.assertEqual(
				set( testDirectory.glob( "*.txt" ) ),
				{
					testDirectory / "{}.0021.txt".format( startFrame ),
					testDirectory / "{}.0022.txt".format( startFrame ),
				}
			)

if __name__ == "__main__":
	unittest.main()
