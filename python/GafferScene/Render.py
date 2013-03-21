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

import subprocess

import IECore

import Gaffer
import GafferScene

class Render( Gaffer.Node ) :

	def __init__( self, name="Render" ) :
	
		Gaffer.Node.__init__( self, name )
	
		self.addChild(
			GafferScene.ScenePlug(
				"in"
			)
		)
				
	def execute( self ) :
	
		renderer = self._createRenderer()
	
		# output globals
				
		scenePlug = self["in"].getInput()
		globals = scenePlug["globals"].getValue()
				
		for name, value in globals.items() :
			if isinstance( value, IECore.PreWorldRenderable ) :
				value.render( renderer )
			elif isinstance( value, IECore.Data ) :
				renderer.setOption( name, value )
		
		# figure out the shutter
		
		cameraBlur = globals.get( "render:cameraBlur", None )
		cameraBlur = cameraBlur.value if cameraBlur else False
		transformBlur = globals.get( "render:transformBlur", None )
		transformBlur = transformBlur.value if transformBlur else False
		deformationBlur = globals.get( "render:deformationBlur", None )
		deformationBlur = deformationBlur.value if deformationBlur else False
		
		frame = Gaffer.Context.current().getFrame()
		if cameraBlur or transformBlur or deformationBlur :
			shutter = globals.get( "render:shutter", None )
			shutter = shutter.value if shutter else IECore.V2f( -0.25, 0.25 )
			shutter = IECore.V2f( frame ) + shutter
		else :
			shutter = IECore.V2f( frame, frame )	
			
		# output the camera
			
		self.__outputCamera( scenePlug, globals, shutter, cameraBlur, renderer )
		
		# output the world
										
		with IECore.WorldBlock( renderer ) :
		
			scriptNode = self.ancestor( Gaffer.ScriptNode.staticTypeId() )
			scriptNode.save()			
			
			self.__outputLights( scenePlug, globals, renderer )
			
			procedural = GafferScene.ScriptProcedural()
			procedural["fileName"].setTypedValue( scriptNode["fileName"].getValue() )
			procedural["node"].setTypedValue( scenePlug.node().relativeName( scriptNode ) )
			procedural["frame"].setNumericValue( frame )
			
			# avoid having to compute an accurate bound taking into account motion
			# blur by just having a huge bound - we know we want to render the
			# contents of the procedural (it's all we have to render), and the procedural
			# will accurately bound itself once it's called by the renderer anyway.
			bound = IECore.Box3f( IECore.V3f( -1e30 ), IECore.V3f( 1e30 ) )
			
			with IECore.AttributeBlock( renderer ) :
			
				renderer.setAttribute(
					"name",
					IECore.StringData(
						self.relativeName(
							self.ancestor( Gaffer.ScriptNode.staticTypeId() )
						)
					)
				)
				
				self._outputProcedural( procedural, bound, renderer )
			
		commandAndArgs = self._commandAndArgs()
		if commandAndArgs :
			self.__launchExternalRender( commandAndArgs )
		
	def _createRenderer( self ) :
	
		raise NotImplementedError
			
	def _outputProcedural( self, procedural, bound, renderer ) :
	
		## \todo We need this function because Cortex has no mechanism for getting
		# a delayed load procedural into a rib or ass file. We should consider how
		# that should be done. In an ideal world the ParameterisedProcedural would
		# just do it magically somehow when rendered to a Renderer generating a
		# scene file.
		
		raise NotImplementedError
	
	def _commandLineAndArgs( self ) :
	
		raise NotImplementedError
		
	def __launchExternalRender( self, commandAndArgs ) :
	
		p = subprocess.Popen( commandAndArgs )
		
		applicationRoot = self.ancestor( Gaffer.ApplicationRoot.staticTypeId() )
		if applicationRoot is None or applicationRoot.getName() != "gui" :
			p.wait()
	
	def __outputCamera( self, scenePlug, globals, shutter, blur, renderer ) :

		# get the camera
		
		cameraPath = globals.get( "render:camera", None )
		
		camera = None
		if cameraPath is not None :
			
			cameraObject = scenePlug.object( cameraPath.value )
			if isinstance( cameraObject, IECore.Camera ) :
				camera = cameraObject
			
			camera.setTransform( self.__transform( scenePlug, cameraPath.value, shutter, blur ) )
			
		if camera is None :
			camera = IECore.Camera()
		
		# apply the resolution
			
		resolution = globals.get( "render:resolution", None )
		if resolution is not None :
			camera.parameters()["resolution"] = resolution
			
		camera.addStandardParameters()
		
		# apply the shutter
				
		camera.parameters()["shutter"] = shutter
	
		# actually output the camera to the renderer
			
		camera.render( renderer )
	
	def __outputLights( self, scenePlug, globals, renderer ) :
	
		if "gaffer:forwardDeclarations" not in globals :
			return
	
		for path, declaration in globals["gaffer:forwardDeclarations"].items() :
			if declaration["type"].value == IECore.TypeId.Light :
				
				attributes = scenePlug.fullAttributes( path )
				visibility = attributes.get( "gaffer:visibility", None )
				if visibility is not None and not visibility.value :
					continue
				
				transform = scenePlug.fullTransform( path )
				light = scenePlug.object( path )
				light.handle = path
				
				with IECore.AttributeBlock( renderer ) :
					
					for key, value in attributes.items() :
						if isinstance( value, IECore.Data ) :
							renderer.setAttribute( key, value )

					renderer.concatTransform( transform )
					light.render( renderer )
				
				renderer.illuminate( light.handle, True )
	
	def __transform( self, scenePlug, path, shutter, blur = False ) :
		
		numSamples = 1
		if blur :
			attributes = scenePlug.fullAttributes( path )
			transformBlurSegments = attributes.get( "gaffer:transformBlurSegments", None )
			numSamples = transformBlurSegments.value + 1 if transformBlurSegments else 2
			transformBlur = attributes.get( "gaffer:transformBlur", None )
			if transformBlur is not None and not transformBlur.value :
				numSamples = 1
			
		result = IECore.MatrixMotionTransform()
		with Gaffer.Context( Gaffer.Context.current() ) as transformContext :
			for i in range( 0, numSamples ) :
				frame = shutter[0] + ( shutter[1] - shutter[0] ) * float( i ) / max( 1, numSamples - 1 )
				transformContext.setFrame( frame )
				result[frame] = scenePlug.fullTransform( path )
		
		return result
			
IECore.registerRunTimeTyped( Render )
