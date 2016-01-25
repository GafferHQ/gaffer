##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import gc

import IECore
import IECoreGL

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class SceneProceduralTest( GafferSceneTest.SceneTestCase ) :

	class __WrappingProcedural( IECore.ParameterisedProcedural ) :

		def __init__( self, procedural ) :

			IECore.ParameterisedProcedural.__init__( self, "" )

			self.__procedural = procedural

		def doBound( self, args ) :

			return self.__procedural.bound()

		def doRender( self, renderer, args ) :

			renderer.procedural( self.__procedural )

	def testComputationErrors( self ) :

		# This test actually exposed a crash bug in IECoreGL, but it's important
		# that Gaffer isn't susceptible to triggering that bug.

		badNode = GafferScene.Text()
		badNode["font"].setValue( "iDontExist" )

		renderer = IECoreGL.Renderer()
		renderer.setOption( "gl:mode", IECore.StringData( "deferred" ) )

		with IECore.CapturingMessageHandler() as mh :

			with IECore.WorldBlock( renderer ) :

				procedural = GafferScene.SceneProcedural( badNode["out"], Gaffer.Context(), "/" )
				self.__WrappingProcedural( procedural ).render( renderer )

		self.assertTrue( len( mh.messages ) )
		self.assertTrue( "Unable to find font" in mh.messages[0].message )

	def testPythonComputationErrors( self ) :

		# As above, this may be an IECoreGL bug, but again it's important that
		# Gaffer doesn't trigger it.

		script = Gaffer.ScriptNode()
		script["plane"] = GafferScene.Plane()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( 'parent["plane"]["transform"]["translate"]["x"] = iDontExist["andNorDoI"]' )

		renderer = IECoreGL.Renderer()
		renderer.setOption( "gl:mode", IECore.StringData( "deferred" ) )

		with IECore.CapturingMessageHandler() as mh :

			with IECore.WorldBlock( renderer ) :

				procedural = GafferScene.SceneProcedural( script["plane"]["out"], Gaffer.Context(), "/" )
				self.__WrappingProcedural( procedural ).render( renderer )

		self.assertTrue( len( mh.messages ) )
		self.assertTrue( "iDontExist" in mh.messages[0].message )

	def testMotionBlurredBounds( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()

		script["expression1"] = Gaffer.Expression()
		script["expression1"].setExpression( 'parent["plane"]["transform"]["translate"]["x"] = context.getFrame()' )

		script["expression2"] = Gaffer.Expression()
		script["expression2"].setExpression( 'parent["plane"]["dimensions"]["x"] = 1 + context.getFrame()' )

		script["options"] = GafferScene.StandardOptions()
		script["options"]["in"].setInput( script["plane"]["out"] )

		for path, frame, bound in [
			( "/plane", 1, IECore.Box3f( IECore.V3f( 0, -.5, 0 ), IECore.V3f( 2, .5, 0 ) ) ),
			( "/plane", 2, IECore.Box3f( IECore.V3f( 0.5, -.5, 0 ), IECore.V3f( 3.5, .5, 0 ) ) ),
		] :
			context = Gaffer.Context()
			context.setFrame( frame )
			procedural = GafferScene.SceneProcedural( script["options"]["out"], context, path )
			self.assertEqual( procedural.bound(), bound )

		script["options"]["options"]["transformBlur"]["enabled"].setValue( True )
		script["options"]["options"]["transformBlur"]["value"].setValue( True )
		script["options"]["options"]["deformationBlur"]["enabled"].setValue( True )
		script["options"]["options"]["deformationBlur"]["value"].setValue( True )
		script["options"]["options"]["shutter"]["enabled"].setValue( True )
		script["options"]["options"]["shutter"]["value"].setValue( IECore.V2f( 0, 1 ) )

		for path, frame, bound in [
			( "/plane", 1, IECore.Box3f( IECore.V3f( 0, -.5, 0 ), IECore.V3f( 3.5, .5, 0 ) ) ),
			( "/plane", 2, IECore.Box3f( IECore.V3f( 0.5, -.5, 0 ), IECore.V3f( 5, .5, 0 ) ) ),
		] :
			context = Gaffer.Context()
			context.setFrame( frame )
			procedural = GafferScene.SceneProcedural( script["options"]["out"], context, path )
			self.assertEqual( procedural.bound(), bound )

	def testScriptNodeDeletion( self ) :

		# In certain circumstances, there may be no external references to the script node during a render,
		# meaning the scene procedural must hold a reference to it. Lets check this works...

		script = Gaffer.ScriptNode()
		script["plane"] = GafferScene.Plane()

		renderer = IECore.CapturingRenderer()

		with IECore.WorldBlock( renderer ) :

			procedural = GafferScene.SceneProcedural( script["plane"]["out"], Gaffer.Context(), "/" )

			del script

			while gc.collect() :
				pass
			IECore.RefCounted.collectGarbage()

			self.__WrappingProcedural( procedural ).render( renderer )

		# if all is well, the capturing renderer should have generated a plane innit.
		# lets check this:

		def findMesh( g ):
			if isinstance( g, IECore.MeshPrimitive ):
				return g
			elif isinstance( g, IECore.Group ):
				if len( g.children() ) == 0:
					return None
				return findMesh( g.children()[0] )
			return None

		self.assertNotEqual( findMesh( renderer.world() ), None )

	def testAllRenderedSignal( self ) :

		class AllRenderedTest( object ) :
			allRenderedSignalCalled = False
			def allRendered( self ):
				self.allRenderedSignalCalled = True

		script = Gaffer.ScriptNode()
		script["plane"] = GafferScene.Plane()

		# test creating/deleting a single procedural:
		t = AllRenderedTest()
		allRenderedConnection = GafferScene.SceneProcedural.allRenderedSignal().connect( t.allRendered )

		procedural = GafferScene.SceneProcedural( script["plane"]["out"], Gaffer.Context(), "/" )
		self.assertEqual( t.allRenderedSignalCalled, False )
		del procedural
		self.assertEqual( t.allRenderedSignalCalled, True )

		# create/delete two of 'em:
		t = AllRenderedTest()
		allRenderedConnection = GafferScene.SceneProcedural.allRenderedSignal().connect( t.allRendered )
		procedural1 = GafferScene.SceneProcedural( script["plane"]["out"], Gaffer.Context(), "/" )
		procedural2 = GafferScene.SceneProcedural( script["plane"]["out"], Gaffer.Context(), "/" )

		self.assertEqual( t.allRenderedSignalCalled, False )
		del procedural1
		self.assertEqual( t.allRenderedSignalCalled, False )
		del procedural2
		self.assertEqual( t.allRenderedSignalCalled, True )


		# now actually render them:
		renderer = IECore.CapturingRenderer()
		t = AllRenderedTest()
		allRenderedConnection = GafferScene.SceneProcedural.allRenderedSignal().connect( t.allRendered )
		procedural1 = GafferScene.SceneProcedural( script["plane"]["out"], Gaffer.Context(), "/" )
		procedural2 = GafferScene.SceneProcedural( script["plane"]["out"], Gaffer.Context(), "/" )

		self.assertEqual( t.allRenderedSignalCalled, False )
		with IECore.WorldBlock( renderer ) :
			renderer.procedural( procedural1 )

		self.assertEqual( t.allRenderedSignalCalled, False )
		with IECore.WorldBlock( renderer ) :
			renderer.procedural( procedural2 )

		self.assertEqual( t.allRenderedSignalCalled, True )

		# now render one and delete one:
		renderer = IECore.CapturingRenderer()
		t = AllRenderedTest()
		allRenderedConnection = GafferScene.SceneProcedural.allRenderedSignal().connect( t.allRendered )
		procedural1 = GafferScene.SceneProcedural( script["plane"]["out"], Gaffer.Context(), "/" )
		procedural2 = GafferScene.SceneProcedural( script["plane"]["out"], Gaffer.Context(), "/" )

		self.assertEqual( t.allRenderedSignalCalled, False )
		del procedural1
		self.assertEqual( t.allRenderedSignalCalled, False )
		with IECore.WorldBlock( renderer ) :
			renderer.procedural( procedural2 )

		self.assertEqual( t.allRenderedSignalCalled, True )

	def testTransformBlurAttributeScope( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		script["sphere"]["type"].setValue( GafferScene.Sphere.Type.Primitive )

		script["expression1"] = Gaffer.Expression()
		script["expression1"].setExpression( 'parent["sphere"]["transform"]["translate"]["x"] = context.getFrame()' )

		script["filter"] = GafferScene.PathFilter()
		script["filter"]["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		script["attributes"] = GafferScene.StandardAttributes()
		script["attributes"]["in"].setInput( script["sphere"]["out"] )
		script["attributes"]["filter"].setInput( script["filter"]["out"] )
		script["attributes"]["attributes"]["transformBlur"]["enabled"].setValue( True )

		script["options"] = GafferScene.StandardOptions()
		script["options"]["in"].setInput( script["attributes"]["out"] )
		script["options"]["options"]["transformBlur"]["enabled"].setValue( True )
		script["options"]["options"]["transformBlur"]["value"].setValue( True )
		script["options"]["options"]["shutter"]["enabled"].setValue( True )
		script["options"]["options"]["shutter"]["value"].setValue( IECore.V2f( -0.5, 0.5 ) )

		sphereBound = IECore.Box3f( IECore.V3f( -1 ), IECore.V3f( 1 ) )
		velocity = IECore.V3f( 1, 0, 0 )

		context = Gaffer.Context()
		for frame in range( 0, 10 ) :
			for transformBlur in ( False, True ) :

				context.setFrame( frame )
				script["attributes"]["attributes"]["transformBlur"]["value"].setValue( transformBlur )

				procedural = GafferScene.SceneProcedural( script["options"]["out"], context, "/sphere" )
				bound = procedural.bound()
				if transformBlur :
					self.assertEqual( bound, IECore.Box3f( sphereBound.min + velocity * ( frame - 0.5 ), sphereBound.max + velocity * ( frame + 0.5 ) ) )
				else :
					self.assertEqual( bound, IECore.Box3f( sphereBound.min + velocity * frame, sphereBound.max + velocity * frame ) )

	def testComputeBound( self ) :

		script = Gaffer.ScriptNode()
		script["p"] = GafferScene.Plane()

		proc1 = GafferScene.SceneProcedural( script["p"]["out"], script.context(), "/" )
		proc2 = GafferScene.SceneProcedural( script["p"]["out"], script.context(), "/", computeBound = False )

		self.assertEqual( proc1.bound(), script["p"]["out"].bound( "/" ) )
		self.assertEqual( proc2.bound(), IECore.Renderer.Procedural.noBound )

if __name__ == "__main__":
	unittest.main()
