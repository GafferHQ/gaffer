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

import fnmatch
import traceback

import IECore

import Gaffer
import GafferUI

import GafferRenderMan

##########################################################################
# Access to shaders and annotations from the shader cache
##########################################################################

def _shader( shaderNode ) :

	if isinstance( shaderNode, GafferRenderMan.RenderManShader ) :
		shaderName = shaderNode["name"].getValue()
	else :
		shaderName = shaderNode["__shaderName"].getValue()

	try :
		return GafferRenderMan.RenderManShader.shaderLoader().read( shaderName + ".sdl" )
	except Exception, e :
		return None

def _shaderAnnotations( shaderNode ) :

	shader = _shader( shaderNode )
	return shader.blindData().get( "ri:annotations", {} ) if shader is not None else {}

##########################################################################
# Nodules
##########################################################################

def __parameterNoduleCreator( plug ) :

	# only coshader parameters should be connectable in the node
	# graph.
	if plug.typeId() == Gaffer.Plug.staticTypeId() :
		return GafferUI.StandardNodule( plug )
	elif plug.typeId() == Gaffer.ArrayPlug.staticTypeId() :
		# coshader arrays tend to be used for layering, so we prefer to present the
		# last entry at the top, hence the increasing direction.
		return GafferUI.CompoundNodule(
			plug,
			GafferUI.LinearContainer.Orientation.Y,
			direction = GafferUI.LinearContainer.Direction.Increasing
		)

	return None

GafferUI.Nodule.registerNodule( GafferRenderMan.RenderManShader, fnmatch.translate( "parameters.*" ), __parameterNoduleCreator )

##########################################################################
# NodeUI - we implement a custom NodeUI so we can enable/disable
# parameter uis using a plugSet callback.
##########################################################################

class RenderManShaderUI( GafferUI.StandardNodeUI ) :

	def __init__( self, node, displayMode = None, **kw ) :

		GafferUI.StandardNodeUI.__init__( self, node, displayMode, **kw )

		self.__plugSetConnection = self.node().plugSetSignal().connect( Gaffer.WeakMethod( self.__plugSet ) )
		self.__plugInputChangedConnection = self.node().plugInputChangedSignal().connect( Gaffer.WeakMethod( self.__plugInputChanged ) )

		self.__updateActivations()

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.StandardNodeUI.setReadOnly( self, readOnly )

		if not readOnly :
			self.__updateActivations()

	def __plugSet( self, plug ) :

		if plug.parent().isSame( self.node()["parameters"] ) :
			self.__updateActivations()

	def __plugInputChanged( self, plug ) :

		if plug.parent().isSame( self.node()["parameters"] ) :
			self.__updateActivations()

	def __updateActivations( self ) :

		if self.getReadOnly() :
			# nothing should be activated, regardless
			return

		parametersPlug = self.node()["parameters"]

		annotations = _shaderAnnotations( self.node() )
		activators = {}
		for name, value in annotations.items() :
			if name.startswith( "activator." ) and name.endswith( ".expression" ) :
				activator = activators.setdefault( name.split( "." )[1], {} )
				activator["expression"] = value.value
			elif name.endswith( ".activator" ) :
				plugName = name.split( "." )[0]
				plug = parametersPlug.getChild( plugName )
				if plug is not None :
					activator = activators.setdefault( value.value, {} )
					activatorPlugs = activator.setdefault( "plugs", [] )
					activatorPlugs.append( plug )

		class ExpressionVariables :

			def __init__( self, parametersPlug ) :

				self.__parametersPlug = parametersPlug

			def connected( self, key ) :

				return self.__parametersPlug[key].getInput() is not None

			def __getitem__( self, key ) :

				if key == "connected" :
					return self.connected
				else :
					return self.__parametersPlug[key].getValue()

		for activator in activators.values() :

			expression = activator.get( "expression", None )
			if not expression :
				continue

			plugs = activator.get( "plugs", None )
			if not plugs :
				continue

			try :
				active = eval( expression, globals(), ExpressionVariables( parametersPlug ) )
			except Exception, e :
				IECore.msg( IECore.Msg.Level.Error, "Parameter activator", "".join( traceback.format_exception_only( type( e ), e ) ) )
				continue

			for plug in plugs :
				plugValueWidget = self.plugValueWidget( plug, lazy=False )
				if plugValueWidget is not None :
					plugValueWidget.setReadOnly( not active )
					plugWidget = plugValueWidget.ancestor( GafferUI.PlugWidget )
					if plugWidget is not None :
						plugWidget.labelPlugValueWidget().setReadOnly( not active )

GafferUI.NodeUI.registerNodeUI( GafferRenderMan.RenderManShader, RenderManShaderUI )
GafferUI.NodeUI.registerNodeUI( GafferRenderMan.RenderManLight, RenderManShaderUI )

##########################################################################
# PlugValueWidget for the "parameters" compound. This is defined in order
# to group shader parameters into sections according to the "page" metadata.
##########################################################################

def __parametersPlugValueWidgetCreator( plug ) :

	shader = _shader( plug.node() )
	annotations = _shaderAnnotations( plug.node() )

	if shader is not None :
		# when shaders are reloaded after having new parameters added,
		# the order of the plugs and the parameters don't match, so we
		# use the parameter ordering to define the ui order.
		## \todo Ideally we'd get the plug ordering to match in
		# RenderManShader::loadShader(), and then the ordering of
		# connections in the node graph would be correct too.
		orderedParameterNames = shader.blindData()["ri:orderedParameterNames"]
		parameterNames = []
		for name in orderedParameterNames :
			if name.endswith( "Values" ) and name[:-6] + "Positions" in shader.parameters :
				name = name[:-6]
			elif name.endswith( "Positions" ) and name[:-9] + "Values" in shader.parameters :
				continue
			if name in plug :
				parameterNames.append( name )
	else :
		# we still want to present some sort of ui, even if we couldn't
		# load the shader for some reason.
		parameterNames = [ c.getName() for c in plug.children() ]

	sections = []
	namesToSections = {}
	for name in parameterNames :
		sectionName = annotations.get( name + ".page", None )
		sectionName = sectionName.value if sectionName is not None else ""
		if sectionName not in namesToSections :

			if sectionName == "" :
				collapsed = None
			else :
				collapsed = annotations.get( "page." + sectionName + ".collapsed", None )
				if collapsed is not None :
					collapsed = collapsed.value in ( "True", "true", "1" )
				else :
					collapsed = True

			section = {
				"label" : sectionName,
				"collapsed" : collapsed,
				"names" : [],
			}
			sections.append( section )
			namesToSections[sectionName] = section

		section = namesToSections[sectionName]
		section["names"].append( name )

	return GafferUI.SectionedCompoundPlugValueWidget( plug, sections )

GafferUI.PlugValueWidget.registerCreator( GafferRenderMan.RenderManShader, "parameters", __parametersPlugValueWidgetCreator )
GafferUI.PlugValueWidget.registerCreator( GafferRenderMan.RenderManLight, "parameters", __parametersPlugValueWidgetCreator )

##########################################################################
# PlugValueWidgets for the individual parameter plugs. We use annotations
# stored in the shader to provide hints as to how we should build the UI.
# We use the OSL specification for shader metadata in the hope that one day
# we'll get to use OSL in Gaffer and then we'll have a consistent metadata
# convention across both shader types.
##########################################################################

def __optionValue( plug, stringValue ) :

	if isinstance( plug, Gaffer.StringPlug ) :
		return stringValue
	elif isinstance( plug, Gaffer.IntPlug ) :
		return int( stringValue )
	elif isinstance( plug, Gaffer.FloatPlug ) :
		return float( stringValue )
	else :
		raise Exception( "Unsupported parameter type." )

def __numberCreator( plug, annotations ) :

	if isinstance( plug, Gaffer.CompoundPlug ) :
		return GafferUI.CompoundNumericPlugValueWidget( plug )
	else :
		return GafferUI.NumericPlugValueWidget( plug )

def __stringCreator( plug, annotations ) :

	return GafferUI.StringPlugValueWidget( plug )

def __booleanCreator( plug, annotations ) :

	return GafferUI.BoolPlugValueWidget( plug )

def __popupCreator( plug, annotations ) :

	options = annotations.get( plug.getName() + ".options", None )
	if options is None :
		raise Exception( "No \"options\" annotation." )

	options = options.value.split( "|" )
	labelsAndValues = [ ( x, __optionValue( plug, x ) ) for x in options ]
	return GafferUI.EnumPlugValueWidget( plug, labelsAndValues )

def __mapperCreator( plug, annotations ) :

	options = annotations.get( plug.getName() + ".options", None )
	if options is None :
		raise Exception( "No \"options\" annotation." )

	options = options.value.split( "|" )
	labelsAndValues = []
	for option in options :
		tokens = option.split( ":" )
		if len( tokens ) != 2 :
			raise Exception( "Option \"%s\" is not of form name:value" % option )
		labelsAndValues.append( ( tokens[0], __optionValue( plug, tokens[1] ) ) )

	return GafferUI.EnumPlugValueWidget( plug, labelsAndValues )

def __fileNameCreator( plug, annotations ) :

	extensions = annotations.get( plug.getName() + ".extensions", None )
	if extensions is not None :
		extensions = extensions.value.split( "|" )
	else :
		extensions = []

	bookmarksCategory = annotations.get( plug.getName() + ".bookmarksCategory", None )
	if bookmarksCategory is not None :
		bookmarksCategory = bookmarksCategory.value
	else :
		# seems like a reasonable guess, and it's preferable to have a category
		# rather than to have any bookmarks made here pollute the bookmarks for
		# other browsers.
		bookmarksCategory = "texture"

	return GafferUI.PathPlugValueWidget(
		plug,
		path = Gaffer.FileSystemPath(
			"/",
			filter = Gaffer.FileSystemPath.createStandardFilter(
				extensions = extensions,
				extensionsLabel = "Show only supported files",
			),
		),
		pathChooserDialogueKeywords = {
			"bookmarks" : GafferUI.Bookmarks.acquire(
				plug,
				pathType = Gaffer.FileSystemPath,
				category = bookmarksCategory,
			),
		},
	)

def __nullCreator( plug, annotations ) :

	return None

__creators = {
	"number" : __numberCreator,
	"string" : __stringCreator,
	"boolean" : __booleanCreator,
	"checkBox" : __booleanCreator,
	"popup" : __popupCreator,
	"mapper" : __mapperCreator,
	"filename" : __fileNameCreator,
	"null" : __nullCreator,
}

def __plugValueWidgetCreator( plug ) :

	global __creators

	annotations = _shaderAnnotations( plug.node() )
	parameterName = plug.getName()

	widgetType = annotations.get( parameterName + ".widget", None )
	widgetCreator = None
	if widgetType is not None :
		widgetCreator = __creators.get( widgetType.value, None )
		if widgetCreator is None :
			IECore.msg(
				IECore.Msg.Level.Warning,
				"RenderManShaderUI",
				"Shader parameter \"%s.%s\" has unsupported widget type \"%s\"" %
					( plug.node()["name"].getValue(), parameterName, widgetType )
			)

	if widgetCreator is not None :
		try :
			return widgetCreator( plug, annotations )
		except Exception, e :
			IECore.msg(
				IECore.Msg.Level.Warning,
				"RenderManShaderUI",
				"Error creating UI for parameter \"%s.%s\" : \"%s\"" %
					( plug.node()["name"].getValue(), parameterName, str( e ) )
			)

	if plug.typeId() == Gaffer.ArrayPlug.staticTypeId() :
		# coshader array
		return None

	result = GafferUI.PlugValueWidget.create( plug, useTypeOnly=True )
	if isinstance( result, GafferUI.VectorDataPlugValueWidget ) :
		result.vectorDataWidget().setSizeEditable( plug.defaultValue().size() == 0 )

	return result

GafferUI.PlugValueWidget.registerCreator( GafferRenderMan.RenderManShader, "parameters.*", __plugValueWidgetCreator )
GafferUI.PlugValueWidget.registerCreator( GafferRenderMan.RenderManLight, "parameters.*", __plugValueWidgetCreator )

##########################################################################
# Metadata registrations
##########################################################################


def __nodeDescription( node ) :

	__defaultNodeDescription = """Loads shaders for use in RenderMan renderers. Use the ShaderAssignment node to assign shaders to objects in the scene."""

	description = _shaderAnnotations( node ).get( "help", None )
	return description.value if description is not None else __defaultNodeDescription

def __plugDescription( plug ) :

	annotations = _shaderAnnotations( plug.node() )
	d = annotations.get( plug.getName() + ".help", None )

	return d.value if d is not None else ""

def __plugLabel( plug ) :

	annotations = _shaderAnnotations( plug.node() )
	d = annotations.get( plug.getName() + ".label", None )

	return d.value if d is not None else None

def __plugDivider( plug ) :

	annotations = _shaderAnnotations( plug.node() )
	d = annotations.get( plug.getName() + ".divider", None )
	if d is None :
		return False

	return d.value.lower() in ( "True", "true", "1" )

Gaffer.Metadata.registerNodeDescription( GafferRenderMan.RenderManShader, __nodeDescription )

Gaffer.Metadata.registerPlugDescription( GafferRenderMan.RenderManShader, "parameters.*", __plugDescription )
Gaffer.Metadata.registerPlugDescription( GafferRenderMan.RenderManLight, "parameters.*", __plugDescription )

Gaffer.Metadata.registerPlugValue( GafferRenderMan.RenderManShader, "parameters.*", "label", __plugLabel )
Gaffer.Metadata.registerPlugValue( GafferRenderMan.RenderManLight, "parameters.*", "label", __plugLabel )

Gaffer.Metadata.registerPlugValue( GafferRenderMan.RenderManShader, "parameters.*", "divider", __plugDivider )
Gaffer.Metadata.registerPlugValue( GafferRenderMan.RenderManLight, "parameters.*", "divider", __plugDivider )
