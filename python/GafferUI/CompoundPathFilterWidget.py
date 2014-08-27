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

import IECore

import Gaffer
import GafferUI

class CompoundPathFilterWidget( GafferUI.PathFilterWidget ) :

	def __init__( self, pathFilter, **kw ) :

		self.__grid = GafferUI.GridContainer( spacing=4 )

		GafferUI.PathFilterWidget.__init__( self, self.__grid, pathFilter, **kw )

		self.__filters = []
		self._updateFromPathFilter()

	## Must be implemented by subclasses to update the UI when the filter
	# changes in some way.
	def _updateFromPathFilter( self ) :

		if self.pathFilter().getFilters() == self.__filters :
			return

		for y in range( self.__grid.gridSize().y - 1, -1, -1 ) :
			self.__grid.removeRow( y )

		gridPos = IECore.V2i( 0 )
		for filter in self.pathFilter().getFilters() :

			filterWidget = GafferUI.PathFilterWidget.create( filter )
			if filterWidget is None :
				continue

			self.__grid[gridPos.x, gridPos.y] = filterWidget

			if gridPos.x < 2 :
				gridPos.x += 1
			else :
				gridPos.x = 0
				gridPos.y += 1

		self.__filters = self.pathFilter().getFilters()

GafferUI.PathFilterWidget.registerType( Gaffer.CompoundPathFilter, CompoundPathFilterWidget )
