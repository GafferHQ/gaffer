##########################################################################
#
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

class PathChooserDialogue( GafferUI.Dialogue ) :

	## valid has the following possible values :
	#    None : Accept both valid (existing) and invalid (nonexisting) paths
	#    True : Accept only valid (existing) paths
	#    False : Accept only invalid (nonexisting) paths
	#
	# leaf has the following possible values :
	#    None : Accept both leaf and non-leaf paths
	#    True : Accept only leaf paths
	#    False : Accept only non-leaf paths
	def __init__( self, path, title=None, cancelLabel="Cancel", confirmLabel="OK", allowMultipleSelection=False, valid=None, leaf=None, bookmarks=None, **kw ) :

		if allowMultipleSelection :
			assert( valid != False )

		if title is None :
			title = "Select paths" if allowMultipleSelection else "Select path"

		GafferUI.Dialogue.__init__( self, title, **kw )

		self.__path = path
		self.__allowMultipleSelection = allowMultipleSelection
		self.__valid = valid
		self.__leaf = leaf

		self.__pathChooserWidget = GafferUI.PathChooserWidget( path, allowMultipleSelection=allowMultipleSelection, bookmarks=bookmarks )
		self._setWidget( self.__pathChooserWidget )
		self.__pathChooserWidget.pathSelectedSignal().connect( Gaffer.WeakMethod( self.__pathChooserSelected ), scoped = False )
		self.__pathChooserWidget.pathListingWidget().selectionChangedSignal().connect( Gaffer.WeakMethod( self.__updateButtonState ), scoped = False )

		self.__cancelButton = self._addButton( cancelLabel )
		self.__cancelButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ), scoped = False )
		self.__confirmButton = self._addButton( confirmLabel )
		self.__confirmButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ), scoped = False )

		self.__pathSelectedSignal = Gaffer.Signals.Signal1()

		self.__updateButtonState()

	## A signal called when a path has been selected. Slots for this signal
	# should accept a single argument which will be the PathChooserDialogue instance.
	def pathSelectedSignal( self ) :

		return self.__pathSelectedSignal

	## Causes the dialogue to enter a modal state, returning the path once it has been
	# selected by the user. Returns None if the dialogue is cancelled. Note that you should
	# use waitForPaths instead if multiple selection is enabled.
	def waitForPath( self, **kw ) :

		assert( not self.__allowMultipleSelection )
		paths = self.waitForPaths( **kw )
		if paths :
			assert( len( paths ) == 1 )
			return paths[0]

		return None

	## Causes the dialogue to enter a modal state, returning the paths once they have been
	# selected by the user. Returns None if the dialogue is cancelled.
	def waitForPaths( self, **kw ) :

		if self.__allowMultipleSelection :
			self.__pathChooserWidget.directoryPathWidget().grabFocus()
		else :
			self.__pathChooserWidget.pathWidget().grabFocus()

		button = self.waitForButton( **kw )

		if button is self.__confirmButton :
			return self.__result()

		return None

	def pathChooserWidget( self ) :

		return self.__pathChooserWidget

	def __result( self ) :

		result = self.__pathChooserWidget.pathListingWidget().getSelection()
		result = [ self.__path.copy().setFromString( x ) for x in result.paths() ]
		if not result and not self.__allowMultipleSelection :
			result = [ self.__path.copy() ]
		return result

	def __buttonClicked( self, button ) :

		if button is self.__confirmButton :
			if self.__pathChooserWidget.getBookmarks() is not None :
				self.__pathChooserWidget.getBookmarks().addRecent(
					str( self.__pathChooserWidget.directoryPathWidget().getPath() )
				)

			self.pathSelectedSignal()( self )

	def __pathChooserSelected( self, pathChooser ) :

		assert( pathChooser is self.__pathChooserWidget )
		if self.__confirmButton.getEnabled() :
			self.__confirmButton.clickedSignal()( self.__confirmButton )

	def __updateButtonState( self, *unused ) :

		confirmEnabled = True

		potentialResult = self.__result()
		if not potentialResult :
			confirmEnabled = False

		if confirmEnabled and self.__valid is not None :
			for path in potentialResult :
				if path.isValid() != self.__valid :
					confirmEnabled = False
					break

		if confirmEnabled and self.__leaf is not None :
			for path in potentialResult :
				if path.isValid() and path.isLeaf() != self.__leaf :
					confirmEnabled = False
					break

		self.__confirmButton.setEnabled( confirmEnabled )
