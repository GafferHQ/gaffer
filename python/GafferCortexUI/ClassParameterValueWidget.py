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

class ClassParameterValueWidget( GafferCortexUI.CompoundParameterValueWidget ) :

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

	def _headerWidget( self ) :

		result = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 0 )

		# label

		label = GafferUI.Label(
			"Class" if self._collapsible() is not None else self._parameterLabelText( self.parameterHandler() ),
			horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right
		)
		## \todo Decide how we allow this sort of tweak using the public
		# interface. Perhaps we should have a SizeableContainer or something?
		label._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )
		label.setToolTip( self._parameterToolTip( self._parameterHandler() ) )
		result.append( label )

		# space
		result.append( GafferUI.Spacer( imath.V2i( 8, 1 ) ) )

		# class button
		className, classVersion = self._parameter().getClass( True )[1:3]

		classButton = GafferUI.MenuButton( className if className else "Choose...", hasFrame=False )
		classButton.setMenu( self.__classMenu() )
		result.append( classButton )

		# version button
		if className :
			versionButton = GafferUI.MenuButton( " v%d" % classVersion if className else "", hasFrame=False )
			versionButton.setMenu( self.__versionMenu() )
			result.append( versionButton )

		# a spacer to stop the buttons expanding
		result.append( GafferUI.Spacer( imath.V2i( 1, 1 ), imath.V2i( 9999999, 1 ) ), expand=True )

		return result

	def __classMenu( self ) :

		md = IECore.MenuDefinition()

		classInfo = self._parameter().getClass( True )

		classNameFilter = "*"
		with IECore.IgnoredExceptions( KeyError ) :
			classNameFilter = self._parameter().userData()["UI"]["classNameFilter"].value
		menuPathStart = max( 0, classNameFilter.find( "*" ) )

		if classInfo[1] :
			md.append(
				"/Remove", { "command" : IECore.curry( Gaffer.WeakMethod( self.__setClass ), "", 0 ) }
			)
			md.append( "/RemoveDivider", { "divider" : True } )

		loader = IECore.ClassLoader.defaultLoader( classInfo[3] )
		for className in loader.classNames( classNameFilter ) :

			classVersions = loader.versions( className )
			for classVersion in classVersions :

				menuPath = "/" + className[menuPathStart:]
				if len( classVersions ) > 1 :
					menuPath += "/v%d" % classVersion

				md.append(
					menuPath,
					{
						"command" : IECore.curry( Gaffer.WeakMethod( self.__setClass ), className, classVersion ),
						"active" : className != classInfo[1] or classVersion != classInfo[2]
					},
				)

		return GafferUI.Menu( md )

	def __versionMenu( self ) :

		md = IECore.MenuDefinition()

		classInfo = self._parameter().getClass( True )
		if classInfo[1] :
			loader = IECore.ClassLoader.defaultLoader( classInfo[3] )
			for version in loader.versions( classInfo[1] ) :
				md.append(
					"/v%d" % version,
					{
						"command" : IECore.curry( Gaffer.WeakMethod( self.__setClass ), classInfo[1], version ),
						"active" : version != classInfo[2],
					},
				)

		return GafferUI.Menu( md )

	def __setClass( self, className, classVersion ) :

		with self.getPlug().node().parameterModificationContext() :
			self._parameter().setClass( className, classVersion )

GafferCortexUI.ParameterValueWidget.registerType( IECore.ClassParameter, ClassParameterValueWidget )
