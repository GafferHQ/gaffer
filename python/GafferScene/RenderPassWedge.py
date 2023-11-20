##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

import IECore

import Gaffer
import GafferDispatch
import GafferScene

class RenderPassWedge( GafferDispatch.TaskContextProcessor ) :

	def __init__( self, name = "RenderPassWedge" ) :

		GafferDispatch.TaskContextProcessor.__init__( self, name )

		self["in"] = GafferScene.ScenePlug()
		self["out"] = GafferScene.ScenePlug( direction = Gaffer.Plug.Direction.Out )
		self["out"].setInput( self["in"] )
		self["out"].setFlags( Gaffer.Plug.Flags.Serialisable, False )

		self["__ContextQuery"] = Gaffer.ContextQuery()
		self["__ContextQuery"].addQuery( Gaffer.IntPlug( defaultValue = 1 ) )
		self["__ContextQuery"].addQuery( Gaffer.StringPlug() )
		self["__ContextQuery"]["queries"][0]["name"].setValue( "frameRange:start" )
		self["__ContextQuery"]["queries"][1]["name"].setValue( "renderPass" )

		self["__TimeWarp"] = Gaffer.TimeWarp()
		self["__TimeWarp"].setup( self["in"] )
		self["__TimeWarp"]["in"].setInput( self["in"] )
		self["__TimeWarp"]["speed"].setValue( 0 )
		self["__TimeWarp"]["offset"].setInput( self["__ContextQuery"]["out"][0]["value"] )

		self["__OptionQuery"] = GafferScene.OptionQuery()
		self["__OptionQuery"]["scene"].setInput( self["__TimeWarp"]["out"] )
		self["__OptionQuery"].addQuery( Gaffer.StringVectorDataPlug( defaultValue = IECore.StringVectorData() ) )
		self["__OptionQuery"].addQuery( Gaffer.BoolPlug( defaultValue = True ) )
		self["__OptionQuery"]["queries"][0]["name"].setValue( "renderPass:names" )
		self["__OptionQuery"]["queries"][1]["name"].setValue( "renderPass:enabled" )

		self["__Collect"] = Gaffer.Collect()
		self["__Collect"]["contextVariable"].setValue( "renderPass" )
		self["__Collect"]["contextValues"].setInput( self["__OptionQuery"]["out"][0]["value"] )
		self["__Collect"]["enabled"].setInput( self["__OptionQuery"]["out"][1]["value"] )
		self["__Collect"].addInput( Gaffer.StringPlug( "names" ) )
		self["__Collect"]["in"]["names"].setInput( self["__ContextQuery"]["out"][1]["value"] )

		self["names"] = Gaffer.StringVectorDataPlug( direction = Gaffer.Plug.Direction.Out, defaultValue = IECore.StringVectorData() )
		self["names"].setInput( self["__Collect"]["out"]["names"] )
		self["names"].setFlags( Gaffer.Plug.Flags.Serialisable, False )

	def _processedContexts( self, context ) :

		# make a context for each of the enabled pass names
		contexts = []
		for name in self["names"].getValue() :
			contexts.append( Gaffer.Context( context ) )
			contexts[-1]["renderPass"] = name

		return contexts

IECore.registerRunTimeTyped( RenderPassWedge, typeName = "GafferScene::RenderPassWedge" )
