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

import collections
import functools

import IECore

import Gaffer
import GafferUI
import GafferImage

class ViewPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__menuButton = GafferUI.MenuButton( menu = GafferUI.Menu( Gaffer.WeakMethod( self._menuDefinition ) ) )

		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plug, **kw )

		self.__plugDirtiedConnection = self.getPlug().node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__imagePlugDirtied ), scoped = True )
		self._updateFromPlug()


	def _updateFromPlug( self ) :

		errored = False
		with self.getContext() :
			try:
				value = self.getPlug().getValue()
			except:
				errored = True
		viewNames = GafferImage.ImagePlug.defaultViewNames()
		try:
			viewNames = self.__firstInputImagePlug().viewNames()
		except:
			pass

		name = value
		if value == "":
			name = "(Use Current Context)"
		elif not value in viewNames:
			if not GafferImage.ImagePlug.defaultViewName in viewNames:
				name += " (invalid)"
			else:
				name += " (default)"


		if not errored:
			self.__menuButton.setText( name )
		else:
			self.__menuButton.setText( "" )

		self.__menuButton.setErrored( errored )
		self.__menuButton.setEnabled( self._editable() )


	def __firstInputImagePlug( self ):
		for i in self.getPlug().node().children( GafferImage.ImagePlug ):
			if i.direction() == Gaffer.Plug.Direction.In:
				return i

		return None

	def __imagePlugDirtied( self, plug ):
		i = self.__firstInputImagePlug()
		if i and plug == self.__firstInputImagePlug()["viewNames"]:
			self._updateFromPlug()

	def _views( self ) :

		try :
			with self.getContext() :
				viewNames = self.__firstInputImagePlug()["viewNames"].getValue()
				return IECore.StringVectorData( sorted( viewNames ) )
		except:
			return GafferImage.ImagePlug.defaultViewNames()

	def _menuDefinition( self ) :

		currentValue = None
		with self.getContext() :
			with IECore.IgnoredExceptions( Gaffer.ProcessException ) :
				currentValue = self.getPlug().getValue()

		result = IECore.MenuDefinition()
		for v in self._views():
			result.append(
				"/" + v,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = v ),
					"checkBox" : v == currentValue,
				}
			)

		if Gaffer.Metadata.value( self.getPlug(), "viewPlugValueWidget:allowUseCurrentContext" ):
			result.append(
				"/(Use Current Context)",
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = "" ),
					"checkBox" : "" == currentValue,
				}
			)

		return result

	def __setValue( self, unused, value ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().setValue( value )
