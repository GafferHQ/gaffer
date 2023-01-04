##########################################################################
#
#  Copyright (c) 2014-2015, Image Engine Design Inc. All rights reserved.
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

import collections
import functools

import Gaffer

# Import C++ bindings
from Gaffer._NodeAlgo import *

##########################################################################
# Presets
##########################################################################

## Returns the names of all presets defined for the plug. Presets may
# be registered in two ways :
#
#	- Individually as "preset:<name>" plug metadata items
#	- En masse as a "presetNames" array metadata item with
#     corresponding "presetValues" array metadata item.
#
# Presets registered with the "preset:<name>" form take precedence. The
# "en masse" form can be useful where metadata is computed dynamically
# and the available presets will vary from instance to instance of a node.
#
# For a compound plug, it is considered to have a preset availiable if all
# child plugs have the same preset available
def presets( plug ) :
	if not hasattr( plug, "setValue" ):
		# For compound plugs, return presets that are present on all children
		if plug.children():
			return functools.reduce( __intersectLists, [ __presets( i ).keys() for i in plug.children()] )
		else:
			return []

	return list( __presets( plug ).keys() )

## Returns the name of the preset currently applied to the plug.
# Returns None if no preset is applied.
def currentPreset( plug ) :

	matchingPresets = []
	if not hasattr( plug, "getValue" ) :
		# For compound plugs, this is a bit tricky, since with a compound preset, some child plugs could
		# have the same value for multiple presets.  This means we can't narrow it down right away - we
		# need to track all presets that could potentially match the plugs we've considered so far
		if plug.children():
			matchingPresets = functools.reduce( __intersectLists, [ __matchingPresets( i ) for i in plug.children()] )
	else:
		matchingPresets = __matchingPresets( plug )

	if matchingPresets:
		return matchingPresets[0]
	else:
		return None

## Applies the named preset to the plug.
def applyPreset( plug, presetName ) :
	if not hasattr( plug, "setValue" ) :
		for i in plug.children():
			applyPreset( i, presetName )
	else:
		plug.setValue( __presets( plug )[presetName] )

def __presets( plug ) :

	result = collections.OrderedDict()

	for n in Gaffer.Metadata.registeredValues( plug ) :
		if n.startswith( "preset:" ) :
			result[n[7:]] = Gaffer.Metadata.value( plug, n )

	presetNames = Gaffer.Metadata.value( plug, "presetNames" )
	presetValues = Gaffer.Metadata.value( plug, "presetValues" )
	if presetNames and presetValues :
		for presetName, presetValue in zip( presetNames, presetValues ) :
			result.setdefault( presetName, presetValue )

	if result :
		return result

	# No presets from this plug. See if we can "inherit" them
	# from a connected plug.

	if plug.direction() == plug.Direction.In :
		plug = next( iter( plug.outputs() ), None )
		if plug is not None :
			return __presets( plug )

	return result

def __matchingPresets( plug ) :
	value = plug.getValue()
	return [ k for k, v in __presets( plug ).items() if v == value ]

def __intersectLists( a, b ) :
	return [ i for i in a if i in b ]

##########################################################################
# User defaults
##########################################################################

def applyUserDefaults( nodeOrNodes ) :

	if isinstance( nodeOrNodes, list ) :
		for node in nodeOrNodes :
			__applyUserDefaults( node )

	else :
		__applyUserDefaults( nodeOrNodes )

def hasUserDefault( plug ) :

	return Gaffer.Metadata.value( plug, "userDefault" ) is not None

def isSetToUserDefault( plug ) :

	if not hasattr( plug, "getValue" ) :
		return False

	userDefault = Gaffer.Metadata.value( plug, "userDefault" )
	if userDefault is None :
		return False

	if Gaffer.PlugAlgo.dependsOnCompute( plug ) :
		# Computed values may vary by context, as such there is no
		# single "current value", so no true concept of whether or not
		# it's at the user default.
		return False

	return userDefault == plug.getValue()

def applyUserDefault( plug ) :

	__applyUserDefaults( plug )

def __applyUserDefaults( graphComponent ) :

	if isinstance( graphComponent, Gaffer.ValuePlug ) and graphComponent.settable() :
		plugValue = Gaffer.Metadata.value( graphComponent, "userDefault" )
		if plugValue is not None :
			graphComponent.setValue( plugValue )

	for plug in graphComponent.children( Gaffer.Plug ) :
		__applyUserDefaults( plug )
