##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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
import threading

import IECore

import Gaffer
import GafferScene
import GafferSceneUI
import GafferSceneTest

class HistoryPathTest( GafferSceneTest.SceneTestCase ) :

	@staticmethod
	def __inspector( scene, parameter, editScope=None, attribute="light" ) :

		editScopePlug = Gaffer.Plug()
		editScopePlug.setInput( editScope["enabled"] if editScope is not None else None )
		inspector = GafferSceneUI.Private.ParameterInspector(
			scene, editScopePlug, attribute, ( "", parameter )
		)

		return inspector

	def setUp( self ) :

		GafferSceneTest.SceneTestCase.setUp( self )
		# Ignore messages intended to catch bad usage by the UI. It's fine
		# to be testing on the main thread.
		self.ignoreMessage( IECore.Msg.Level.Warning, "HistoryPath", "Path evaluated on unexpected thread" )

	def test( self ) :

		s = Gaffer.ScriptNode()

		s["testLight"] = GafferSceneTest.TestLight()

		s["lightFilter"] = GafferScene.PathFilter()
		s["lightFilter"]["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		s["tweaks"] = GafferScene.ShaderTweaks()
		s["tweaks"]["in"].setInput( s["testLight"]["out"] )
		s["tweaks"]["filter"].setInput( s["lightFilter"]["out"] )
		s["tweaks"]["shader"].setValue( "light" )

		exposureTweak = Gaffer.TweakPlug( "exposure", 2.0 )
		s["tweaks"]["tweaks"].addChild( exposureTweak )

		s["editScope"] = Gaffer.EditScope()
		s["editScope"].setup( s["tweaks"]["out"] )
		s["editScope"]["in"].setInput( s["tweaks"]["out"] )

		# Just the light
		inspector = self.__inspector( s["testLight"]["out"], "exposure" )

		with Gaffer.Context() as context :
			context["scene:path"] = IECore.InternedStringVectorData( ["light"] )
			historyPath = inspector.historyPath()

		self.assertIsInstance( historyPath, Gaffer.Path )

		self.assertFalse( historyPath.isLeaf() )
		self.assertTrue( historyPath.isValid() )
		self.assertEqual( len( historyPath ), 0 )

		c = historyPath.children()
		self.assertEqual( len( c ), 1 )
		self.assertTrue( c[0].isLeaf() )
		self.assertTrue( c[0].isValid() )
		self.assertEqual( c[0].property( "name" ), str( c[0][-1] ) )

		# Add tweaks
		inspector = self.__inspector( s["tweaks"]["out"], "exposure" )

		with Gaffer.Context() as context :
			context["scene:path"] = IECore.InternedStringVectorData( ["light"] )
			historyPath = inspector.historyPath()

		self.assertFalse( historyPath.isLeaf() )
		self.assertTrue( historyPath.isValid() )
		self.assertEqual( len( historyPath ), 0 )

		c = historyPath.children()
		self.assertEqual( len(c ), 2 )
		self.assertTrue( c[0].isLeaf() )
		self.assertTrue( c[0].isValid() )
		self.assertEqual( c[0].property( "name" ), str( c[0][-1] ) )
		self.assertTrue( c[1].isLeaf() )
		self.assertTrue( c[1].isValid() )
		self.assertEqual( c[1].property( "name" ), str( c[1][-1] ) )

		# Add an edit to the EditScope
		inspector = self.__inspector( s["editScope"]["out"], "exposure", s["editScope"] )

		with Gaffer.Context() as context :
			context["scene:path"] = IECore.InternedStringVectorData( ["light"] )
			edit = inspector.inspect().acquireEdit()
			edit["enabled"].setValue( True )
			edit["value"].setValue( 4.0 )
			historyPath = inspector.historyPath()

		self.assertFalse( historyPath.isLeaf() )
		self.assertTrue( historyPath.isValid() )
		self.assertEqual( len( historyPath ), 0 )

		c = historyPath.children()
		self.assertEqual( len( c ), 3 )
		self.assertTrue( c[0].isLeaf() )
		self.assertTrue( c[0].isValid() )
		self.assertEqual( c[0].property( "name" ), str( c[0][-1] ) )
		self.assertTrue( c[1].isLeaf() )
		self.assertTrue( c[1].isValid() )
		self.assertEqual( c[1].property( "name" ), str( c[1][-1] ) )
		self.assertTrue( c[2].isLeaf() )
		self.assertTrue( c[2].isValid() )
		self.assertEqual( c[2].property( "name" ), str( c[2][-1] ) )

		# Add a node + plug at the end of the graph that isn't parented to the script
		orphanNode = Gaffer.Node()
		orphanNode.addChild( GafferScene.ScenePlug( "orphanPlug", Gaffer.Plug.Direction.Out ) )
		orphanNode["orphanPlug"].setInput( s["editScope"]["out"])

		inspector = self.__inspector( orphanNode["orphanPlug"], "exposure" )

		with Gaffer.Context() as context :
			context["scene:path"] = IECore.InternedStringVectorData( ["light"] )
			historyPath = inspector.historyPath()

		self.assertFalse( historyPath.isLeaf() )
		self.assertTrue( historyPath.isValid() )
		self.assertEqual( len( historyPath ), 0 )

		c = historyPath.children()
		self.assertEqual( len( c ), 3 )
		self.assertTrue( c[0].isLeaf() )
		self.assertTrue( c[0].isValid() )
		self.assertEqual( c[0].property( "name" ), str( c[0][-1] ) )
		self.assertTrue( c[1].isLeaf() )
		self.assertTrue( c[1].isValid() )
		self.assertEqual( c[1].property( "name" ), str( c[1][-1] ) )
		self.assertTrue( c[2].isLeaf() )
		self.assertTrue( c[2].isValid() )
		self.assertEqual( c[2].property( "name" ), str( c[2][-1] ) )

	def testPropertyNames( self ) :

		s = Gaffer.ScriptNode()

		s["testLight"] = GafferSceneTest.TestLight()

		inspector = self.__inspector( s["testLight"]["out"], "exposure" )

		with Gaffer.Context() as context :
			context["scene:path"] = IECore.InternedStringVectorData( ["light"] )
			historyPath = inspector.historyPath()

		self.assertEqual(
			sorted( historyPath.propertyNames() ),
			sorted(
				[
					"fullName",
					"name",
				]
			)
		)

		self.assertEqual(
			sorted( historyPath.children()[0].propertyNames() ),
			sorted(
				[
					"fullName",
					"name",
					"history:value",
					"history:fallbackValue",
					"history:operation",
					"history:source",
					"history:editWarning",
					"history:node"
				]
			)
		)

	def testProperties( self ) :

		s = Gaffer.ScriptNode()

		s["testLight"] = GafferSceneTest.TestLight()

		s["lightFilter"] = GafferScene.PathFilter()
		s["lightFilter"]["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		s["tweaks"] = GafferScene.ShaderTweaks()
		s["tweaks"]["in"].setInput( s["testLight"]["out"] )
		s["tweaks"]["filter"].setInput( s["lightFilter"]["out"] )
		s["tweaks"]["shader"].setValue( "light" )

		exposureTweak = Gaffer.TweakPlug( "exposure", 2.0 )
		exposureTweak["mode"].setValue( Gaffer.TweakPlug.Mode.Add )
		s["tweaks"]["tweaks"].addChild( exposureTweak )

		s["editScope"] = Gaffer.EditScope()
		s["editScope"].setup( s["tweaks"]["out"] )
		s["editScope"]["in"].setInput( s["tweaks"]["out"] )

		inspector1 = self.__inspector( s["editScope"]["out"], "exposure", s["editScope"] )

		with Gaffer.Context() as context :
			context["scene:path"] = IECore.InternedStringVectorData( ["light"] )

			edit = inspector1.inspect().acquireEdit()
			edit["enabled"].setValue( True )
			edit["value"].setValue( 3.0 )

			historyPath = inspector1.historyPath()

		c = historyPath.children()

		self.assertEqual( c[0].property( "name" ), str( c[0][-1] ) )
		self.assertEqual( c[0].property( "history:node" ), s["testLight"] )
		self.assertEqual( c[0].property( "history:value" ), 0.0 )
		self.assertEqual( c[0].property( "history:fallbackValue" ), None )
		self.assertEqual( c[0].property( "history:operation" ), Gaffer.TweakPlug.Mode.Create )
		self.assertEqual( c[0].property( "history:source" ), s["testLight"]["parameters"]["exposure"] )
		self.assertEqual( c[0].property( "history:editWarning" ), "" )

		self.assertEqual( c[1].property( "name" ), str( c[1][-1] ) )
		self.assertEqual( c[1].property( "history:node" ), s["tweaks"] )
		self.assertEqual( c[1].property( "history:value" ), 2.0 )
		self.assertEqual( c[1].property( "history:fallbackValue" ), None )
		self.assertEqual( c[1].property( "history:operation" ), Gaffer.TweakPlug.Mode.Add )
		self.assertEqual( c[1].property( "history:source" ), exposureTweak )
		self.assertEqual( c[1].property( "history:editWarning" ), "" )

		self.assertEqual( c[2].property( "name" ), str( c[2][-1] ) )
		self.assertEqual( c[2].property( "history:node" ), s["editScope"]["LightEdits"]["ShaderTweaks"] )
		self.assertEqual( c[2].property( "history:value" ), 3.0 )
		self.assertEqual( c[2].property( "history:fallbackValue" ), None )
		self.assertEqual( c[2].property( "history:operation" ), Gaffer.TweakPlug.Mode.Replace )
		self.assertEqual( c[2].property( "history:source" ), edit )
		self.assertEqual( c[2].property( "history:editWarning" ), "" )

	def testCopy( self ) :

		s = Gaffer.ScriptNode()

		s["testLight"] = GafferSceneTest.TestLight()
		s["testLight"]["parameters"]["exposure"].setValue( 3.0 )

		inspector = self.__inspector( s["testLight"]["out"], "exposure" )

		with Gaffer.Context() as context :
			context["scene:path"] = IECore.InternedStringVectorData( ["light"] )
			historyPath = inspector.historyPath()

		self.assertEqual( historyPath.children()[0].property( "history:value" ), 3.0 )

		rootCopy = historyPath.copy()
		self.assertEqual( rootCopy.children()[0].property( "history:value" ), 3.0 )

		leafCopy = rootCopy.children()[0].copy()
		self.assertEqual( leafCopy.property( "history:node" ), s["testLight"] )
		self.assertEqual( leafCopy.property( "history:value" ), 3.0 )

	def testInvalidPath( self ) :

		s = Gaffer.ScriptNode()

		s["testLight"] = GafferSceneTest.TestLight()

		inspector = self.__inspector( s["testLight"]["out"], "exposure" )

		with Gaffer.Context() as context :
			context["scene:path"] = IECore.InternedStringVectorData( ["light"] )
			historyPath = inspector.historyPath()

		historyPath.setFromString( "/missingNode" )
		self.assertFalse( historyPath.isValid() )

	def testPlugClashing( self ) :

		s = Gaffer.ScriptNode()

		s["testLight"] = GafferSceneTest.TestLight()

		s["lightFilter"] = GafferScene.PathFilter()
		s["lightFilter"]["paths"].setValue( IECore.StringVectorData( ["light"] ) )

		s["loop"] = Gaffer.Loop()
		s["loop"].setup( s["testLight"]["out"] )
		s["loop"]["in"].setInput( s["testLight"]["out"] )

		s["tweaks"] = GafferScene.ShaderTweaks()
		s["tweaks"]["in"].setInput( s["loop"]["previous"] )
		s["tweaks"]["filter"].setInput( s["lightFilter"]["out"] )
		s["tweaks"]["shader"].setValue( "light" )

		exposureTweak = Gaffer.TweakPlug( "exposure", 1.0 )
		exposureTweak["mode"].setValue( Gaffer.TweakPlug.Mode.Add )
		s["tweaks"]["tweaks"].addChild( exposureTweak )

		s["loop"]["next"].setInput( s["tweaks"]["out"] )

		inspector = self.__inspector( s["loop"]["out"], "exposure" )

		with Gaffer.Context() as context :
			context["scene:path"] = IECore.InternedStringVectorData( ["light"] )
			historyPath = inspector.historyPath()

		self.assertEqual( len( historyPath.children() ), s["loop"]["iterations"].getValue() + 1 )
		self.assertEqual( historyPath.children()[0].property( "history:node" ), s["testLight"] )
		self.assertEqual( historyPath.children()[0].property( "history:value" ), 0 )
		for i in range( 1, s["loop"]["iterations"].getValue() + 1 ) :
			self.assertEqual( historyPath.children()[i].property( "history:node" ), s["tweaks"] )
			self.assertEqual( historyPath.children()[i].property( "history:value" ), i )

	def testTwoTweaksWithIdenticalSource( self ) :

		script = Gaffer.ScriptNode()

		script["light"] = GafferSceneTest.TestLight()

		script["lightFilter"] = GafferScene.PathFilter()
		script["lightFilter"]["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		script["tweaks1"] = GafferScene.ShaderTweaks()
		script["tweaks1"]["in"].setInput( script["light"]["out"] )
		script["tweaks1"]["filter"].setInput( script["lightFilter"]["out"] )
		script["tweaks1"]["shader"].setValue( "light" )
		script["tweaks1"]["tweaks"].addChild( Gaffer.TweakPlug( "exposure", 2.0 ) )

		script["tweaks2"] = GafferScene.ShaderTweaks()
		script["tweaks2"]["in"].setInput( script["tweaks1"]["out"] )
		script["tweaks2"]["filter"].setInput( script["lightFilter"]["out"] )
		script["tweaks2"]["shader"].setValue( "light" )
		script["tweaks2"]["tweaks"].addChild( Gaffer.TweakPlug( "exposure", 2.0 ) )
		script["tweaks2"]["tweaks"][0].setInput( script["tweaks1"]["tweaks"][0] )

		inspector = self.__inspector( script["tweaks2"]["out"], "exposure" )
		with Gaffer.Context() as context :
			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/light" )
			historyPath = inspector.historyPath()

		self.assertFalse( historyPath.isLeaf() )
		self.assertTrue( historyPath.isValid() )
		self.assertEqual( len( historyPath ), 0 )

		children = historyPath.children()
		self.assertEqual( len( children ), 3 )

		self.assertEqual(
			[ c.property( "history:node" ) for c in children ],
			[ script["light"], script["tweaks1"], script["tweaks2"] ]
		)

	def testEmptyHistory( self ) :

		s = Gaffer.ScriptNode()

		s["testLight"] = GafferSceneTest.TestLight()
		s["testLight"]["enabled"].setValue( False )

		inspector = self.__inspector( s["testLight"]["out"], "exposure" )

		with Gaffer.Context() as context :
			context["scene:path"] = IECore.InternedStringVectorData( ["light"] )
			historyPath = inspector.historyPath()

		self.assertEqual( len( historyPath.children() ), 0 )

	def testAttributeFallbackValues( self ) :

		s = Gaffer.ScriptNode()

		s["testLight"] = GafferSceneTest.TestLight()

		s["group"] = GafferScene.Group()
		s["group"]["in"][0].setInput( s["testLight"]["out"] )

		s["groupFilter"] = GafferScene.PathFilter()
		s["groupFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		s["tweaks"] = GafferScene.AttributeTweaks()
		s["tweaks"]["in"].setInput( s["group"]["out"] )
		s["tweaks"]["filter"].setInput( s["groupFilter"]["out"] )

		groupTextureResolutionTweak = Gaffer.TweakPlug( "gl:visualiser:maxTextureResolution", 1024 )
		groupTextureResolutionTweak["mode"].setValue( Gaffer.TweakPlug.Mode.Create )
		s["tweaks"]["tweaks"].addChild( groupTextureResolutionTweak )

		s["lightFilter"] = GafferScene.PathFilter()
		s["lightFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/light" ] ) )

		s["openGLAttributes"] = GafferScene.OpenGLAttributes()
		s["openGLAttributes"]["in"].setInput( s["tweaks"]["out"] )
		s["openGLAttributes"]["filter"].setInput( s["lightFilter"]["out"] )
		s["openGLAttributes"]["attributes"]["gl:visualiser:maxTextureResolution"]["enabled"].setValue( True )
		s["openGLAttributes"]["attributes"]["gl:visualiser:maxTextureResolution"]["value"].setValue( 1536 )

		inspector = GafferSceneUI.Private.AttributeInspector(
			s["openGLAttributes"]["out"], None, "gl:visualiser:maxTextureResolution",
		)

		with Gaffer.Context() as context :
			context["scene:path"] = IECore.InternedStringVectorData( [ "group", "light" ] )
			historyPath = inspector.historyPath()

		c = historyPath.children()

		self.assertEqual( c[0].property( "name" ), str( c[0][-1] ) )
		self.assertEqual( c[0].property( "history:node" ), s["openGLAttributes"] )
		self.assertEqual( c[0].property( "history:value" ), 1536 )
		self.assertEqual( c[0].property( "history:fallbackValue" ), 1024 )
		self.assertEqual( c[0].property( "history:operation" ), Gaffer.TweakPlug.Mode.Create )
		self.assertEqual( c[0].property( "history:source" ), s["openGLAttributes"]["attributes"]["gl:visualiser:maxTextureResolution"] )
		self.assertEqual( c[0].property( "history:editWarning" ), "Edits to \"gl:visualiser:maxTextureResolution\" may affect other locations in the scene." )

		s["openGLAttributes"]["enabled"].setValue( False )

		with Gaffer.Context() as context :
			context["scene:path"] = IECore.InternedStringVectorData( [ "group", "light" ] )
			historyPath = inspector.historyPath()

		c = historyPath.children()

		self.assertEqual( c[0].property( "name" ), str( c[0][-1] ) )
		self.assertEqual( c[0].property( "history:node" ), s["testLight"] )
		self.assertEqual( c[0].property( "history:value" ), None )
		self.assertEqual( c[0].property( "history:fallbackValue" ), 512 )
		self.assertEqual( c[0].property( "history:operation" ), Gaffer.TweakPlug.Mode.Create )
		self.assertEqual( c[0].property( "history:source" ), s["testLight"]["visualiserAttributes"]["maxTextureResolution"] )
		self.assertEqual( c[0].property( "history:editWarning" ), "" )

		# Disabling the openGLAttributes node results in its `visualiserMaxTextureResolution` plug remaining
		# in the history but providing no value. We'll be able to see the value set on /group as the fallback
		# value.
		self.assertEqual( c[1].property( "name" ), str( c[1][-1] ) )
		self.assertEqual( c[1].property( "history:node" ), s["openGLAttributes"] )
		self.assertEqual( c[1].property( "history:value" ), None )
		self.assertEqual( c[1].property( "history:fallbackValue" ), 1024 )
		self.assertEqual( c[1].property( "history:operation" ), Gaffer.TweakPlug.Mode.Create )
		self.assertEqual( c[1].property( "history:source" ), s["openGLAttributes"]["attributes"]["gl:visualiser:maxTextureResolution"] )
		self.assertEqual( c[1].property( "history:editWarning" ), "Edits to \"gl:visualiser:maxTextureResolution\" may affect other locations in the scene." )

	def testIsLeafAndIsValid( self ) :

		light = GafferSceneTest.TestLight()
		inspector = self.__inspector( light["out"], "exposure" )
		with Gaffer.Context() as context :
			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/light" )
			historyPath = inspector.historyPath()

		self.assertTrue( historyPath.isValid() )
		self.assertFalse( historyPath.isLeaf() )

		historyPath = historyPath.children()[0]
		self.assertTrue( historyPath.isValid() )
		self.assertTrue( historyPath.isLeaf() )

		historyPathDeeper = historyPath.copy()
		historyPathDeeper.append( "foo" )
		self.assertFalse( historyPathDeeper.isValid() )
		self.assertFalse( historyPathDeeper.isLeaf() )

		historyPathEdited = historyPath.copy()
		historyPathEdited[0] += "foo"
		self.assertFalse( historyPathEdited.isValid() )
		self.assertFalse( historyPathEdited.isLeaf() )

	def testNoPropertiesOnNonLeafPaths( self ) :

		light = GafferSceneTest.TestLight()
		inspector = self.__inspector( light["out"], "exposure" )
		with Gaffer.Context() as context :
			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/light" )
			historyPath = inspector.historyPath()

		self.assertIsNone( historyPath.property( "history:node" ) )

		historyPath = historyPath.children()[0]
		self.assertIsNotNone( historyPath.property( "history:node" ) )

		historyPathDeeper = historyPath.copy()
		historyPathDeeper.append( "foo" )
		self.assertIsNone( historyPathDeeper.property( "history:node" ) )

		historyPathEdited = historyPath.copy()
		historyPathEdited[0] += "foo"
		self.assertIsNone( historyPathEdited.property( "history:node" ) )

	def testInspectionIsDeferred( self ) :

		monitor = Gaffer.PerformanceMonitor()

		light = GafferSceneTest.TestLight()
		inspector = self.__inspector( light["out"], "exposure" )
		with Gaffer.Context() as context :
			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/light" )
			with monitor :
				historyPath = inspector.historyPath()

		self.assertEqual( len( monitor.allStatistics() ), 0 )

		with monitor :
			historyPath.children()

		self.assertGreaterEqual( len( monitor.allStatistics() ), 1 )

	def testCancellation( self ) :

		light = GafferSceneTest.TestLight()
		inspector = self.__inspector( light["out"], "exposure" )
		with Gaffer.Context() as context :
			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/light" )
			historyPath = inspector.historyPath()

		canceller = IECore.Canceller()
		canceller.cancel()

		with self.assertRaises( IECore.Cancelled ) :
			historyPath.children( canceller )

		historyPath.append( "0" )

		light["parameters"]["exposure"].setValue( 1 )
		with self.assertRaises( IECore.Cancelled ) :
			historyPath.propertyNames( canceller )

		with self.assertRaises( IECore.Cancelled ) :
			historyPath.property( "history:source", canceller )

	def testCancellationForEdit( self ) :

		# Make light with expression which loops infinitely unless cancelled.

		script = Gaffer.ScriptNode()
		script["light"] = GafferSceneTest.TestLight()

		HistoryPathTest.expressionStartedCondition = threading.Condition()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			import time
			import GafferSceneUITest.HistoryPathTest

			with GafferSceneUITest.HistoryPathTest.expressionStartedCondition :
				GafferSceneUITest.HistoryPathTest.expressionStartedCondition.notify()

			while True :
				time.sleep( 0.01 )
				IECore.Canceller.check( context.canceller() )

			parent["light"]["parameters"]["exposure"] = parent["light"]["parameters"]["intensity"]["r"] + 1
			"""
		) )

		inspector = self.__inspector( script["light"]["out"], "exposure" )
		with Gaffer.Context() as context :
			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/light" )
			historyPath = inspector.historyPath()

		# Start background task to evaluate `historyPath` and
		# wait till the expression starts.

		with self.expressionStartedCondition :
			backgroundTask = Gaffer.BackgroundTask(
				historyPath.cancellationSubject(),
				lambda canceller : historyPath.children( canceller )
			)
			self.expressionStartedCondition.wait()

		# Make an edit to the script. This must cancel the background task
		# before it can go ahead.

		script["light"]["parameters"]["intensity"]["r"].setValue( 2 )
		backgroundTask.wait()
		self.assertEqual( backgroundTask.status(), backgroundTask.Status.Cancelled )

	def testSceneReader( self ) :

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( "${GAFFER_ROOT}/python/GafferSceneTest/usdFiles/sphereLight.usda" )

		inspector = self.__inspector( reader["out"], "exposure" )
		with Gaffer.Context() as context :
			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/SpotLight23" )
			historyPath = inspector.historyPath()

		self.assertEqual(
			[ c.property( "history:node" ) for c in historyPath.children() ],
			[ reader ]
		)

if __name__ == "__main__":
	unittest.main()
