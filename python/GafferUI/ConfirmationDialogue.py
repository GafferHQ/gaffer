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

    def __init__( self, title, message, buttonLabels = [ "Cancel", "OK" ], defaultButton = 1, sizeMode=GafferUI.Window.SizeMode.Automatic, **kw ) :

        GafferUI.Dialogue.__init__( self, title, sizeMode=sizeMode, **kw )

        self._setWidget( GafferUI.Label( message ) )

        self.__defaultButton = defaultButton if defaultButton < len(buttonLabels) else (len(buttonLabels)-1)

        self.__buttons = []
        for buttonLabel in buttonLabels:
            self.__buttons.append( self._addButton( buttonLabel ) )

    ## Causes the dialogue to enter a modal state, returning the ID of the
    # button that was pressed
    def waitForConfirmation( self, **kw ) :

        self.__buttons[self.__defaultButton]._qtWidget().setFocus()
        button = self.waitForButton( **kw )
        return self.__buttons.index(button)
