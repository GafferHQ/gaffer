##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferUI

class TransformPlugValueWidget( GafferUI.CompoundPlugValueWidget ) :

	def __init__( self, plug, collapsed=True, label=None, **kw ) :

		GafferUI.CompoundPlugValueWidget.__init__( self, plug, collapsed, label, self.__summary )

	@staticmethod
	def __summary( plug ) :

		info = []

		translate = plug["translate"].getValue()
		if translate[0] != 0 or translate[1] != 0 or translate[2] != 0 :
			info.append( "Translate " + str( translate ) )

		rotate = plug["rotate"].getValue()
		if rotate[0] != 0 or rotate[1] != 0 or rotate[2] != 0 :
			info.append( "Rotate " + str( rotate ) )

		scale = plug["scale"].getValue()
		if scale[0] != 1 or scale[1] != 1 or scale[2] != 1 :
			if scale[0] != scale[1] or scale[0] != scale[2] :
				info.append( "Scale " + str( scale ) )
			else :
				info.append( "Scale %0g" % scale[0] )

		return ", ".join( info )


GafferUI.PlugValueWidget.registerType( Gaffer.TransformPlug, TransformPlugValueWidget )
