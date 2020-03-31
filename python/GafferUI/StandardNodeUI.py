##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
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

## A standard UI which should do the job fairly well for most node types. It uses
# the PlugLayout class to create the main layout - see documentation for PlugLayout
# to see how the layout can be controlled using Metadata entries.
class StandardNodeUI( GafferUI.NodeUI ) :

	def __init__( self, node, **kw ) :

		self.__mainColumn = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )

		GafferUI.NodeUI.__init__( self, node, self.__mainColumn, **kw )

		with self.__mainColumn :
			self.__plugLayout = GafferUI.PlugLayout( node )

	def plugValueWidget( self, plug ) :

		hierarchy = []
		while not plug.isSame( self.node() ) :
			hierarchy.insert( 0, plug )
			plug = plug.parent()

		widget = self.__plugLayout.plugValueWidget( hierarchy[0] )
		if widget is None :
			return None

		for i in range( 1, len( hierarchy ) ) :
			widget = widget.childPlugValueWidget( hierarchy[i] )
			if widget is None :
				return None

		return widget

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.NodeUI.setReadOnly( self, readOnly )

		self.__plugLayout.setReadOnly( readOnly )

GafferUI.NodeUI.registerNodeUI( Gaffer.Node, StandardNodeUI )
