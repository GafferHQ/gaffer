##########################################################################
#
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import GafferUI
import GafferCortexUI

from GafferCortexUI.CompoundPlugValueWidget import CompoundPlugValueWidget

## Supported parameter userData entries :
#
# ["UI"]["collapsible"]
# ["UI"]["collapsed"]
#
# Supported child userData entries :
#
# ["UI"]["visible"]
class CompoundParameterValueWidget( GafferCortexUI.ParameterValueWidget ) :

	## If collapsible is not None then it overrides any ["UI]["collapsible"] userData the parameter might have.
	def __init__( self, parameterHandler, collapsible=None, _plugValueWidgetClass=None, **kw ) :

		if collapsible is None :
			collapsible = True
			with IECore.IgnoredExceptions( KeyError ) :
				collapsible = parameterHandler.parameter().userData()["UI"]["collapsible"].value

		collapsed = None
		if collapsible :
			collapsed = True
			with IECore.IgnoredExceptions( KeyError ) :
				collapsed = parameterHandler.parameter().userData()["UI"]["collapsed"].value

		if _plugValueWidgetClass is None :
			_plugValueWidgetClass = _PlugValueWidget

		GafferCortexUI.ParameterValueWidget.__init__(
			self,
			_plugValueWidgetClass( parameterHandler, collapsed ),
			parameterHandler,
			**kw
		)

# CompoundParameterValueWidget is simply a lightweight wrapper around this CompoundPlugValueWidget
# derived class. This allows us to take advantage of all the code in CompoundPlugValueWidget that
# deals with dynamically adding and removing children etc.
class _PlugValueWidget( CompoundPlugValueWidget ) :

	def __init__( self, parameterHandler, collapsed ) :

		CompoundPlugValueWidget.__init__( self, parameterHandler.plug(), collapsed )

		self.__parameterHandler = parameterHandler

	def _childPlugs( self ) :

		plug = self.getPlug()
		orderedChildren = []
		for childName in self.__parameterHandler.parameter().keys() :
			if childName in plug :
				orderedChildren.append( plug[childName] )

		return orderedChildren

	def _childPlugWidget( self, childPlug ) :

		childParameter = self.__parameterHandler.parameter()[childPlug.getName()]

		with IECore.IgnoredExceptions( KeyError ) :
			if not childParameter.userData()["UI"]["visible"].value :
				return None

		childParameterHandler = self.__parameterHandler.childParameterHandler( childParameter )
		valueWidget = GafferCortexUI.ParameterValueWidget.create( childParameterHandler )
		if not valueWidget :
			return None

		if isinstance( valueWidget, CompoundParameterValueWidget ) :
			return valueWidget

		return GafferUI.PlugWidget( valueWidget )

	def _parameter( self ) :

		return self.__parameterHandler.parameter()

	def _parameterHandler( self ) :

		return self.__parameterHandler

	def _parameterLabelText( self, parameterHandler ) :

		return IECore.CamelCase.toSpaced( parameterHandler.plug().getName() )

	def _parameterToolTip( self, parameterHandler ) :

		plug = parameterHandler.plug()

		result = "<h3>" + plug.relativeName( plug.node() ) + "</h3>"
		if parameterHandler.parameter().description :
			result += "\n\n" + parameterHandler.parameter().description

		return result

# install implementation class as a protected member, so it can be used by
# derived classes.
CompoundParameterValueWidget._PlugValueWidget = _PlugValueWidget

GafferCortexUI.ParameterValueWidget.registerType( IECore.CompoundParameter, CompoundParameterValueWidget )
