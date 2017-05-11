##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

class SplineBasisPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__menuButton = GafferUI.MenuButton( "", menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )
		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plug, **kw )

		self.__presets = {
			"Linear" : ( IECore.CubicBasisf.linear(), 1 ),
			"BSpline" : ( IECore.CubicBasisf.bSpline(), 3 ),
			"CatmullRom" : ( IECore.CubicBasisf.catmullRom(), 2 ),
		}

		# TODO - there is some extra work to be done to support Bezier mode nicely, since you need
		# two tangent points for each segment.  For the moment, we just don't expose it
		#	"bezier" : ( IECore.CubicBasisf.bezier(), 1 ),

		self._addPopupMenu( self.__menuButton )
		self._updateFromPlug()

	def __currentLabel( self ) :
		text = "Invalid"
		if self.getPlug() is not None:
			basisName = None
			matrixName = "Unknown"

			with self.getContext():
				basisMatrix = self.getPlug()["basis"]["matrix"].getValue()
				basisStep = self.getPlug()["basis"]["step"].getValue()
				endPointMultiplicity = self.getPlug()["endPointMultiplicity"].getValue()

			for label, values in self.__presets.items():
				if basisMatrix == values[0].matrix:
					matrixName = label

				if basisMatrix == values[0].matrix and basisStep == values[0].step  and endPointMultiplicity == values[1]:
					basisName = label
					break

			if basisName:
				text = basisName
			else:
				text = "Custom Basis: Matrix=%s Step=%i EndPointMultiplicity=%i" % (
					matrixName, basisStep, endPointMultiplicity )

		return text

	def _updateFromPlug( self ) :

		self.__menuButton.setEnabled( self._editable() )
		self.__menuButton.setText( self.__currentLabel() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()
		if self.getPlug() is None :
			return result

		currentPreset = self.__currentLabel()
		for label, values in self.__presets.items() :
			result.append(
				"/" + label,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__applyPreset ), presetValues = values ),
					"checkBox" : label == currentPreset,
				}
			)

		return result

	def __applyPreset( self, unused, presetValues ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug()["basis"]["matrix"].setValue( presetValues[0].matrix )
			self.getPlug()["basis"]["step"].setValue( presetValues[0].step )
			self.getPlug()["endPointMultiplicity"].setValue( presetValues[1] )
