##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

class StandardNodeToolbar( GafferUI.NodeToolbar ) :

	def __init__( self, node, edge = GafferUI.Edge.Top, **kw ) :

		self.__layout = GafferUI.PlugLayout(
			node,
			orientation = GafferUI.ListContainer.Orientation.Horizontal if edge in ( GafferUI.Edge.Top, GafferUI.Edge.Bottom ) else GafferUI.ListContainer.Orientation.Vertical,
			layoutName = "toolbarLayout",
			rootSection = edge.name
		)

		GafferUI.NodeToolbar.__init__( self, node, self.__layout, **kw )

	@staticmethod
	def top( node ) :

		return StandardNodeToolbar( node, edge = GafferUI.Edge.Top )

	@staticmethod
	def bottom( node ) :

		return StandardNodeToolbar( node, edge = GafferUI.Edge.Bottom )

	@staticmethod
	def left( node ) :

		return StandardNodeToolbar( node, edge = GafferUI.Edge.Left )

	@staticmethod
	def right( node ) :

		return StandardNodeToolbar( node, edge = GafferUI.Edge.Right )
