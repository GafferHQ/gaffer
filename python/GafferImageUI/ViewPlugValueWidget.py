##########################################################################
#
#  Copyright (c) 2022, Image Engine Design Inc. All rights reserved.
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

import functools

import IECore

import Gaffer
import GafferUI
import GafferImage

from GafferUI.PlugValueWidget import sole

class ViewPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__menuButton = GafferUI.MenuButton( menu = GafferUI.Menu( Gaffer.WeakMethod( self._menuDefinition ) ) )

		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plugs, **kw )

		self.__currentValue = None
		self.__availableViews = []

	def _auxiliaryPlugs( self, plug ) :

		firstInputImage = next( GafferImage.ImagePlug.RecursiveInputRange( plug.node() ), None )
		return [ firstInputImage["viewNames"] ] if firstInputImage is not None else []

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		return [
			{
				"value" : plug.getValue(),
				"availableViews" : viewNamesPlugs[0].getValue()
			}
			for plug, viewNamesPlugs in zip( plugs, auxiliaryPlugs )
		]

	def _updateFromValues( self, values, exception ) :

		self.__currentValue = sole( v["value"] for v in values )
		self.__availableViews = sorted( set().union( *[ v["availableViews"] for v in values ] ) )

		if self.__currentValue == "" :
			self.__menuButton.setText( "(Current Context)" )
		elif self.__currentValue is None :
			self.__menuButton.setText( "---" )
		elif self.__currentValue in self.__availableViews :
			self.__menuButton.setText( self.__currentValue )
		else :
			self.__menuButton.setText(
				"{}{}".format(
					self.__currentValue,
					" (invalid)" if GafferImage.ImagePlug.defaultViewName not in self.__availableViews else " (default)"
				)
			)

		self.__menuButton.setErrored( exception is not None )

	def _updateFromEditable( self ) :

		self.__menuButton.setEnabled( self._editable() )

	def _views( self ) :

		return self.__availableViews

	def _menuDefinition( self ) :

		result = IECore.MenuDefinition()
		for v in self._views():
			result.append(
				"/" + v,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = v ),
					"checkBox" : v == self.__currentValue,
				}
			)

		if all( Gaffer.Metadata.value( p, "viewPlugValueWidget:allowUseCurrentContext" ) for p in self.getPlugs() ) :
			result.append(
				"/(Current Context)",
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = "" ),
					"checkBox" : "" == self.__currentValue,
				}
			)

		return result

	def __setValue( self, unused, value ) :

		with Gaffer.UndoScope( next( iter( self.getPlugs() ) ).ancestor( Gaffer.ScriptNode ) ) :
			for plug in self.getPlugs() :
				plug.setValue( value )
