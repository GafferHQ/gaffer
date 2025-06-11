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

from Qt import QtCore

class _ProxySelectionModel( QtCore.QItemSelectionModel ) :

	def __init__( self, viewModel, sourceSelectionModel, parent = None ) :

		QtCore.QItemSelectionModel.__init__( self, viewModel, parent )

		self.__sourceSelectionModel = sourceSelectionModel
		self.__initModelChain()

		self.__sourceSelectionModel.selectionChanged.connect( self.__sourceSelectionChanged )
		self.__sourceSelectionModel.currentChanged.connect( self.__sourceCurrentChanged )
		self.__sourceSelectionModel.modelChanged.connect( self.__modelChanged )

		self.__settingSelection = False
		self.currentChanged.connect( self.__currentChanged )
		self.modelChanged.connect( self.__modelChanged )

	def select( self, selection, flags ) :

		assert( isinstance( selection, ( QtCore.QItemSelection, QtCore.QModelIndex ) ) )

		if isinstance( selection, QtCore.QModelIndex ) :
			# The overload of this just wraps the selection and calls back here
			# which results in double evaluation
			selection = QtCore.QItemSelection( selection, selection )

		QtCore.QItemSelectionModel.select( self, selection, flags )

		# Forward to source model
		self.__settingSelection = True
		try :
			sourceSelection = self.mapSelectionToSource( selection )
			self.__sourceSelectionModel.select( sourceSelection, flags )
		finally :
			self.__settingSelection = False

	def mapToSource( self, index ) :

		assert( self.__modelChain )

		for model in self.__modelChain :
			index = model.mapToSource( index )

		if index.isValid() :
			assert( index.model() is self.__sourceSelectionModel.model() )

		return index

	def mapFromSource( self, index ) :

		assert( self.__modelChain )

		for model in reversed( self.__modelChain ) :
			index = model.mapFromSource( index )

		if index.isValid() :
			assert( index.model() is self.model() )

		return index

	def mapSelectionToSource( self, itemSelection ) :

		assert( self.__modelChain )

		for model in self.__modelChain :
			itemSelection = model.mapSelectionToSource( itemSelection )

		return itemSelection

	def mapSelectionFromSource( self, itemSelection ) :

		assert( self.__modelChain )

		for model in reversed( self.__modelChain ) :
			itemSelection = model.mapSelectionFromSource( itemSelection )

		return itemSelection

	def __modelChanged( self ) :

		self.__initModelChain()

	def __initModelChain( self ) :

		# Build a chain of models from this views model to the target

		assert( self.__sourceSelectionModel )

		models = []
		model = self.model()
		if model is not None :
			targetModel = self.__sourceSelectionModel.model()

			while model != targetModel :
				assert( hasattr( model, 'sourceModel' ) )
				models.append( model )
				model = model.sourceModel()

		self.__modelChain = models

	def __currentChanged( self, index ) :

		sourceIndex = self.mapToSource( index )
		self.__sourceSelectionModel.setCurrentIndex( sourceIndex, QtCore.QItemSelectionModel.NoUpdate )

	def __sourceSelectionChanged( self, selected, deselected ) :

		viewSelected = self.mapSelectionFromSource( selected )
		viewDeselected = self.mapSelectionFromSource( deselected )

		QtCore.QItemSelectionModel.select( self, viewDeselected, QtCore.QItemSelectionModel.Deselect )
		QtCore.QItemSelectionModel.select( self, viewSelected, QtCore.QItemSelectionModel.Select )

	def __sourceCurrentChanged( self, current, previous ) :

		if self.__settingSelection :
			return

		viewCurrent = self.mapFromSource( current )
		if viewCurrent.isValid() :
			self.setCurrentIndex( viewCurrent, QtCore.QItemSelectionModel.NoUpdate )
