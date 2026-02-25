##########################################################################
#
#  Copyright (c) 2019, John Haddon. All rights reserved.
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
import GafferRenderMan

from GafferUI.PlugValueWidget import sole

Gaffer.Metadata.registerNode(

	GafferRenderMan.RenderManOptions,

	"description",
	"""
	Sets global scene options applicable to the RenderMan
	renderer. Use the StandardOptions node to set
	global options applicable to all renderers.
	""",

	plugs = {

		"options" : {

			"layout:customWidget:optionFilter:widgetType" : "GafferUI.PlugLayout.StandardFilterWidget",
			"layout:customWidget:optionFilter:index" : 0,

		},

	}

)

class _GPUConfigPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__menuButton = GafferUI.MenuButton( "", menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )

		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plugs, **kw )

		self._addPopupMenu( self.__menuButton )

		self.__currentValue = []

	# Returns a dictionary mapping device IDs to labels.
	@staticmethod
	def __devices() :

		from rman import pxrcore

		result = {}
		for i in range( pxrcore.GetGpgpuCount( pxrcore.k_cuda ) ) :
			descriptor = pxrcore.GpgpuDescriptor()
			pxrcore.GetGpgpuDescriptor( pxrcore.k_cuda, i, descriptor )
			result[i] = descriptor.name

		return result

	def _updateFromValues( self, values, exception ) :

		self.__currentValue = sole( values ) or []

		if not self.__currentValue :
			self.__menuButton.setText( "None" )
		else :
			devices = self.__devices()
			self.__menuButton.setText(
				", ".join( [
					"{} ({})".format( i, devices.get( i, "Unavailable" ) )
					for i in self.__currentValue
				] )
			)

		self.__menuButton.setErrored( exception is not None )

	def _updateFromEditable( self ) :

		self.__menuButton.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		devices = self.__devices()
		for i in self.__currentValue :
			devices.setdefault( i, "Unavailable" )

		for i in sorted( devices.keys() ) :
			result.append(
				"{} ({})".format( i, devices[i] ),
				{
					"checkBox" : i in self.__currentValue,
					"command" : functools.partial( Gaffer.WeakMethod( self.__toggleIndex ), index = i ),
				}
			)

		return result

	def __toggleIndex( self, checked, index ) :

		if checked :
			newValue = sorted( set( self.__currentValue ).union( [ index ] ) )
		else :
			newValue = [ i for i in self.__currentValue if i != index ]

		newValue = IECore.IntVectorData( newValue )

		with Gaffer.UndoScope( self.scriptNode() ) :
			for plug in self.getPlugs() :
				plug.setValue( newValue )
