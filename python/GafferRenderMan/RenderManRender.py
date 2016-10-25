##########################################################################
#
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

import os
import shlex
import subprocess32 as subprocess

import IECore
import IECoreRI

import Gaffer
import GafferScene

class RenderManRender( GafferScene.ExecutableRender ) :

	def __init__( self, name="RenderManRender" ) :

		GafferScene.ExecutableRender.__init__( self, name )

		self.addChild(
			Gaffer.StringPlug(
				"mode",
				Gaffer.Plug.Direction.In,
				"render",
			)
		)

		self.addChild(
			Gaffer.StringPlug(
				"ribFileName",
			)
		)

		self.addChild(
			Gaffer.StringPlug(
				"command",
				defaultValue = "renderdl",
			)
		)

	def execute( self ) :

		GafferScene.ExecutableRender.execute( self )

		if self["mode"].getValue() != "render" :
			return

		command = self["command"].getValue().strip()
		if not command :
			return

		args = shlex.split( command )
		args.append( self["ribFileName"].getValue() )

		subprocess.check_call( args )

	def _createRenderer( self ) :

		fileName = self["ribFileName"].getValue()
		directory = os.path.dirname( fileName )
		if directory :
			try :
				os.makedirs( directory )
			except OSError :
				# makedirs very unhelpfully raises an exception if
				# the directory already exists, but it might also
				# raise if it fails. we reraise only in the latter case.
				if not os.path.isdir( directory ) :
					raise

		renderer = IECoreRI.Renderer( fileName )
		renderer.setOption( "ri:frame", int( Gaffer.Context.current().getFrame() ) )

		return renderer

	def _outputWorldProcedural( self, scenePlug, renderer ) :

		# Enable all visibility types - maybe this is something which'll
		# get dealt with using attributes at the root level at some point.
		renderer.setAttribute( "ri:visibility:camera", IECore.BoolData( True ) )
		renderer.setAttribute( "ri:visibility:transmission", IECore.BoolData( True ) )
		renderer.setAttribute( "ri:visibility:diffuse", IECore.BoolData( True ) )
		renderer.setAttribute( "ri:visibility:specular", IECore.BoolData( True ) )
		renderer.setAttribute( "ri:visibility:photon", IECore.BoolData( True ) )

		# Create the ScriptProcedural that we want to load at render time.
		scriptNode = scenePlug.node().scriptNode()
		scriptContext = scriptNode.context()
		currentContext = Gaffer.Context.current()

		procedural = GafferScene.ScriptProcedural()
		procedural["fileName"].setTypedValue( scriptNode["fileName"].getValue() )
		procedural["node"].setTypedValue( scenePlug.node().relativeName( scriptNode ) )
		procedural["frame"].setNumericValue( currentContext.getFrame() )

		# In practice when using the raytrace hider, 3delight always expands
		# all procedurals before rendering begins, so computing bounds is
		# a waste of time.
		globals = scenePlug["globals"].getValue()
		computeBound = True
		with IECore.IgnoredExceptions( KeyError ) :
			if globals["option:ri:hider"].value == "raytrace" :
				computeBound = False
		procedural["computeBound"].setTypedValue( computeBound )

		contextArgs = IECore.StringVectorData()
		for entry in [ k for k in currentContext.keys() if k != "frame" and not k.startswith( "ui:" ) ] :
			if entry not in scriptContext.keys() or currentContext[entry] != scriptContext[entry] :
				contextArgs.extend( [
					"-" + entry,
					 repr( currentContext[entry] )
				] )

		procedural["context"].setValue( contextArgs )

		# Output an ExternalProcedural that will load the ScriptProcedural.
		pythonString = "IECoreRI.executeProcedural( \"gaffer/script\", 1, %s )" % str( IECore.ParameterParser().serialise( procedural.parameters(), procedural.parameters().getValue() ) )
		externalProcedural = IECore.Renderer.ExternalProcedural(
			"iePython",
			IECore.Box3f( IECore.V3f( -1e30 ), IECore.V3f( 1e30 ) ) if computeBound else IECore.Renderer.Procedural.noBound,
			{
				"ri:data" : pythonString,
			}
		)
		renderer.procedural( externalProcedural )

IECore.registerRunTimeTyped( RenderManRender, typeName = "GafferRenderMan::RenderManRender" )
