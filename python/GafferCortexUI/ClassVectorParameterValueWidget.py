##########################################################################
#
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import imath

import IECore

import Gaffer
import GafferUI
import GafferCortexUI

from GafferCortexUI.CompoundPlugValueWidget import CompoundPlugValueWidget

class ClassVectorParameterValueWidget( GafferCortexUI.CompoundParameterValueWidget ) :

	def __init__( self, parameterHandler, collapsible=None, **kw ) :

		GafferCortexUI.CompoundParameterValueWidget.__init__(
			self,
			parameterHandler,
			collapsible,
			_PlugValueWidget,
			**kw
		)

class _PlugValueWidget( GafferCortexUI.CompoundParameterValueWidget._PlugValueWidget ) :

	def __init__( self, parameterHandler, collapsed ) :

		GafferCortexUI.CompoundParameterValueWidget._PlugValueWidget.__init__( self, parameterHandler, collapsed )

		self.__buttonRow = None

	def _footerWidget( self ) :

		if self.__buttonRow is not None :
			return self.__buttonRow

		self.__buttonRow = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
		self.__buttonRow.append(
			GafferUI.MenuButton( image="plus.png", hasFrame=False, menu=GafferUI.Menu( self.__classMenuDefinition() ) )
		)
		self.__buttonRow.append( GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ) ), expand = True )

		return self.__buttonRow

	def _childPlugWidget( self, childPlug ) :

		return _ChildParameterUI( self._parameterHandler().childParameterHandler( self._parameterHandler().parameter()[childPlug.getName()] ) )

	def _childPlugs( self ) :

		parentPlug = self.getPlug()
		return [ parentPlug[p] for p in self._parameter().keys() ]

	def _layerMenuDefinition( self, childParameterName ) :

		result = IECore.MenuDefinition()

		layerNames = self._parameter().keys()
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

		cls = self._parameter().getClass( childParameterName, True )
		loader = IECore.ClassLoader.defaultLoader( self._parameter().searchPathEnvVar() )
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
			classNameFilter = self._parameter().userData()["UI"]["classNameFilter"].value
		menuPathStart = max( 0, classNameFilter.find( "*" ) )

		loader = IECore.ClassLoader.defaultLoader( self._parameter().searchPathEnvVar() )
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

		node = self.getPlug().node()
		node.setParameterisedValues()

		with node.parameterModificationContext() :
			self._parameter().removeClass( childParameterName )

	def __setClass( self, childParameterName, className, classVersion ) :

		if not childParameterName :
			childParameterName = self._parameter().newParameterName()

		node = self.getPlug().node()
		node.setParameterisedValues()

		with node.parameterModificationContext() :
			self._parameter().setClass( childParameterName, className, classVersion )

	def __moveLayer( self, oldIndex, newIndex ) :

		classes = [ c[1:] for c in self._parameter().getClasses( True ) ]
		cl = classes[oldIndex]
		del classes[oldIndex]
		classes[newIndex:newIndex] = [ cl ]

		node = self.getPlug().node()
		node.setParameterisedValues()

		with node.parameterModificationContext() :
			self._parameter().setClasses( classes )

		# just moving the layer won't actually add or remove plugs, so it won't trigger
		# a rebuild of the ui automatically via CompoundParameterValueWidget. so we
		# do that ourselves here.
		## \todo Have the CompoundParameterHandler reflect the changing parameter order
		# by changing the plug order, and have the CompoundPlugValueWidget pick up on this
		# and reorder things automatically.
		self._CompoundPlugValueWidget__updateChildPlugUIs()

GafferCortexUI.ParameterValueWidget.registerType( IECore.ClassVectorParameter, ClassVectorParameterValueWidget )

class _ChildParameterUI( CompoundPlugValueWidget ) :

	def __init__( self, parameterHandler, **kw ) :

		CompoundPlugValueWidget.__init__(
			self,
			parameterHandler.plug(),
			collapsed = None,
			**kw
		)

		self.__parameterHandler = parameterHandler

		self.__footerWidget = None

	def _headerWidget( self ) :

		with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal ) as result :

			collapseButton = GafferUI.Button( image = "collapsibleArrowRight.png", hasFrame=False )
			collapseButton.clickedSignal().connect( Gaffer.WeakMethod( self.__collapseButtonClicked ) )

			GafferUI.Spacer( imath.V2i( 2 ) )

			# find parameters which belong in the header
			############################################

			preHeaderParameters = []
			headerParameters = []
			for parameter in self.__parameterHandler.parameter().values() :
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
				GafferCortexUI.ParameterValueWidget.create( self.__parameterHandler.childParameterHandler( parameter ) )

			# the layer button

			layerButton = GafferUI.MenuButton( image="classVectorParameterHandle.png", hasFrame=False )

			compoundPlugValueWidget = self.ancestor( _PlugValueWidget )
			parentParameter = compoundPlugValueWidget._parameter()
			cls = parentParameter.getClass( self.__parameterHandler.parameter().name, True )

			layerButtonToolTip = "<h3>%s v%d</h3>" % ( cls[1], cls[2] )
			if cls[0].description :
				layerButtonToolTip += "<p>%s</p>" % cls[0].description
			layerButtonToolTip += "<p>Click to reorder or remove.</p>"
			layerButton.setToolTip( layerButtonToolTip )

			layerButton.setMenu( GafferUI.Menu( IECore.curry( Gaffer.WeakMethod( compoundPlugValueWidget._layerMenuDefinition ), self.__parameterHandler.parameter().name ) ) )

			GafferUI.Spacer( imath.V2i( 2 ) )

			# the label

			if "label" in self.getPlug() :
				self.__label = GafferUI.Label( self.getPlug()["label"].getValue(), horizontalAlignment = GafferUI.Label.HorizontalAlignment.Left )
				self.__label._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() ) ## \todo Naughty!
				self.__label.setToolTip(
					compoundPlugValueWidget._parameterToolTip(
						self.__parameterHandler.childParameterHandler( self.__parameterHandler.parameter()["label"] ),
					),
				)
				self.__label.buttonPressSignal().connect( Gaffer.WeakMethod( self.__labelButtonPress ) )
				self.getPlug().node().plugSetSignal().connect( Gaffer.WeakMethod( self.__plugSet ) )

			# parameters after the label
			for parameter in headerParameters :
				GafferCortexUI.ParameterValueWidget.create( self.__parameterHandler.childParameterHandler( parameter ) )

			# prevent things expanding in an unwanted way
			GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

		return result

	def _childPlugWidget( self, childPlug ) :

		# _childPlugs() should prevent us arriving here
		assert( False )

	def _footerWidget( self ) :

		if self.__footerWidget is not None :
			return self.__footerWidget

		self.__footerWidget = GafferCortexUI.CompoundParameterValueWidget( self.__parameterHandler, collapsible=False )
		self.__footerWidget.setVisible( False )
		return self.__footerWidget

	def _childPlugs( self ) :

		# we draw them all ourselves, either in the header or the footer.
		return []

	def __collapseButtonClicked( self, button ) :

		visible = not self.__footerWidget.getVisible()
		self.__footerWidget.setVisible( visible )
		button.setImage( "collapsibleArrowDown.png" if visible else "collapsibleArrowRight.png" )

	def __labelButtonPress( self, label, event ) :

		self.__labelMenu = GafferUI.Menu( IECore.MenuDefinition( [
			( "Change label...", { "command" : Gaffer.WeakMethod( self.__changeLabel ) } ),
		] ) )
		self.__labelMenu.popup( parent=label )

	def __changeLabel( self, menu ) :

		labelPlug = self.__parameterHandler.plug()["label"]
		dialogue = GafferUI.TextInputDialogue( initialText = labelPlug.getValue(), title="Enter new label" )
		labelText = dialogue.waitForText( parentWindow=menu.ancestor( GafferUI.Window ) )
		labelPlug.setValue( labelText )

	def __plugSet( self, plug ) :

		labelPlug = self.__parameterHandler.plug()["label"]
		if plug.isSame( labelPlug ) :
			self.__label.setText( labelPlug.getValue() )
