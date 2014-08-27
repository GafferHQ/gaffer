##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )

## PyQt and PySide differ in their bindings of functions using the
# QVariant type. PySide doesn't expose QVariant and instead uses
# the standard python types, whereas PyQt binds and uses the QVariant type.
# This class provides functions to help with writing code which works
# with either set of bindings.
class _Variant() :

	## Returns value converted to a form which can be passed to a function
	# expecting a QVariant.
	@staticmethod
	def toVariant( value ) :

		# PyQt uses QVariant
		if hasattr( QtCore, "QVariant" ) :
			if value is not None :
				return QtCore.QVariant( value )
			else :
				return QtCore.QVariant()

		# whereas PySide just uses python values
		return value

	## Converts variant to a standard python object.
	@staticmethod
	def fromVariant( variant ) :

		if hasattr( QtCore, "QVariant" ) and isinstance( variant, QtCore.QVariant ) :
			t = variant.type()
			if t == QtCore.QVariant.String :
				return str( variant.toString() )
			elif t == QtCore.QVariant.Double :
				return variant.toDouble()[0]
			elif t == QtCore.QVariant.Int :
				return variant.toInt()[0]
			elif t == QtCore.QVariant.Bool :
				return variant.toBool()
			else :
				raise ValueError( "Unsupported QVariant type" )
		else :
			return variant
