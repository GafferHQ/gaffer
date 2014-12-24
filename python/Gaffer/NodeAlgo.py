##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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
def presets( plug ) :

	result = []
	for n in Gaffer.Metadata.registeredPlugValues( plug ) :
		if n.startswith( "preset:" ) :
			result.append( n[7:] )

	result.extend( Gaffer.Metadata.plugValue( plug, "presetNames" ) or [] )

	return result

## Returns the name of the preset currently applied to the plug.
# Returns None if no preset is applied.
def currentPreset( plug ) :

	if not hasattr( plug, "getValue" ) :
		return None
	
	value = plug.getValue()
	failedNames = set()
	for n in Gaffer.Metadata.registeredPlugValues( plug ) :
		if n.startswith( "preset:" ) :
			presetName = n[7:]
			if Gaffer.Metadata.plugValue( plug, n ) == value :
				return presetName
			else :
				failedNames.add( presetName )

	presetNames = Gaffer.Metadata.plugValue( plug, "presetNames" )
	if presetNames is not None :
		for presetName, presetValue in zip( presetNames, Gaffer.Metadata.plugValue( plug, "presetValues" ) ) :
			if value == presetValue and presetName not in failedNames :
				return presetName

	return None
	
## Applies the named preset to the plug.
def applyPreset( plug, presetName ) :

	value = Gaffer.Metadata.plugValue( plug, "preset:" + presetName )
	if value is None :
		presetNames = Gaffer.Metadata.plugValue( plug, "presetNames" )
		presetValues = Gaffer.Metadata.plugValue( plug, "presetValues" )
		value = presetValues[presetNames.index( presetName )]

	plug.setValue( value )

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
	
	return Gaffer.Metadata.plugValue( plug, "userDefault" ) is not None

def applyUserDefault( plug ) :
	
	__applyUserDefaults( plug )

def __applyUserDefaults( graphComponent ) :
	
	if isinstance( graphComponent, Gaffer.Plug ) :
		plugValue = Gaffer.Metadata.plugValue( graphComponent, "userDefault" )
		if plugValue is not None :
			graphComponent.setValue( plugValue )
	
	for child in graphComponent.children() :
		__applyUserDefaults( child )
