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

		result = GafferDispatch.LocalDispatcher( jobPool = GafferDispatch.LocalDispatcher.JobPool() )
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

		script["dispatcher"] = self.__dispatcher()
		script["dispatcher"]["tasks"][0].setInput( script["wedge"]["task"] )
		script["dispatcher"]["task"].execute()

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
		script["writer"]["fileName"].setValue( self.temporaryDirectory() / "${renderPass}.txt" )

		script["wedge"] = GafferScene.RenderPassWedge()
		script["wedge"]["preTasks"][0].setInput( script["writer"]["task"] )

		script["passes"] = GafferScene.RenderPasses()
		script["passes"]["names"].setValue( IECore.StringVectorData( [ "tom", "dick", "harry" ] ) )

		script["wedge"]["in"].setInput( script["passes"]["out"] )

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

		script["dispatcher"] = self.__dispatcher( frameRange = "21-22" )
		script["dispatcher"]["tasks"][0].setInput( script["wedge"]["task"] )

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
					script["dispatcher"]["task"].execute()

			self.assertEqual( monitor.combinedStatistics().numUniqueValues( "frame" ), 1 )

			self.assertEqual(
				set( testDirectory.glob( "*.txt" ) ),
				{
					testDirectory / "{}.0021.txt".format( startFrame ),
					testDirectory / "{}.0022.txt".format( startFrame ),
				}
			)

	def testAdaptorDeletingPasses( self ) :

		def createAdaptor() :

			node = GafferScene.DeleteRenderPasses()
			node["names"].setValue( "fx*" )
			return node

		GafferScene.SceneAlgo.registerRenderAdaptor( "RenderPassWedgeTest", createAdaptor, client = "RenderPassWedge" )
		self.addCleanup( GafferScene.SceneAlgo.deregisterRenderAdaptor, "RenderPassWedgeTest" )

		script = Gaffer.ScriptNode()

		script["renderPasses"] = GafferScene.RenderPasses()
		script["renderPasses"]["names"].setValue( IECore.StringVectorData( [ "char1", "char2", "fx1", "fx2" ] ) )

		script["log"] = GafferDispatchTest.LoggingTaskNode()
		script["log"]["dependsOnPass"] = Gaffer.StringPlug( defaultValue = "${renderPass}" )

		script["wedge"] = GafferScene.RenderPassWedge()
		script["wedge"]["preTasks"].next().setInput( script["log"]["task"] )
		script["wedge"]["in"].setInput( script["renderPasses"]["out"] )

		script["dispatcher"] = self.__dispatcher()
		script["dispatcher"]["tasks"].next().setInput( script["wedge"]["task"] )
		script["dispatcher"]["task"].execute()

		self.assertEqual(
			{ l.context["renderPass"] for l in script["log"].log },
			{ "char1", "char2" }
		)

	def testAdaptorDisablingPasses( self ) :

		def createAdaptor() :

			node = GafferScene.SceneProcessor()
			node["options"] = GafferScene.CustomOptions()
			node["options"]["in"].setInput( node["in"] )
			node["options"]["options"].addChild( Gaffer.NameValuePlug( "renderPass:enabled", False ) )

			node["switch"] = Gaffer.NameSwitch()
			node["switch"].setup( node["options"]["out"] )
			node["switch"]["in"][0]["value"].setInput( node["in"] )
			node["switch"]["in"][1]["value"].setInput( node["options"]["out"] )
			node["switch"]["in"][1]["name"].setValue( "char*" )
			node["switch"]["selector"].setValue( "${renderPass}" )

			node["out"].setInput( node["switch"]["out"]["value"] )

			return node

		GafferScene.SceneAlgo.registerRenderAdaptor( "RenderPassWedgeTest", createAdaptor, client = "RenderPassWedge" )
		self.addCleanup( GafferScene.SceneAlgo.deregisterRenderAdaptor, "RenderPassWedgeTest" )

		script = Gaffer.ScriptNode()

		script["renderPasses"] = GafferScene.RenderPasses()
		script["renderPasses"]["names"].setValue( IECore.StringVectorData( [ "char1", "char2", "fx1", "fx2" ] ) )

		script["log"] = GafferDispatchTest.LoggingTaskNode()
		script["log"]["dependsOnPass"] = Gaffer.StringPlug( defaultValue = "${renderPass}" )

		script["wedge"] = GafferScene.RenderPassWedge()
		script["wedge"]["preTasks"].next().setInput( script["log"]["task"] )
		script["wedge"]["in"].setInput( script["renderPasses"]["out"] )

		script["dispatcher"] = self.__dispatcher()
		script["dispatcher"]["tasks"].next().setInput( script["wedge"]["task"] )
		script["dispatcher"]["task"].execute()

		self.assertEqual(
			{ l.context["renderPass"] for l in script["log"].log },
			{ "fx1", "fx2" }
		)

if __name__ == "__main__":
	unittest.main()
