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

import unittest
import threading
import imath

import IECore

import Gaffer
import GafferTest
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
		self.assertEqual( c[0].property( "history:operation" ), Gaffer.TweakPlug.Mode.Create )
		self.assertEqual( c[0].property( "history:source" ), s["testLight"]["parameters"]["exposure"] )
		self.assertEqual( c[0].property( "history:editWarning" ), "" )

		self.assertEqual( c[1].property( "name" ), str( c[1][-1] ) )
		self.assertEqual( c[1].property( "history:node" ), s["tweaks"] )
		self.assertEqual( c[1].property( "history:value" ), 2.0 )
		self.assertEqual( c[1].property( "history:operation" ), Gaffer.TweakPlug.Mode.Add )
		self.assertEqual( c[1].property( "history:source" ), exposureTweak )
		self.assertEqual( c[1].property( "history:editWarning" ), "" )

		self.assertEqual( c[2].property( "name" ), str( c[2][-1] ) )
		self.assertEqual( c[2].property( "history:node" ), s["editScope"]["LightEdits"]["ShaderTweaks"] )
		self.assertEqual( c[2].property( "history:value" ), 3.0 )
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

	def testEmptyHistory( self ) :

		s = Gaffer.ScriptNode()

		s["testLight"] = GafferSceneTest.TestLight()
		s["testLight"]["enabled"].setValue( False )

		inspector = self.__inspector( s["testLight"]["out"], "exposure" )

		with Gaffer.Context() as context :
			context["scene:path"] = IECore.InternedStringVectorData( ["light"] )
			historyPath = inspector.historyPath()

		self.assertEqual( len( historyPath.children() ), 0 )


if __name__ == "__main__":
	unittest.main()
