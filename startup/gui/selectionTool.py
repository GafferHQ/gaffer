##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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
import IECoreScene

from pxr import Kind

import IECore

import GafferSceneUI

##########################################################################
# USD Kind
##########################################################################

def __kindSelectionModifier( targetKind, scene, pathString ) :
	path = pathString.split( "/" )[1:]

	kind = None
	while len( path ) > 0 :
		attributes = scene.attributes( path )
		kind = attributes.get( "usd:kind", None )

		if kind is not None and Kind.Registry.IsA( kind.value, targetKind ) :
			break
		path.pop()

	return path


usdKinds = Kind.Registry.GetAllKinds()

# Build a simplified hierarchy for sorting
kindPaths = []
for kind in usdKinds :
	kindPath = kind
	kindParent = Kind.Registry.GetBaseKind( kind )
	while kindParent != "" :
		kindPath = kindParent + "/" + kindPath
		kindParent = Kind.Registry.GetBaseKind( kindParent )
	kindPaths.append( kindPath )

kindPaths.sort( reverse = True)

# We prefer to have "subcomponent" at the end.
try :
	kindPaths.remove( "subcomponent" )
	kindPaths.append( "subcomponent" )
except :
	pass

for kindPath in kindPaths :
	kind = kindPath.split( "/" )[-1]
	GafferSceneUI.SelectionTool.registerSelectMode(
		"USD Kind/" + IECore.CamelCase.toSpaced( kind ),
		functools.partial( __kindSelectionModifier, kind ),
	)

##########################################################################
# Shader Assignment
##########################################################################

def __shaderSource( attributeKeyword, scene, pathString ) :
	path = pathString.split( "/" )[1:]

	while len( path ) > 0 :
		attributes = scene.attributes( path )
		for k, v in attributes.items() :
			if (
				attributeKeyword in k.split( ':' ) and
				k != "surface:full" and
				k != "surface:preview" and
				k != "displacement:full" and
				k != "displacement:preview" and 
				isinstance( v, IECoreScene.ShaderNetwork )
			) :
				return path
		
		path.pop()
	
	return []

GafferSceneUI.SelectionTool.registerSelectMode( "Shader Assignment/Surface", functools.partial( __shaderSource, "surface" ) )
GafferSceneUI.SelectionTool.registerSelectMode( "Shader Assignment/Displacement", functools.partial( __shaderSource, "displacement" ) )
