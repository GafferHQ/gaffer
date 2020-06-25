##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Cinesite VFX Ltd. nor the names of
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

import os

import Gaffer
import GafferScene
import GafferImageUI

from GafferImageUI import CatalogueUI

# We provide extended info in the Catalogue's status column
# to reflect interactive/batch renders triggered from the UI.

imageNameMap = {
	GafferScene.InteractiveRender : "catalogueStatusInteractiveRender",
	GafferScene.Render : "catalogueStatusBatchRender",
}

statusIconColumn = CatalogueUI.column( "Status" )
if statusIconColumn :

	class __ExtededStatusIconColumn( CatalogueUI.IconColumn ) :

		def __init__( self ) :

			CatalogueUI.IconColumn.__init__( self, "" )

		def value( self, image, catalogue ) :

			iconName = statusIconColumn.value( image, catalogue )

			try :
				scenePlug = GafferScene.SceneAlgo.sourceScene( catalogue["out"] )
				if not scenePlug :
					return iconName
			except Gaffer.ProcessException :
				return "errorNotificationSmall"

			for type_ in imageNameMap.keys() :
				if isinstance( scenePlug.node(), type_ ) :
					suffix = "Complete" if image["fileName"].getValue() else "Running"
					return imageNameMap[type_] + suffix

			return iconName

	CatalogueUI.registerColumn( "Status", __ExtededStatusIconColumn() )
