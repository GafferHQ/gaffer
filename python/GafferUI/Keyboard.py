##########################################################################
#
#  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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

from Qt import QtCore
from Qt import QtWidgets

class Keyboard :

	Modifiers = IECore.Enum.create(
		"Shift",
		"Control",
		"Alt",
		"Meta"
	)

	@staticmethod
	def queryModifiers() :

		result = set()

		modifiers = QtWidgets.QApplication.queryKeyboardModifiers()

		if modifiers & QtCore.Qt.ShiftModifier :

			result.add( Keyboard.Modifiers.Shift )

		if modifiers & QtCore.Qt.ControlModifier :

			result.add( Keyboard.Modifiers.Control )

		if modifiers & QtCore.Qt.AltModifier :

			result.add( Keyboard.Modifiers.Alt )

		if modifiers & QtCore.Qt.MetaModifier :

			result.add( Keyboard.Modifiers.Meta )

		return result

	@staticmethod
	def modifiersDown( modifierOrModifiers ) :

		if not isinstance( modifierOrModifiers, ( list, tuple ) ) :
			modifierOrModifiers = [ modifierOrModifiers, ]

		current = Keyboard.queryModifiers()

		for m in modifierOrModifiers :
			if m not in current:
				return False

		return True
