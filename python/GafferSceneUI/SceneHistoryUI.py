##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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
import IECoreScene

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

def appendViewContextMenuItems( viewer, view, menuDefinition ) :

	if not isinstance( view, GafferSceneUI.SceneView ) :
		return None

	menuDefinition.append(
		"/History",
		{
			"subMenu" : functools.partial(
				__historySubMenu,
				context = view.getContext(),
				scene = view["in"],
				selectedPath = __sceneViewSelectedPath( view )
			)
		}
	)

def connectToEditor( editor ) :

	if isinstance( editor, GafferUI.Viewer ) :
		editor.keyPressSignal().connect( __viewerKeyPress, scoped = False )

##########################################################################
# Internal implementation
##########################################################################

def __historySubMenu( menu, context, scene, selectedPath ) :

	menuDefinition = IECore.MenuDefinition()

	menuDefinition.append(
		"/Edit Source...",
		{
			"active" : selectedPath is not None,
			"command" : functools.partial( __editSourceNode, context, scene, selectedPath ),
			"shortCut" : "Alt+E",
		}
	)

	menuDefinition.append(
		"/Edit Tweaks...",
		{
			"active" : selectedPath is not None,
			"command" : functools.partial( __editTweaksNode, context, scene, selectedPath ),
			"shortCut" : "Alt+Shift+E",
		}
	)

	return menuDefinition

def __sceneViewSelectedPath( sceneView ) :

	sceneGadget = sceneView.viewportGadget().getPrimaryChild()
	if sceneGadget.getSelection().size() == 1 :
		return sceneGadget.getSelection().paths()[0]
	else :
		return None

def __editSourceNode( context, scene, path ) :

	with context :
		source = GafferScene.SceneAlgo.source( scene, path )

	if source is None :
		return

	node = source.node()
	node = __ancestorWithReadOnlyChildNodes( node ) or node
	GafferUI.NodeEditor.acquire( node, floating = True )

def __editTweaksNode( context, scene, path ) :

	with context :
		attributes = scene.fullAttributes( path )

	shaderAttributeNames = [ x[0] for x in attributes.items() if isinstance( x[1], IECoreScene.ShaderNetwork ) ]
	# Just happens to order as Surface, Light, Displacement, which is what we want.
	shaderAttributeNames = list( reversed( sorted( shaderAttributeNames ) ) )
	if not len( shaderAttributeNames ) :
		return

	with context :
		tweaks = GafferScene.SceneAlgo.shaderTweaks( scene, path, shaderAttributeNames[0] )

	if tweaks is None :
		return

	node = __ancestorWithReadOnlyChildNodes( tweaks ) or tweaks
	GafferUI.NodeEditor.acquire( node, floating = True )

def __ancestorWithReadOnlyChildNodes( node ) :

	result = None
	while isinstance( node, Gaffer.Node ) :
		if Gaffer.MetadataAlgo.getChildNodesAreReadOnly( node ) :
			result = node
		node = node.parent()

	return result

def __viewerKeyPress( viewer, event ) :

	view = viewer.view()
	if not isinstance( view, GafferSceneUI.SceneView ) :
		return False

	if event.key == "E" and event.modifiers == event.modifiers.Alt :
		selectedPath = __sceneViewSelectedPath( view )
		if selectedPath is not None :
			__editSourceNode( view.getContext(), view["in"], selectedPath )
		return True
	elif event.key == "E" and event.modifiers == event.modifiers.Alt | event.modifiers.Shift :
		selectedPath = __sceneViewSelectedPath( view )
		if selectedPath is not None :
			__editTweaksNode( view.getContext(), view["in"], selectedPath )
		return True
