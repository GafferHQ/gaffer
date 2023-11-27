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

import contextlib

import IECore

import Gaffer
import GafferUI

class DataPathPreview( GafferUI.DeferredPathPreview ) :

	def __init__( self, path ) :

		self.__vectorDataWidget = GafferUI.VectorDataWidget( IECore.IntVectorData(), editable=False )

		GafferUI.DeferredPathPreview.__init__( self, self.__vectorDataWidget, path )

		self._updateFromPath()

	def isValid( self ) :

		if not hasattr( self.getPath(), "data" ) or not self.getPath().isLeaf() :
			return False

		return True

	def _load( self ) :

		data = None
		with contextlib.suppress( RuntimeError ) :
			data = self.getPath().data()

		return data

	def _deferredUpdate( self, data ) :

		if data is None :
			data = IECore.IntVectorData()
		elif not IECore.DataTraits.isSequenceDataType( data ) :
			data = IECore.StringVectorData( [ str( data.value ) ] )

		self.__vectorDataWidget.setData( data )

GafferUI.PathPreviewWidget.registerType( "Data", DataPathPreview )
