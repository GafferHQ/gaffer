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

import imath

import Gaffer
import GafferUI

# _Formatting
# -----------
#
# Formatters are used to present plug values as strings in a table cell.

__valueFormatters = {}

## Returns the value of the plug as it will be formatted in a Spreadsheet.
def formatValue( plug, forToolTip = False ) :

	currentPreset = Gaffer.NodeAlgo.currentPreset( plug )
	if currentPreset is not None :
		return currentPreset

	formatter = __valueFormatters.get( plug.__class__, __defaultValueFormatter )
	return formatter( plug, forToolTip )

## Registers a custom formatter for the specified `plugType`.
# `formatter` must have the same signature as `formatValue()`.
def registerValueFormatter( plugType, formatter ) :

	__valueFormatters[ plugType ] = formatter

# Standard formatters
# -------------------

def __defaultValueFormatter( plug, forToolTip ) :

	if not hasattr( plug, "getValue" ) :
		return ""

	value = plug.getValue()
	if isinstance( value, str ) :
		return value
	elif isinstance( value, ( int, float ) ) :
		return GafferUI.NumericWidget.valueToString( value )
	elif isinstance( value, ( imath.V2i, imath.V2f, imath.V3i, imath.V3f ) ) :
		return ", ".join( GafferUI.NumericWidget.valueToString( v ) for v in value )

	try :
		# Unknown type. If iteration is supported then use that.
		separator = "\n" if forToolTip else ", "
		return separator.join( str( x ) for x in value )
	except :
		# Otherwise just cast to string
		return str( value )

def __transformPlugFormatter( plug, forToolTip ) :

	separator = "\n" if forToolTip else "  "
	return separator.join(
		"{label} : {value}".format(
			label = c.getName().title() if forToolTip else c.getName()[0].title(),
			value = formatValue( c, forToolTip )
		)
		for c in plug.children()
	)

registerValueFormatter( Gaffer.TransformPlug, __transformPlugFormatter )
