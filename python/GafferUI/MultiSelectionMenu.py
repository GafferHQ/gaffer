##########################################################################
#  
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import IECore

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

class MultiSelectionMenu( GafferUI.Button ) :

	__palette = None

	def __init__(
		self,
		allowMultipleSelection = False,
		alwaysHaveASelection = False,
		**kw
	) :
		self.__allowMultipleSelection = allowMultipleSelection
		self.__alwaysHaveASelection = alwaysHaveASelection
		self.__selectionChangedSignal = None
			
		GafferUI.Button.__init__( self, **kw )
		self._menu = GafferUI.Menu( self._addMenuDefinition, self._qtWidget() )
		self._qtWidget().setMenu( self._menu._qtWidget() )
		
		self.__menuLabels = []
		self.__selectedLabels = [] 
		self.__enabledLabels = []
		self._setDisplayName()

	## A signal emitted whenever the selection changes.
	def selectionChangedSignal( self ) :
		if self.__selectionChangedSignal is None :
			self.__selectionChangedSignal = GafferUI.WidgetSignal()
		return self.__selectionChangedSignal

	## Returns a list of the enabled labels.	
	def getEnabledItems( self ) :
		self._cleanUpList( self.__enabledLabels, self.__menuLabels ) # Ensure that the selected list is ordered properly.
		return self.__enabledLabels

	## Sets which items are enabled.	
	def setEnabledItems( self, labels ) :
		
		input = self._validateInput( labels )
		if len( input ) == 0 :
			raise RuntimeError("No valid items to be enabled were specified.")
	
		self.__enabledLabels[:] = input	

	## Adds a list of items to the current selection.
	def appendToSelection( self, labels ) :

		# Remove items that are not in the menu and returns a list.
		input = self._validateInput( labels )
		
		if self.__allowMultipleSelection :
			for label in labels :
				if not label in self.__selectedLabels :
					self.__selectedLabels.append( label )
			self._selectionChanged()
		else :
			if len( labels ) > 1 :
				raise RuntimeError("Parameter must be single item or a list with one element.")
	
		# Remove all selected labels that are not in the menu, emit signals if necessary and update the button.
		self._validateState()
	
	## Returns a list of the selected labels.	
	def getSelection( self ) :
		self._cleanUpList( self.__selectedLabels, self.__menuLabels ) # Ensure that the selected list is ordered properly.
		return self.__selectedLabels

	## Sets which items are selected.
	# If a list is provided then the current selection is replaced with the valid elements within the list.
	# If a single element is proveded then it is appended to the current selection unless multiple selections
	# are not enabled in which case the selection is replaced.
	def setSelection( self, labels ) :
		
		input = self._validateInput( labels )
		if len( input ) == 0 and self.__alwaysHaveASelection :
			raise RuntimeError("No valid selections were specified.")
		
		if self.__allowMultipleSelection :
			self.__selectedLabels[:] = input
			self._selectionChanged()
		else :
			if len( input ) > 1 :
				raise RuntimeError("Parameter must be single item or a list with one element.")
			else :
				self.__selectedLabels[:] = input
				self._selectionChanged()

		# Remove all selected labels that are not in the menu, emit signals if necessary and update the button.
		self._validateState()

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
			self._validateState()
	
	def insert( self, index, label ) :
		if not label in self.__menuLabels :
			self.__menuLabels.insert( index, label )
			self.__enabledLabels.insert( index, label )
	
	def setText( self, text ) :
		self._qtWidget().setText( text )
	
	def getText( self ) :
		self._qtWidget().getText()	
		
	##############################################
	# Private Methods
	#############################################
	def _validateInput( self, labels ) :
		if isinstance( labels, list ) :
			validInput = labels
		elif isinstance( labels, str) :
			validInput = [ labels ]
		else :
			validInput = list( labels )
				
		self._cleanUpList( validInput, self.__menuLabels )
		return validInput

	## The slot which is called when an item is clicked on.	
	def _selectClicked( self, label, selected=None ) :
		if self.__allowMultipleSelection :
			if selected == True :
				self.appendToSelection( label )
			else :
				self.__selectedLabels.remove( label )
				self._selectionChanged()
		else :
			# Check the mode that we are in. If we are not required to have a selection
			# then if we already have the label selected we can remove it.
			if label in self.__selectedLabels and not self.__alwaysHaveASelection :
				self.__selectedLabels = []
				self._validateState()
				self._selectionChanged()
			else :
				self.setSelection( label )
		
	## Updates the button's text and emits the selectionChangedSignal.
	def _selectionChanged( self ) :
		self._setDisplayName()
		self.selectionChangedSignal()( self )

	def _addMenuDefinition( self ) :
		m = IECore.MenuDefinition()
		for label in self.__menuLabels :
			menuPath = label
			if not menuPath.startswith( "/" ):
				menuPath = "/" + menuPath
			m.append(
				menuPath,
				{
					"command" : IECore.curry( self._selectClicked, label ),
					"active" : label in self.__enabledLabels,
					"checkBox" : ( ( self.__allowMultipleSelection ) or ( not self.__allowMultipleSelection and not self.__alwaysHaveASelection ) ) and label in self.__selectedLabels 
				}
			)
		return m

	## Checks to see if the internal lists are up-to-date and ordered correctly.
	# If a label has been found to be removed and it was selected then the selectionChanged signal is emitted
	# and the name of the button also changed.
	def _validateState( self ) :
		# Remove duplicates from the list whist preserving it's order.
		seen = set()
		seen_add = seen.add
		self.__menuLabels[:] = [ x for x in self.__menuLabels if x not in seen and not seen_add(x)]
			
		# Now we check that the enabled and selected lists are in order and without duplicates. If duplicates are
		# found or their entry does not exist within self.__menuLabels then they are removed and the relevant signals emitted.
		if self._cleanUpList( self.__selectedLabels, self.__menuLabels ) :
			self._selectionChanged()
		self._cleanUpList( self.__enabledLabels , self.__menuLabels ) 
		
		# If we don't allow multiple selection then make sure that at least one item is selected!
		if self.__alwaysHaveASelection and len( self.__selectedLabels ) == 0 and len( self.__enabledLabels ) > 0 :
			self.__selectedLabels.append( self.__enabledLabels[0] )
			self._selectionChanged()

	## A simple method to make sure that the passed list only holds
	# elements that l2 does. It also orders the elements and ensures
	# that there are no duplicate entries.
	# Returns True if the list was changed.
	def _cleanUpList( self, l, l2 ) :
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
		label = self.__menuLabels[index]
		self.remove(label)
		self._validateState()

	def __setslice__( self, i, j, sequence ) :
		s = list( sequence[i:j] )
		self.__menuLabels[i:j] = s
		self.__enabledLabels = self.__enabledLabels + s
		self._validateState()

	def __delslice__( self, i, j ) :
		del self.__menuLabels[i:j]
		self._validateState()

	def __setitem__( self, index, label ) :
		if label not in self.__menuLabels :
			self.__menuLabels[index] = label
			self.__enabledLabels.append( label )
			self._validateState()
	
	def __repr__( self ) :
		return self.__menuLabels.__repr__()

	def __getitem__( self, index ) :
		return self.__menuLabels[index]

	def _setDisplayName( self ) :
		name = "..."
		nEntries = len( self.__menuLabels )
		nSelected = len( self.__selectedLabels )
		if nEntries == 0 :
			name = "none"
		elif nSelected == nEntries :
			name = "all"
		elif nSelected == 0 :
			name = "none"
		elif nSelected == 1 :
			name = self.getSelection()[0]
		self._qtWidget().setText(name)

