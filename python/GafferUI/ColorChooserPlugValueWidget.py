##########################################################################
#
#  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

import Gaffer
import GafferUI

class ColorChooserPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__colorChooser = GafferUI.ColorChooser()

		GafferUI.PlugValueWidget.__init__( self, self.__colorChooser, plugs, **kw )

		self.__colorChooser.setSwatchesVisible( False )

		self.__colorChangedConnection = self.__colorChooser.colorChangedSignal().connect(
			Gaffer.WeakMethod( self.__colorChanged ), scoped = False
		)

		self.__lastChangedReason = None
		self.__mergeGroupId = 0

	def _updateFromValues( self, values, exception ) :

		# ColorChooser only supports one colour, and doesn't have
		# an "indeterminate" state, so when we have multiple plugs
		# the best we can do is take an average.
		if len( values ) :
			color = sum( values ) / len( values )
		else :
			color = imath.Color4f( 0 )

		with Gaffer.Signals.BlockedConnection( self.__colorChangedConnection ) :
			self.__colorChooser.setColor( color )
			self.__colorChooser.setErrored( exception is not None )

	def _updateFromEditable( self ) :

		self.__colorChooser.setEnabled( self.__allComponentsEditable() )

	def __colorChanged( self, colorChooser, reason ) :

		if not GafferUI.ColorChooser.changesShouldBeMerged( self.__lastChangedReason, reason ) :
			self.__mergeGroupId += 1
		self.__lastChangedReason = reason

		with Gaffer.UndoScope(
			next( iter( self.getPlugs() ) ).ancestor( Gaffer.ScriptNode ),
			mergeGroup = "ColorPlugValueWidget%d%d" % ( id( self, ), self.__mergeGroupId )
		) :

			with self._blockedUpdateFromValues() :
				for plug in self.getPlugs() :
					plug.setValue( self.__colorChooser.getColor() )

	def __allComponentsEditable( self ) :

		if not self._editable() :
			return False

		# The base class `_editable()` call doesn't consider that
		# child plugs might be read only, so check for that.
		## \todo Should the base class be doing this for us?
		for plug in self.getPlugs() :
			for child in Gaffer.Plug.Range( plug ) :
				if Gaffer.MetadataAlgo.readOnly( child ) :
					return False

		return True
