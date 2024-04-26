##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import collections
import inspect

import IECore

import Gaffer
import GafferScene

class RenderPassTypeAdaptor( GafferScene.SceneProcessor ) :

	def __init__( self, name = "RenderPassTypeAdaptor" ) :

		GafferScene.SceneProcessor.__init__( self, name )

		self["client"] = Gaffer.StringPlug()
		self["renderer"] = Gaffer.StringPlug()

		self["__OptionQuery"] = GafferScene.OptionQuery()
		self["__OptionQuery"]["scene"].setInput( self["in"] )
		self["__OptionQuery"].addQuery( Gaffer.StringPlug() )
		self["__OptionQuery"]["queries"][0]["name"].setValue( "renderPass:type" )

		self["__ContextQuery"] = Gaffer.ContextQuery()
		self["__ContextQuery"].addQuery( Gaffer.StringPlug() )
		self["__ContextQuery"]["queries"][0]["name"].setValue( "renderPass" )

		self["__NameSwitch"] = Gaffer.NameSwitch()
		self["__NameSwitch"].setup( GafferScene.ScenePlug() )
		self["__NameSwitch"]["in"]["in0"]["value"].setInput( self["in"] )

		self["__AutoTypeExpression"] = Gaffer.Expression()
		self["__AutoTypeExpression"].setExpression(
			inspect.cleandoc(
				"""
				import GafferScene

				renderPassType = parent["__OptionQuery"]["out"]["out0"]["value"]
				autoTypeFunction = GafferScene.RenderPassTypeAdaptor.autoTypeFunction()
				if renderPassType == "auto" and callable( autoTypeFunction ) :
					renderPassName = parent["__ContextQuery"]["out"]["out0"]["value"]
					renderPassType = autoTypeFunction( renderPassName )

				parent["__NameSwitch"]["selector"] = renderPassType
				"""
			)
		)

		global __renderPassTypeProcessors
		for type in self.registeredTypeNames() :
			outputPlug = self["in"]

			for name, p in __renderPassTypeProcessors[type].items() :
				processor = p()
				processor["in"].setInput( outputPlug )
				self.addChild( processor )
				processor.setName( f"{type}_{name}" )
				if processor.getChild( "client" ) :
					processor["client"].setInput( self["client"] )
				if processor.getChild( "renderer" ) :
					processor["renderer"].setInput( self["renderer"] )
				outputPlug = processor["out"]

			plug = self["__NameSwitch"]["in"].next()
			plug["value"].setInput( outputPlug )
			plug["name"].setValue( type )

		self["out"].setInput( self["__NameSwitch"]["out"]["value"] )
		self['out'].setFlags( Gaffer.Plug.Flags.Serialisable, False )

	global __renderPassTypeProcessors
	__renderPassTypeProcessors = collections.defaultdict( dict )

	@staticmethod
	def registerTypeProcessor( type, name, f ) :

		global __renderPassTypeProcessors
		__renderPassTypeProcessors[type][name] = f

	@staticmethod
	def registeredTypeNames() :

		global __renderPassTypeProcessors
		return __renderPassTypeProcessors.keys()

	@staticmethod
	def registeredTypeProcessors( type ) :

		global __renderPassTypeProcessors
		return __renderPassTypeProcessors[type].keys()

	@staticmethod
	def deregisterTypeProcessor( type, name ) :

		global __renderPassTypeProcessors
		if type in __renderPassTypeProcessors.keys() and name in __renderPassTypeProcessors[type].keys() :
			del __renderPassTypeProcessors[type][name]

			if not __renderPassTypeProcessors[type].keys() :
				del __renderPassTypeProcessors[type]

	global __renderPassAutoTypeFunction
	__renderPassAutoTypeFunction = None

	@staticmethod
	def registerAutoTypeFunction( f ) :

		global __renderPassAutoTypeFunction
		__renderPassAutoTypeFunction = f

	@staticmethod
	def autoTypeFunction() :

		global __renderPassAutoTypeFunction
		return __renderPassAutoTypeFunction

IECore.registerRunTimeTyped( RenderPassTypeAdaptor, typeName = "GafferScene::RenderPassTypeAdaptor" )
