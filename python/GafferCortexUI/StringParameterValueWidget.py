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

import IECore

import Gaffer
import GafferUI
import GafferCortex
import GafferCortexUI

__nodeTypes = (
	GafferCortex.ParameterisedHolderNode,
	GafferCortex.ParameterisedHolderComputeNode,
	GafferCortex.ParameterisedHolderDependencyNode,
	GafferCortex.ParameterisedHolderTaskNode,
)

## Supported userData entries :
#
# ["UI"]["password"]
# ["UI"]["multiLine"]
# ["UI"]["multiLineFixedLineHeight"]

class StringParameterValueWidget( GafferCortexUI.ParameterValueWidget ) :

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

		GafferCortexUI.ParameterValueWidget.__init__( self, plugValueWidget, parameterHandler, **kw )

GafferCortexUI.ParameterValueWidget.registerType( IECore.StringParameter, StringParameterValueWidget )

##########################################################################
# Metadata
##########################################################################

def __fixedLineHeight( plug ) :

	## \todo There should really be a method to map from plug to parameter.
	# The logic exists in ParameterisedHolder.plugSet() but isn't public.
	parameter = plug.node().parameterHandler().parameter()
	for name in plug.relativeName( plug.node() ).split( "." )[1:] :
		if not isinstance( parameter, IECore.CompoundParameter ) :
			return None
		else :
			parameter = parameter[name]

	# by default the multi-line widget gets auto-expanded in the op interface which works nicely when
	# the user has to insert a lot of text, but very often we just want to provide a multi-line text field
	# for a brief description, for this reason we check by the user data "multiLineFixedLineHeight" which when set
	# forces the parameter to show an arbitrary number of lines
	fixedLineHeight = None
	with IECore.IgnoredExceptions( KeyError ) :
		fixedLineHeight = parameter.userData()["UI"]["multiLineFixedLineHeight"].value

	return fixedLineHeight

for nodeType in __nodeTypes:
	Gaffer.Metadata.registerValue( nodeType, "parameters.*...", "fixedLineHeight", __fixedLineHeight )
