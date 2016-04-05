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

import os

import IECore
import IECoreArnold

import Gaffer
import GafferScene

class ArnoldRender( GafferScene.ExecutableRender ) :

	def __init__( self, name="ArnoldRender" ) :

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
				"fileName",
			)
		)

		self.addChild(
			Gaffer.IntPlug(
				"verbosity",
				Gaffer.Plug.Direction.In,
				2
			)
		)

	def _createRenderer( self ) :

		fileName = self["fileName"].getValue()
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

		renderer = IECoreArnold.Renderer( fileName )
		renderer.setOption( "ai:procedural_searchpath", os.path.expandvars( "$GAFFER_ROOT/arnold/procedurals" ) )

		return renderer

	def _outputWorldProcedural( self, scenePlug, renderer ) :

		# Create the ScriptProcedural that we want to load at render time.
		scriptNode = scenePlug.node().scriptNode()
		scriptContext = scriptNode.context()
		currentContext = Gaffer.Context.current()

		procedural = GafferScene.ScriptProcedural()
		procedural["fileName"].setTypedValue( scriptNode["fileName"].getValue() )
		procedural["node"].setTypedValue( scenePlug.node().relativeName( scriptNode ) )
		procedural["frame"].setNumericValue( currentContext.getFrame() )
		## \todo Determine an appropriate value for the "computeBounds" parameter.
		# In theory we might see startup time improvements if we turned it off as
		# we do for 3delight. But on the other hand turning off bounds computation
		# makes IECoreArnold use load_at_init which by default serialises procedural
		# expansion (in theory the parallel_node_init option could paralellise that
		# again). But since Arnold properly expands procedurals only when they are
		# hit by a ray, perhaps we're actually better off computing accurate bounds
		# in the hope that not everything will be expanded. The only reason it's a
		# definite win to turn it off in 3delight is because everything is going to
		# be expanded anyway.

		contextArgs = IECore.StringVectorData()
		for entry in [ k for k in currentContext.keys() if k != "frame" and not k.startswith( "ui:" ) ] :
			if entry not in scriptContext.keys() or currentContext[entry] != scriptContext[entry] :
				contextArgs.extend( [
					"-" + entry,
					 repr( currentContext[entry] )
				] )

		procedural["context"].setValue( contextArgs )

		# Output an ExternalProcedural that will load the ScriptProcedural.

		externalProcedural = IECore.Renderer.ExternalProcedural(
			"ieProcedural.so",
			IECore.Renderer.Procedural.noBound,
			{
				"className" : "gaffer/script",
				"classVersion" : 1,
				"parameterValues" : IECore.StringVectorData(
					IECore.ParameterParser().serialise( procedural.parameters(), procedural.parameters().getValue() )
				)
			}
		)

		renderer.procedural( externalProcedural )

	def _command( self ) :

		fileName = self["fileName"].getValue()

		mode = self["mode"].getValue()
		if mode == "render" :
			return "kick -dp -dw -v %d '%s'" % ( self["verbosity"].getValue(), fileName )
		elif mode == "expand" :
			return "kick -v %d -forceexpand -resave '%s' '%s'" % ( self["verbosity"].getValue(), fileName, fileName )

		return ""

IECore.registerRunTimeTyped( ArnoldRender, typeName = "GafferArnold::ArnoldRender" )
