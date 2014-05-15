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

class SceneProceduralTest( unittest.TestCase ) :

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

		with IECore.WorldBlock( renderer ) :
		
			procedural = GafferScene.SceneProcedural( badNode["out"], Gaffer.Context(), "/" )
			self.__WrappingProcedural( procedural ).render( renderer )
	
	def testPythonComputationErrors( self ) :
	
		# As above, this may be an IECoreGL bug, but again it's important that
		# Gaffer doesn't trigger it.
		
		script = Gaffer.ScriptNode()
		script["plane"] = GafferScene.Plane()
		
		script["expression"] = Gaffer.Expression()
		script["expression"]["engine"].setValue( "python" )
		script["expression"]["expression"].setValue( 'parent["plane"]["transform"]["translate"]["x"] = iDontExist["andNorDoI"]' )
				
		renderer = IECoreGL.Renderer()
		renderer.setOption( "gl:mode", IECore.StringData( "deferred" ) )

		with IECore.WorldBlock( renderer ) :
		
			procedural = GafferScene.SceneProcedural( script["plane"]["out"], Gaffer.Context(), "/" )
			self.__WrappingProcedural( procedural ).render( renderer )
	
	def testMotionBlurredBounds( self ) :
	
		script = Gaffer.ScriptNode()
		
		script["plane"] = GafferScene.Plane()
		
		script["expression1"] = Gaffer.Expression()
		script["expression1"]["engine"].setValue( "python" )
		script["expression1"]["expression"].setValue( 'parent["plane"]["transform"]["translate"]["x"] = context.getFrame()' )
		
		script["expression2"] = Gaffer.Expression()
		script["expression2"]["engine"].setValue( "python" )
		script["expression2"]["expression"].setValue( 'parent["plane"]["dimensions"]["x"] = 1 + context.getFrame()' )
				
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
			
if __name__ == "__main__":
	unittest.main()
