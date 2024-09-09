##########################################################################
#
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import GafferUI
import GafferCortexUI

class ParameterValueWidget( GafferUI.Widget ) :

	def __init__( self, plugValueWidget, parameterHandler, **kw ) :

		assert( isinstance( plugValueWidget, GafferUI.PlugValueWidget ) )

		GafferUI.Widget.__init__( self, plugValueWidget, **kw )

		self.__plugValueWidget = plugValueWidget
		self.__parameterHandler = parameterHandler

	def plug( self ) :

		return self.__parameterHandler.plug()

	def parameter( self ) :

		return self.__parameterHandler.parameter()

	def parameterHandler( self ) :

		return self.__parameterHandler

	def plugValueWidget( self ) :

		return self.__plugValueWidget

	__popupMenuSignal = Gaffer.Signals.Signal2()
	## This signal is emitted whenever a popup menu for a parameter is about
	# to be shown. This provides an opportunity to customise the menu from
	# external code. The signature for slots is ( menuDefinition, parameterValueWidget ),
	# and slots should just modify the menu definition in place.
	@classmethod
	def popupMenuSignal( cls ) :

		return cls.__popupMenuSignal

	@classmethod
	def create( cls, parameterHandler ) :

		parameter = parameterHandler.parameter()

		if parameter.presetsOnly :
			return GafferCortexUI.PresetsOnlyParameterValueWidget( parameterHandler )

		uiTypeHint = None
		with IECore.IgnoredExceptions( KeyError ) :
			uiTypeHint = parameter.userData()["UI"]["typeHint"].value

		parameterHierarchy = [ parameter.typeId() ] + IECore.RunTimeTyped.baseTypeIds( parameter.typeId() )

		if uiTypeHint is not None :
			for typeId in parameterHierarchy :
				creator = cls.__typesToCreators.get( ( typeId, uiTypeHint ), None )
				if creator is not None :
					return creator( parameterHandler )

		for typeId in parameterHierarchy :
			creator = cls.__typesToCreators.get( ( typeId, None ), None )
			if creator is not None :
				return creator( parameterHandler )

		w = GafferUI.PlugValueWidget.create( parameterHandler.plug() )
		if w is not None :
			return ParameterValueWidget( w, parameterHandler )

		return None

	@classmethod
	def registerType( cls, parameterClassOrTypeId, creator, uiTypeHint = None ) :

		if isinstance( parameterClassOrTypeId, IECore.TypeId ) :
			parameterTypeId = parameterClassOrTypeId
		else :
			parameterTypeId = parameterClassOrTypeId.staticTypeId()

		cls.__typesToCreators[(parameterTypeId, uiTypeHint)] = creator

	__typesToCreators = {}

# parameter popup menus
##########################################################################

# we piggy-back onto the existing PlugValueWidget popup menu signal to
# emit our own popup menu signal where appropriate.

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	node = plug.node()
	if not hasattr( node, "parameterHandler" ) :
		return

	# see if we can find a ParameterValueWidget associated with the PlugValueWidget,
	# and if we can then emit the popupMenuSignal() on it.
	parameterValueWidget = plugValueWidget.ancestor( GafferCortexUI.ParameterValueWidget )
	if parameterValueWidget is None :
		return

	ParameterValueWidget.popupMenuSignal()( menuDefinition, parameterValueWidget )

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )

# add menu items for presets

def __parameterPopupMenu( menuDefinition, parameterValueWidget ) :

	parameterHandler = parameterValueWidget.parameterHandler()

	if isinstance( parameterHandler.parameter(), IECore.CompoundVectorParameter ) :
		# the default value and overall presets don't currently work very well
		# for CompoundVectorParameters.
		return

	# replace plug default item with parameter default item. they
	# differ in that the parameter default applies to all children
	# of things like V3iParameters rather than just a single one.
	menuDefinition.remove( "/Default", raiseIfMissing=False )
	menuDefinition.append(
		"/Default",
		{
			"command" : IECore.curry( __setValue, parameterHandler, parameterHandler.parameter().defaultValue ),
			"active" : parameterValueWidget.plugValueWidget()._editable(),
		}
	)

	# add menu items for presets
	menuDefinition.remove( "/Preset", raiseIfMissing=False )
	if len( parameterHandler.parameter().presetNames() ) :
		menuDefinition.append( "/PresetDivider", { "divider" : True } )

	for name in parameterHandler.parameter().presetNames() :
		menuDefinition.append( "/" + name, { "command" : IECore.curry( __setValue, parameterHandler, name ) } )

__parameterPopupMenuConnection = ParameterValueWidget.popupMenuSignal().connect( __parameterPopupMenu, scoped = True )

def __setValue( parameterHandler, value ) :

	parameterHandler.parameter().setValue( value )
	with Gaffer.UndoScope( parameterHandler.plug().ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
		parameterHandler.setPlugValue()
