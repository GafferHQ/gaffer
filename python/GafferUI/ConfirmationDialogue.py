##########################################################################
#
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

import GafferUI

class ConfirmationDialogue( GafferUI.Dialogue ) :

	def __init__( self, title, message, cancelLabel="Cancel", confirmLabel="OK", sizeMode=GafferUI.Window.SizeMode.Automatic, details = None, **kw ) :

		GafferUI.Dialogue.__init__( self, title, sizeMode=sizeMode, **kw )

		with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 8 ) as column :

			GafferUI.Label( message )

			if details is not None :
				with GafferUI.Collapsible( label = "Details", collapsed = True ) :
					GafferUI.MultiLineTextWidget(
						text = details,
						editable = False,
					)

		self._setWidget( column )

		if cancelLabel is not None :
			self._addButton( cancelLabel )

		self.__confirmButton = self._addButton( confirmLabel )

	## Causes the dialogue to enter a modal state, returning True if the confirm
	# button was pressed, False if the cancel button was pressed, and None if
	# the user closed the dialogue.
	def waitForConfirmation( self, **kw ) :

		self.__confirmButton._qtWidget().setFocus()
		button = self.waitForButton( **kw )

		if button is None :
			return None
		else :
			return button is self.__confirmButton
