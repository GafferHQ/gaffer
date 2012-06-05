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

class ClassVectorParameterValueWidget( GafferUI.CompoundParameterValueWidget ) :

	def __init__( self, parameterHandler, collapsible=None, **kw ) :
		
		GafferUI.CompoundParameterValueWidget.__init__( self, parameterHandler, collapsible, **kw )

		self.__buttonRow = None
		self.__childParameterUIs = {} # mapping from child parameter name to ui

	def _buildChildParameterUIs( self, column ) :
				
		if self.__buttonRow is None :
			self.__buttonRow = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
			self.__buttonRow.append(
				GafferUI.MenuButton( image="plus.png", hasFrame=False, menu=GafferUI.Menu( self.__classMenuDefinition() ) )
			)
			self.__buttonRow.append( GafferUI.Spacer( IECore.V2i( 1 ), IECore.V2i( 999999, 1 ) ), expand = True )
		
		# throw away child uis we don't need any more
		childParameterNames = set( self.parameter().keys() )
		for childParameterName in self.__childParameterUIs.keys() :
			if childParameterName not in childParameterNames :
				del self.__childParameterUIs[childParameterName]
		
		# make (or reuse existing) child uis for each child parameter
		orderedChildUIs = []
		for childParameterName, childParameter in self.parameter().items() :
			if childParameterName not in self.__childParameterUIs :
				self.__childParameterUIs[childParameterName] = _ChildParameterUI( self.parameterHandler().childParameterHandler( childParameter ) )
			orderedChildUIs.append( self.__childParameterUIs[childParameterName] )			
	
		# and update the column to display them
		column[:] = orderedChildUIs + [ self.__buttonRow ]
	
	def _layerMenuDefinition( self, childParameterName ) :
	
		result = IECore.MenuDefinition()	
	
		layerNames = self.parameter().keys()
		layerIndex = layerNames.index( childParameterName )
	
		result.append(
			"/Move/To Top",
			{
				"command" : IECore.curry( Gaffer.WeakMethod( self.__moveLayer ), layerIndex, 0 ),
				"active" : layerIndex != 0
			}
		)
		
		result.append(
			"/Move/Up",
			{
				"command" : IECore.curry( Gaffer.WeakMethod( self.__moveLayer ), layerIndex, layerIndex-1 ),
				"active" : layerIndex >= 1
			}
		)
		
		result.append(
			"/Move/Down",
			{
				"command" : IECore.curry( Gaffer.WeakMethod( self.__moveLayer ), layerIndex, layerIndex+1 ),
				"active" : layerIndex < len( layerNames ) - 1
			}
		)
		
		result.append(
			"/Move/To Bottom",
			{
				"command" : IECore.curry( Gaffer.WeakMethod( self.__moveLayer ), layerIndex, len( layerNames ) - 1 ),
				"active" : layerIndex < len( layerNames ) - 1
			}
		)
		
		result.append( "/RemoveDivider", { "divider" : True } )
		result.append( 
			"/Remove",
			{
				"command" : IECore.curry( Gaffer.WeakMethod( self.__removeClass ), childParameterName ),
			}
		)
		
		cls = self.parameter().getClass( childParameterName, True )
		loader = IECore.ClassLoader.defaultLoader( self.parameter().searchPathEnvVar() )
		versions = loader.versions( cls[1] )
		if len( versions ) > 1 :
			result.append( "/VersionDivider", { "divider" : True } )
			for version in versions :
				result.append(
					"/Set Version/%s" % version,
					{
						"command" : IECore.curry( Gaffer.WeakMethod( self.__setClass ), childParameterName, cls[1], version ),
						"active" : version != cls[2],
					}
				)
	
		return result
				
 	def __classMenuDefinition( self ) :
 	
 		result = IECore.MenuDefinition()
 				
 		classNameFilter = "*"
 		with IECore.IgnoredExceptions( KeyError ) :
 			classNameFilter = self.parameter().userData()["UI"]["classNameFilter"].value
		menuPathStart = max( 0, classNameFilter.find( "*" ) )
		
		loader = IECore.ClassLoader.defaultLoader( self.parameter().searchPathEnvVar() )
		for className in loader.classNames( classNameFilter ) :
			
			classVersions = loader.versions( className )
			for classVersion in classVersions :
								
				menuPath = "/" + className[menuPathStart:]
				if len( classVersions ) > 1 :
					menuPath += "/v%d" % classVersion
				
				result.append(
					menuPath,
					{
						"command" : IECore.curry( Gaffer.WeakMethod( self.__setClass ), None, className, classVersion ),
					},
				)
		
		return result
	
	def __removeClass( self, childParameterName ) :
	
		node = self.plug().node()
		node.setParameterisedValues()
		
		with node.parameterModificationContext() :
			self.parameter().removeClass( childParameterName )
		
	def __setClass( self, childParameterName, className, classVersion ) :
	
		if not childParameterName :
			childParameterName = self.parameter().newParameterName()
		
		node = self.plug().node()
		node.setParameterisedValues()
						
		with node.parameterModificationContext() :
			self.parameter().setClass( childParameterName, className, classVersion )

	def __moveLayer( self, oldIndex, newIndex ) :
	
		classes = [ c[1:] for c in self.parameter().getClasses( True ) ]
		cl = classes[oldIndex]
		del classes[oldIndex]
		classes[newIndex:newIndex] = [ cl ]

		node = self.plug().node()
		node.setParameterisedValues()
				
		with node.parameterModificationContext() :
			self.parameter().setClasses( classes )

		# just moving the layer won't actually add or remove plugs, so it won't trigger
		# a rebuild of the ui automatically via CompoundParameterValueWidget. so we
		# do that ourselves here.
		self._buildChildParameterUIs( self.__childParameterUIs.values()[0].parent() )
		
GafferUI.ParameterValueWidget.registerType( IECore.ClassVectorParameter.staticTypeId(), ClassVectorParameterValueWidget )

class _ChildParameterUI( GafferUI.CompoundParameterValueWidget ) :

	def __init__( self, parameterHandler, **kw ) :
			
		GafferUI.CompoundParameterValueWidget.__init__( self, parameterHandler, collapsible=False, **kw )
		
	def _buildChildParameterUIs( self, column ) :
		
		del column[:]
		with column :		
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal ) :
			
				collapseButton = GafferUI.Button( image = "collapsibleArrowRight.png", hasFrame=False )
				self.__collapseButtonConnection = collapseButton.clickedSignal().connect( Gaffer.WeakMethod( self.__collapseButtonClicked ) )
				
				# find parameters which belong in the header
				############################################
				
				preHeaderParameters = []
				headerParameters = []
				for parameter in self.parameter().values() :
					with IECore.IgnoredExceptions( KeyError ) :
						if parameter.userData()["UI"]["classVectorParameterPreHeader"].value :
							preHeaderParameters.append( parameter )
					with IECore.IgnoredExceptions( KeyError ) :
						if parameter.userData()["UI"]["classVectorParameterHeader"].value :
							headerParameters.append( parameter )
				
				# make the header
				#################
				
				# things before the layer button

				for parameter in preHeaderParameters :
					GafferUI.ParameterValueWidget.create( self.parameterHandler().childParameterHandler( parameter ) )
				
				# the layer button	
				
				layerButton = GafferUI.MenuButton( image="classVectorParameterHandle.png", hasFrame=False )

				parent = self.ancestor( ClassVectorParameterValueWidget )		
				cls = parent.parameter().getClass( self.parameter().name, True )

				layerButtonToolTip = "<h3>%s v%d</h3>" % ( cls[1], cls[2] )
				if cls[0].description :
					layerButtonToolTip += "<p>%s</p>" % cls[0].description
				layerButtonToolTip += "<p>Click to reorder or remove.</p>"
				layerButton.setToolTip( layerButtonToolTip )
				
				layerButton.setMenu( GafferUI.Menu( IECore.curry( Gaffer.WeakMethod( parent._layerMenuDefinition ), self.parameter().name ) ) )

				# the label

				if "label" in self.plug() :
					self.__label = GafferUI.Label( self.plug()["label"].getValue(), horizontalAlignment = GafferUI.Label.HorizontalAlignment.Left )
					self.__label._qtWidget().setMinimumWidth( self._labelWidth ) ## \todo Naughty!
					self.__label._qtWidget().setMaximumWidth( self._labelWidth )
					self.__label.setToolTip( self._parameterToolTip( self.parameterHandler().childParameterHandler( self.parameter()["label"] ) ) )
					self.__labelButtonPressConnection = self.__label.buttonPressSignal().connect( Gaffer.WeakMethod( self.__labelButtonPress ) )
					self.__plugSetConnection = self.plug().node().plugSetSignal().connect( Gaffer.WeakMethod( self.__plugSet ) )
				
				# parameters after the label	
				for parameter in headerParameters :
					GafferUI.ParameterValueWidget.create( self.parameterHandler().childParameterHandler( parameter ) )
				
				# prevent things expanding in an unwanted way
				GafferUI.Spacer( IECore.V2i( 1 ), IECore.V2i( 999999, 1 ), expand = True )
			
		# use a standard CompoundParameterValueWidget to actually house the
		# standard child parameters.
		
		self.__compoundParameterValueWidget = GafferUI.CompoundParameterValueWidget( self.parameterHandler(), collapsible=False )
		self.__compoundParameterValueWidget.setVisible( False )
		column.append( self.__compoundParameterValueWidget )
			
	def __collapseButtonClicked( self, button ) :
	
		visible = not self.__compoundParameterValueWidget.getVisible()
		self.__compoundParameterValueWidget.setVisible( visible )
		button.setImage( "collapsibleArrowDown.png" if visible else "collapsibleArrowRight.png" )
	
	def __labelButtonPress( self, label, event ) :
	
		self.__labelMenu = GafferUI.Menu( IECore.MenuDefinition( [
			( "Change label...", { "command" : Gaffer.WeakMethod( self.__changeLabel ) } ),
		] ) )
		self.__labelMenu.popup( parent=label )
	
	def __changeLabel( self, menu ) :
	
		labelPlug = self.parameterHandler().plug()["label"]
		dialogue = GafferUI.TextInputDialogue( initialText = labelPlug.getValue(), title="Enter new label" )
		labelText = dialogue.waitForText( parentWindow=menu.ancestor( GafferUI.Window ) )
		labelPlug.setValue( labelText )
	
	def __plugSet( self, plug ) :
	
		labelPlug = self.plug()["label"]
		if plug.isSame( labelPlug ) :
			self.__label.setText( labelPlug.getValue() )
	