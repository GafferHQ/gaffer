##########################################################################
#
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

class FormatPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__menuButton = GafferUI.MenuButton( "", menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )
		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plug, **kw )

		self._addPopupMenu( self.__menuButton )
		self._updateFromPlug()

	def _updateFromPlug( self ) :

		self.__menuButton.setEnabled( self._editable() )

		text = ""
		if self.getPlug() is not None :
			with self.getContext() :
				fmt = self.getPlug().getValue()
				if fmt == GafferImage.Format() :
					text = "Default Format"
				else:
					text = GafferImage.Format.formatName( fmt )

		self.__menuButton.setText( text )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()
		if self.getPlug() is None :
			return result

		formats = []
		if not self.getPlug().ancestor( Gaffer.ScriptNode ).isSame( self.getPlug().node() ) :
			formats.append( ( "Default Format", GafferImage.Format() ) )

		for name in GafferImage.Format.formatNames() :
			formats.append( ( name, GafferImage.Format.getFormat( name ) ) )

		currentFormat = self.getPlug().getValue()
		for name, fmt in formats :
			result.append(
				"/" + name,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__applyFormat ), fmt = fmt ),
					"checkBox" : fmt == currentFormat,
				}
			)

		return result

	def __applyFormat( self, unused, fmt ) :

		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().setValue( fmt )

GafferUI.PlugValueWidget.registerType( GafferImage.FormatPlug, FormatPlugValueWidget )
GafferUI.PlugValueWidget.registerType( GafferImage.AtomicFormatPlug, FormatPlugValueWidget )

