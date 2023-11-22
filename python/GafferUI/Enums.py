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

import enum

import GafferUI

from Qt import QtCore

## \todo Move other enums here - ListContainer.Orientation for instance.
__all__ = [ "HorizontalAlignment", "VerticalAlignment", "Edge", "ScrollMode" ]

# HorizontalAlignment

HorizontalAlignment = enum.Enum( "HorizontalAlignment", [ "None_", "Left", "Right", "Center", "Justify" ] )

@staticmethod
def __horizontalFromQt( a ) :

	a = a & QtCore.Qt.AlignHorizontal_Mask
	if a == QtCore.Qt.AlignLeft :
		return HorizontalAlignment.Left
	elif a == QtCore.Qt.AlignRight :
		return HorizontalAlignment.Right
	elif a == QtCore.Qt.AlignHCenter :
		return HorizontalAlignment.Center
	elif a == QtCore.Qt.AlignJustify :
		return HorizontalAlignment.AlignJustify

	return HorizontalAlignment.None_

@staticmethod
def __horizontalToQt( a ) :

	if a == HorizontalAlignment.Left :
		return QtCore.Qt.AlignLeft
	elif a == HorizontalAlignment.Right :
		return QtCore.Qt.AlignRight
	elif a == HorizontalAlignment.Center :
		return QtCore.Qt.AlignHCenter
	elif a == HorizontalAlignment.Justify :
		return QtCore.Qt.AlignJustify

	return QtCore.Qt.Alignment( 0 )

HorizontalAlignment._fromQt = __horizontalFromQt
HorizontalAlignment._toQt = __horizontalToQt

# VerticalAlignment

VerticalAlignment = enum.Enum( "VerticalAlignment", [ "None_", "Top", "Bottom", "Center" ] )

@staticmethod
def __verticalFromQt( a ) :

	a = a & QtCore.Qt.AlignVertical_Mask
	if a == QtCore.Qt.AlignTop :
		return VerticalAlignment.Top
	elif a == QtCore.Qt.AlignBottom :
		return VerticalAlignment.Bottom
	elif a == QtCore.Qt.AlignVCenter :
		return VerticalAlignment.Center

	return VerticalAlignment.None_

@staticmethod
def __verticalToQt( a ) :

	if a == VerticalAlignment.Top :
		return QtCore.Qt.AlignTop
	elif a == VerticalAlignment.Bottom :
		return QtCore.Qt.AlignBottom
	elif a == VerticalAlignment.Center :
		return QtCore.Qt.AlignVCenter

	return QtCore.Qt.Alignment( 0 )

VerticalAlignment._fromQt = __verticalFromQt
VerticalAlignment._toQt = __verticalToQt

# Edge

Edge = enum.Enum( "Edge", [ "Top", "Bottom", "Left", "Right" ] )

# Scroll Mode

ScrollMode = enum.Enum( "ScrollMode", [ "Never", "Always", "Automatic" ] )

__modesToPolicies = {
	ScrollMode.Never : QtCore.Qt.ScrollBarAlwaysOff,
	ScrollMode.Always : QtCore.Qt.ScrollBarAlwaysOn,
	ScrollMode.Automatic : QtCore.Qt.ScrollBarAsNeeded,
}

__policiesToModes = {
	QtCore.Qt.ScrollBarAlwaysOff : ScrollMode.Never,
	QtCore.Qt.ScrollBarAlwaysOn : ScrollMode.Always,
	QtCore.Qt.ScrollBarAsNeeded : ScrollMode.Automatic,
}

@staticmethod
def __scrollModeToQt ( a ):
	return __modesToPolicies[a]

@staticmethod
def __scrollModeFromQt ( a ):
	return __policiesToModes[a]

ScrollMode._fromQt = __scrollModeFromQt
ScrollMode._toQt = __scrollModeToQt
