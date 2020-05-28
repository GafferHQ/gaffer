##########################################################################
#
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

import functools

import IECore

import Gaffer
import GafferUI

class MultiSelectionMenu( GafferUI.MenuButton ) :

	def __init__(
		self,
		allowMultipleSelection = False,
		allowEmptySelection = True,
		**kw
	) :

		GafferUI.MenuButton.__init__(
			self,
			menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ),
			**kw
		)

		self.__allowMultipleSelection = allowMultipleSelection
		self.__allowEmptySelection = allowEmptySelection
		self.__selectionChangedSignal = None

		self.__menuLabels = []
		self.__selectedLabels = []
		self.__enabledLabels = []
		self.__setDisplayName()

	## A signal emitted whenever the selection changes.
	def selectionChangedSignal( self ) :
		if self.__selectionChangedSignal is None :
			self.__selectionChangedSignal = GafferUI.WidgetSignal()
		return self.__selectionChangedSignal

	## Returns a list of the enabled labels.
	def getEnabledItems( self ) :
		self.__cleanUpList( self.__enabledLabels, self.__menuLabels ) # Ensure that the selected list is ordered properly.
		return self.__enabledLabels

	## Sets which items are enabled.
	def setEnabledItems( self, labels ) :

		input = self.__validateInput( labels )
		self.__enabledLabels[:] = input

	## Adds a list of items to the current selection.
	def addSelection( self, labels ) :

		# Remove items that are not in the menu and returns a list.
		input = self.__validateInput( labels )

		if self.__allowMultipleSelection :
			for label in labels :
				if not label in self.__selectedLabels :
					self.__selectedLabels.append( label )
			self.__selectionChanged()
		else :
			if len( labels ) > 1 :
				raise RuntimeError("Parameter must be single item or a list with one element.")

		# Remove all selected labels that are not in the menu, emit signals if necessary and update the button.
		self.__validateState()

	## Returns a list of the selected labels.
	def getSelection( self ) :
		self.__cleanUpList( self.__selectedLabels, self.__menuLabels ) # Ensure that the selected list is ordered properly.
		return self.__selectedLabels

	## Sets which items are selected.
	# If a list is provided then the current selection is replaced with the valid elements within the list.
	# If a single element is provided then it is appended to the current selection unless multiple selections
	# are not enabled in which case the selection is replaced.
	def setSelection( self, labels ) :

		input = self.__validateInput( labels )
		if len( input ) == 0 and not self.__allowEmptySelection :
			return

		if self.__allowMultipleSelection :
			self.__selectedLabels[:] = input
			self.__selectionChanged()
		else :
			if len( input ) > 1 :
				raise RuntimeError("Parameter must be single item or a list with one element.")
			else :
				self.__selectedLabels[:] = input
				self.__selectionChanged()

		# Remove all selected labels that are not in the menu, emit signals if necessary and update the button.
		self.__validateState()

	def index( self, item ) :
		return self.__menuLabels.index( item )

	# Append a new item or list of items to the menu.
	def append( self, labels ) :
		if isinstance( labels, list ) :
			for label in labels :
				if not label in self.__menuLabels :
					self.__menuLabels.append( label )
					self.__enabledLabels.append( label )
		else :
			if not labels in self.__menuLabels :
				self.__menuLabels.append( labels )
				self.__enabledLabels.append( labels )

	def remove( self, label ) :
		if label in self.__menuLabels :
			self.__menuLabels.remove(label)
			self.__validateState()

	def insert( self, index, label ) :
		if not label in self.__menuLabels :
			self.__menuLabels.insert( index, label )
			self.__enabledLabels.insert( index, label )

	##############################################
	# Private Methods
	#############################################
	def __validateInput( self, labels ) :
		if isinstance( labels, list ) :
			validInput = labels
		elif isinstance( labels, str) :
			validInput = [ labels ]
		else :
			validInput = list( labels )

		self.__cleanUpList( validInput, self.__menuLabels )
		return validInput

	## The slot which is called when an item is clicked on.
	def __selectClicked( self, label, selected=None ) :
		if self.__allowMultipleSelection :
			if selected == True :
				self.addSelection( label )
			else :
				if not self.__allowEmptySelection :
					if len( self.__selectedLabels ) > 1 :
						self.__selectedLabels.remove( label )
						self.__selectionChanged()
				else :
					self.__selectedLabels.remove( label )
					self.__selectionChanged()
		else :
			# Check the mode that we are in. If we are not required to have a selection
			# then if we already have the label selected we can remove it.
			if label in self.__selectedLabels and self.__allowEmptySelection :
				self.__selectedLabels = []
				self.__validateState()
				self.__selectionChanged()
			else :
				self.setSelection( label )

	## Updates the button's text and emits the selectionChangedSignal.
	def __selectionChanged( self ) :
		self.__setDisplayName()
		self.selectionChangedSignal()( self )

	def __menuDefinition( self ) :

		m = IECore.MenuDefinition()
		for label in self.__menuLabels :
			menuPath = label
			if not menuPath.startswith( "/" ):
				menuPath = "/" + menuPath
			m.append(
				menuPath,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__selectClicked ), label ),
					"active" : label in self.__enabledLabels,
					"checkBox" : ( ( self.__allowMultipleSelection ) or ( not self.__allowMultipleSelection and self.__allowEmptySelection ) ) and label in self.__selectedLabels
				}
			)
		return m

	## Checks to see if the internal lists are up-to-date and ordered correctly.
	# If a label has been found to be removed and it was selected then the selectionChanged signal is emitted
	# and the name of the button also changed.
	def __validateState( self ) :
		# Remove duplicates from the list whist preserving it's order.
		seen = set()
		seen_add = seen.add
		self.__menuLabels[:] = [ x for x in self.__menuLabels if x not in seen and not seen_add(x)]

		# Now we check that the enabled and selected lists are in order and without duplicates. If duplicates are
		# found or their entry does not exist within self.__menuLabels then they are removed and the relevant signals emitted.
		if self.__cleanUpList( self.__selectedLabels, self.__menuLabels ) :
			self.__selectionChanged()
		self.__cleanUpList( self.__enabledLabels , self.__menuLabels )

		# If we don't allow multiple selection then make sure that at least one item is selected!
		if not self.__allowEmptySelection and len( self.__selectedLabels ) == 0 :
			if len( self.__enabledLabels ) > 0 :
				self.__selectedLabels.append( self.__enabledLabels[0] )
			elif len( self.__menuLabels ) > 0 :
				self.__selectedLabels.append( self.__menuLabels[0] )
			self.__selectionChanged()

	## A simple method to make sure that the passed list only holds
	# elements that l2 does. It also orders the elements and ensures
	# that there are no duplicate entries.
	# Returns True if the list was changed.
	def __cleanUpList( self, l, l2 ) :
		oldLength = len(l)
		seen = set()
		seen_add = seen.add
		l[:] = [ x for x in l2 if x not in seen and not seen_add(x) and x in l ]
		return len(l) != oldLength

	def __contains__( self, label ):
		return label in self.__menuLabels

	def __len__( self ) :
		return len( self.__menuLabels )

	def __delitem__( self, index ) :

		if isinstance( index, slice ) :
			del self.__menuLabels[index]
			self.__validateState()
		else :
			label = self.__menuLabels[index]
			self.remove(label)
			self.__validateState()

	def __setitem__( self, index, value ) :

		if isinstance( index, slice ) :
			s = list( value[index.start:index.stop] )
			self.__menuLabels[index.start:index.stop] = s
			self.__enabledLabels = self.__enabledLabels + s
			self.__validateState()
		else :
			if value not in self.__menuLabels :
				self.__menuLabels[index] = value
				self.__enabledLabels.append( value )
				self.__validateState()

	def __repr__( self ) :
		return self.__menuLabels.__repr__()

	def __getitem__( self, index ) :
		return self.__menuLabels[index]

	def __setDisplayName( self ) :

		name = "..."
		nEntries = len( self.__menuLabels )
		nSelected = len( self.__selectedLabels )

		if nEntries == 0 :
			name = "None"
		elif nSelected == 0 :
			name = "None"
		elif nSelected == 1 :
			name = self.getSelection()[0]
		elif nSelected == nEntries :
			name = "All"

		self.setText( name )
