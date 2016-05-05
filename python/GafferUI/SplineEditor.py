##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

class SplineEditor( GafferUI.EditorWidget ) :

	def __init__( self, scriptNode, **kw ) :

		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )

		GafferUI.EditorWidget.__init__( self, self.__column, scriptNode, **kw )

		self.__splineGadget = GafferUI.SplinePlugGadget()
		self.__selectionAddedConnection = self.__splineGadget.selection().memberAddedSignal().connect( Gaffer.WeakMethod( self.__selectionChanged ) )
		self.__selectionRemovedConnection = self.__splineGadget.selection().memberRemovedSignal().connect( Gaffer.WeakMethod( self.__selectionChanged ) )

		self.__gadgetWidget = GafferUI.GadgetWidget( self.__splineGadget, cameraMode=GafferUI.GadgetWidget.CameraMode.Mode2D )
		self.__gadgetWidget.setBackgroundColor( IECore.Color3f( 0.07 ) )

		self.__column.append( self.__gadgetWidget, expand=True )

		self.__plugWidgetRow = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
		self.__xPlugWidget = GafferUI.NumericPlugValueWidget( plug=None )
		self.__plugWidgetRow.append( self.__xPlugWidget, expand=True )
		self.__yPlugWidget = GafferUI.NumericPlugValueWidget( plug=None )
		self.__plugWidgetRow.append( self.__yPlugWidget, expand=True )

		self.__column.append( self.__plugWidgetRow )

	def splines( self ) :

		return self.__splineGadget.splines()

	def __selectionChanged( self, selection, member ) :

		if not selection.size() :
			self.__xPlugWidget.setPlug( None )
			self.__yPlugWidget.setPlug( None )
		else :
			selectedPlug = selection[-1]
			self.__xPlugWidget.setPlug( selectedPlug["x"] )
			self.__yPlugWidget.setPlug( selectedPlug["y"] )
