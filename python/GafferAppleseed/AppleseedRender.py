##########################################################################
#
#  Copyright (c) 2014, Esteban Tovagliari. All rights reserved.
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
import IECoreAppleseed

import Gaffer
import GafferScene

class AppleseedRender( GafferScene.ExecutableRender ) :

	def __init__( self, name="AppleseedRender" ) :

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
			Gaffer.StringPlug(
				"verbosity",
				Gaffer.Plug.Direction.In,
				"warning",
			)
		)

	def _makeDir( self, directory ) :
		try :
			os.makedirs( directory )
		except OSError :
			# makedirs very unhelpfully raises an exception if
			# the directory already exists, but it might also
			# raise if it fails. we reraise only in the latter case.
			if not os.path.isdir( directory ) :
				raise

	def _createRenderer( self ) :

		fileName = self["fileName"].getValue()
		directory = os.path.dirname( fileName )
		if directory :
			self._makeDir( directory )

		renderer = IECoreAppleseed.Renderer( fileName )
		return renderer

	def _outputWorldProcedural( self, scenePlug, renderer ) :

		# Since Appleseed doesn't yet support deferred-load procedurals, we just
		# output the entire scene immediately rather than output a ScriptProcedural.
		GafferScene.SceneProcedural( scenePlug, Gaffer.Context().current(), "/" ).render( renderer )

	def _command( self ) :
		if self["mode"].getValue() == "render" :
			return "appleseed.cli --message-verbosity %s -c final '%s'" % ( self["verbosity"].getValue(), self["fileName"].getValue() )

		return ""

IECore.registerRunTimeTyped( AppleseedRender, typeName = "GafferAppleseed::AppleseedRender" )
