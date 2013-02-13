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
				
		scenePlug = self["in"].getInput()
		globals = scenePlug["globals"].getValue()
				
		for name, value in globals.items() :
			if isinstance( value, IECore.PreWorldRenderable ) :
				value.render( renderer )
			elif isinstance( value, IECore.Data ) :
				renderer.setOption( name, value )
		
		if "gaffer:renderCamera" in globals :
			self.__outputCamera( scenePlug, globals["gaffer:renderCamera"].value, renderer )
										
		with IECore.WorldBlock( renderer ) :
		
			scriptNode = self.ancestor( Gaffer.ScriptNode.staticTypeId() )
			scriptNode.save()			
			
			procedural = GafferScene.ScriptProcedural()
			procedural["fileName"].setTypedValue( scriptNode["fileName"].getValue() )
			procedural["node"].setTypedValue( scenePlug.node().relativeName( scriptNode ) )
			
			bound = scenePlug.bound( "/" )
			bound = bound.transform( scenePlug.transform( "/" ) )
			
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
	
	def __outputCamera( self, scenePlug, cameraPath, renderer ) :
				
		camera = None
		if cameraPath :
			o = scenePlug.object( cameraPath )
			if isinstance( o, IECore.Camera ) :
				camera = o
				
		if not camera :
			## \todo We shouldn't need to do this but I don't think IECoreArnold is
			# setting a default camera as expected.
			camera = IECore.Camera()
			camera.addStandardParameters()		
			camera.render( renderer )
			return
		
		with IECore.TransformBlock( renderer ) :
			renderer.concatTransform( scenePlug.fullTransform( cameraPath ) )
			camera.render( renderer )
			
IECore.registerRunTimeTyped( Render )
