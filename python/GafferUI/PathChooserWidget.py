##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

class PathChooserWidget( GafferUI.Widget ) :

	def __init__( self, path, **kw ) :
	
		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=8 )
		
		GafferUI.Widget.__init__( self, self.__column, **kw )
		
		self.__path = path
				
		self.__directoryListing = GafferUI.PathListingWidget( self.__path )
		self.__column.append( self.__directoryListing, True )
		
		self.__filterFrame = GafferUI.Frame( borderWidth=0, borderStyle=GafferUI.Frame.BorderStyle.None )
		self.__column.append( self.__filterFrame )
		self.__filter = None
		self.__updateFilter()
		
		pathWidgetRow = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 0 )
		
		reloadButton = GafferUI.Button( image = "refresh.png", hasFrame=False )
		reloadButton.setToolTip( "Click to refresh view" )
		self.__reloadButtonClickedConnection = reloadButton.clickedSignal().connect( Gaffer.WeakMethod( self.__reloadButtonClicked ) )
		pathWidgetRow.append( reloadButton )
		
		upButton = GafferUI.Button( image = "pathUpArrow.png", hasFrame=False )
		upButton.setToolTip( "Click to go up one level" )
		self.__upButtonClickedConnection = upButton.clickedSignal().connect( Gaffer.WeakMethod( self.__upButtonClicked ) )
		pathWidgetRow.append( upButton )
		
		pathWidgetRow.append( GafferUI.Spacer( IECore.V2i( 4, 4 ) ) )
		
		self.__pathWidget = GafferUI.PathWidget( self.__path )
		pathWidgetRow.append( self.__pathWidget )
		
		self.__column.append( pathWidgetRow )
		
		self.__pathSelectedSignal = GafferUI.WidgetSignal()

		self.__listingSelectedConnection = self.__directoryListing.pathSelectedSignal().connect( Gaffer.WeakMethod( self.__pathSelected ) )
		self.__pathWidgetSelectedConnection = self.__pathWidget.activatedSignal().connect( Gaffer.WeakMethod( self.__pathSelected ) )
		self.__pathChangedConnection = self.__path.pathChangedSignal().connect( Gaffer.WeakMethod( self.__pathChanged ) )
		
	## Returns the PathWidget used for text-based path entry.
	def pathWidget( self ) :
	
		return self.__pathWidget

	## This signal is emitted when the user has selected a path.
	def pathSelectedSignal( self ) :
	
		return self.__pathSelectedSignal

	# This slot is connected to the pathSelectedSignals of the children and just forwards
	# them to our own pathSelectedSignal.
	def __pathSelected( self, childWidget ) :
		
		self.pathSelectedSignal()( self )

	def __upButtonClicked( self, button ) :
	
		if not len( self.__path ) :
			return
	
		del self.__path[-1]

	def __reloadButtonClicked( self, button ) :
	
		self.__path.pathChangedSignal()( self.__path )
	
	def __updateFilter( self ) :
	
		newFilter = self.__path.getFilter()
		if self.__filter is newFilter :
			return
		
		newFilterUI = None
		if newFilter is not None :
			newFilterUI = GafferUI.PathFilterWidget.create( newFilter )
		
		self.__filterFrame.setChild( newFilterUI )
		self.__filterFrame.setVisible( newFilterUI is not None )
			
		self.__filter = newFilter
	
	def __pathChanged( self, path ) :
	
		self.__updateFilter()