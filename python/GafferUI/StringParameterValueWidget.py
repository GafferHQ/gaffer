##########################################################################
#
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

from __future__ import with_statement

import IECore

import Gaffer
import GafferUI

## Supported userData entries :
#
# ["UI"]["password"]
# ["UI"]["multiLine"]
class StringParameterValueWidget( GafferUI.ParameterValueWidget ) :

	def __init__( self, parameterHandler, **kw ) :

		multiLine = False
		with IECore.IgnoredExceptions( KeyError ) :
			multiLine = parameterHandler.parameter().userData()["UI"]["multiLine"].value

		if multiLine :
			plugValueWidget = GafferUI.MultiLineStringPlugValueWidget( parameterHandler.plug() )
		else :
			plugValueWidget = GafferUI.StringPlugValueWidget( parameterHandler.plug() )
			with IECore.IgnoredExceptions( KeyError ) :
				if parameterHandler.parameter().userData()["UI"]["password"].value :
					plugValueWidget.textWidget().setDisplayMode( GafferUI.TextWidget.DisplayMode.Password )

		GafferUI.ParameterValueWidget.__init__( self, plugValueWidget, parameterHandler, **kw )

GafferUI.ParameterValueWidget.registerType( IECore.StringParameter, StringParameterValueWidget )
