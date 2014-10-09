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

	def _createRenderer( self ) :

		fileName = self.__fileName()
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

		# enable all visibility types - maybe this is something which'll
		# get dealt with using attributes at the root level at some point.
		renderer.setAttribute( "ri:visibility:camera", IECore.BoolData( True ) )
		renderer.setAttribute( "ri:visibility:transmission", IECore.BoolData( True ) )
		renderer.setAttribute( "ri:visibility:diffuse", IECore.BoolData( True ) )
		renderer.setAttribute( "ri:visibility:specular", IECore.BoolData( True ) )
		renderer.setAttribute( "ri:visibility:photon", IECore.BoolData( True ) )

		scriptNode = scenePlug.node().scriptNode()

		pythonString = "IECoreRI.executeProcedural( 'gaffer/script', 1, [ '-fileName', '%s', '-node', '%s', '-frame', '%f' ] )" % (
			scriptNode["fileName"].getValue(),
			scenePlug.node().relativeName( scriptNode ),
			Gaffer.Context.current().getFrame()
		)

		dynamicLoadCommand = "Procedural \"DynamicLoad\" [ \"iePython\" \"%s\" ] [ -1e30 1e30 -1e30 1e30 -1e30 1e30 ]\n" % pythonString

		renderer.command(
			"ri:archiveRecord",
			{
				"type" : "verbatim",
				"record" : dynamicLoadCommand
			}
		)

	def _command( self ) :

		if self["mode"].getValue() != "render" :
			return ""
		
		result = self["command"].getValue()
		result = Gaffer.Context.current().substitute( result ) ## \todo See __fileName()
		result = result.strip()
		if result == "" :
			return
		
		result += " '" + self.__fileName() + "'"
		
		return result
		
	def __fileName( self ) :

		result = self["ribFileName"].getValue()
		# because execute() isn't called inside a compute(), we
		# don't get string expansions automatically, and have to
		# do them ourselves.
		## \todo Can we improve this situation?
		result = Gaffer.Context.current().substitute( result )
		return result

IECore.registerRunTimeTyped( RenderManRender, typeName = "GafferRenderMan::RenderManRender" )
