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

import Gaffer

import GafferUI

class CompoundPathPreview( GafferUI.PathPreviewWidget ) :

	## If specified, childTypes should be a tuple of names of types
	# registered with PathPreviewWidget - each type will be
	# instantiated to become a tab in the CompoundPathPreview.
	# If not specified, then all registered types are used.
	def __init__( self, path, childTypes=None, **kw ) :

		self.__tabbedContainer = GafferUI.TabbedContainer()

		GafferUI.PathPreviewWidget.__init__( self, self.__tabbedContainer, path, **kw )

		if childTypes is None :
			childTypes = GafferUI.PathPreviewWidget.types()

		self.__labelsAndTabs = []
		for type in childTypes :
			widget = GafferUI.PathPreviewWidget.create( type, path )
			self.__labelsAndTabs.append( ( type, widget ) )

		self.__currentTabChangedConnection = self.__tabbedContainer.currentChangedSignal().connect( Gaffer.WeakMethod( self.__currentTabChanged ) )

		self.__preferredTab = None

		self._updateFromPath()

	def _updateFromPath( self ) :

		with Gaffer.Signals.BlockedConnection( self.__currentTabChangedConnection ) :

			del self.__tabbedContainer[:]
			for label, tab in self.__labelsAndTabs :
				tab.setPath( self.getPath() )
				if tab.isValid() :
					self.__tabbedContainer.append( tab, label=label )
					if label == self.__preferredTab :
						self.__tabbedContainer.setCurrent( tab )

			if self.__preferredTab is None :
				self.__tabbedContainer.setCurrent( self.__tabbedContainer[-1] )

	def __currentTabChanged( self, tabbedContainer, current ) :

		assert( tabbedContainer is self.__tabbedContainer )
		if current is not None :
			self.__preferredTab = self.__tabbedContainer.getLabel( current )
