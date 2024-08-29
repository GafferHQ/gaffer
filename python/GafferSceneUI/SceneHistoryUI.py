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
	elif isinstance( editor, GafferSceneUI.HierarchyView ) or isinstance( editor, GafferSceneUI.LightEditor ) :
		editor.keyPressSignal().connect( __hierarchyViewKeyPress, scoped = False )
	elif isinstance( editor, GafferUI.NodeEditor ) :
		editor.keyPressSignal().connect( __nodeEditorKeyPress, scoped = False )

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

def __contextSelectedPath( context ) :

	selection = GafferSceneUI.ContextAlgo.getSelectedPaths( context )
	if selection.size() != 1 :
		return None

	return selection.paths()[0]

def __editSourceNode( context, scene, path, nodeEditor = None ) :

	with context :
		source = GafferScene.SceneAlgo.source( scene, path )

	if source is None :
		return

	node = source.node()
	node = __ancestorWithNonViewableChildNodes( node ) or node
	if nodeEditor is not None :
		nodeEditor.setNodeSet( Gaffer.StandardSet( [ node ] ) )
	else :
		GafferUI.NodeEditor.acquire( node, floating = True )

def __tweaksNode( scene, path ) :

	tweaks = GafferScene.SceneAlgo.objectTweaks( scene, path )
	if tweaks is not None :
		return tweaks

	attributes = scene.fullAttributes( path )

	shaderAttributeNames = [ x[0] for x in attributes.items() if isinstance( x[1], IECoreScene.ShaderNetwork ) ]
	# Just happens to order as Surface, Light, Displacement, which is what we want.
	shaderAttributeNames = list( reversed( sorted( shaderAttributeNames ) ) )
	if not len( shaderAttributeNames ) :
		return None

	return GafferScene.SceneAlgo.shaderTweaks( scene, path, shaderAttributeNames[0] )

def __editTweaksNode( context, scene, path, nodeEditor = None ) :

	with context :
		tweaks = __tweaksNode( scene, path )

	if tweaks is None :
		return

	node = __ancestorWithNonViewableChildNodes( tweaks ) or tweaks
	if nodeEditor is not None :
		nodeEditor.setNodeSet( Gaffer.StandardSet( [ node ] ) )
	else :
		GafferUI.NodeEditor.acquire( node, floating = True )

def __ancestorWithNonViewableChildNodes( node ) :

	result = None
	while isinstance( node, Gaffer.Node ) :
		if Gaffer.Metadata.value( node, "graphEditor:childrenViewable" ) == False :
			result = node
		node = node.parent()

	return result

__editSourceKeyPress = GafferUI.KeyEvent( "E", GafferUI.KeyEvent.Modifiers.Alt )
__editTweaksKeyPress = GafferUI.KeyEvent(
	"E",
	GafferUI.KeyEvent.Modifiers(
		GafferUI.KeyEvent.Modifiers.Alt | GafferUI.KeyEvent.Modifiers.Shift
	)
)

def __viewerKeyPress( viewer, event ) :

	view = viewer.view()
	if not isinstance( view, GafferSceneUI.SceneView ) :
		return False

	if event == __editSourceKeyPress :
		selectedPath = __sceneViewSelectedPath( view )
		if selectedPath is not None :
			__editSourceNode( view.getContext(), view["in"], selectedPath )
		return True
	elif event == __editTweaksKeyPress :
		selectedPath = __sceneViewSelectedPath( view )
		if selectedPath is not None :
			__editTweaksNode( view.getContext(), view["in"], selectedPath )
		return True

def __hierarchyViewKeyPress( hierarchyView, event ) :

	if event == __editSourceKeyPress :
		selectedPath = __contextSelectedPath( hierarchyView.context() )
		if selectedPath is not None :
			__editSourceNode( hierarchyView.context(), hierarchyView.scene(), selectedPath )
		return True
	elif event == __editTweaksKeyPress :
		selectedPath = __contextSelectedPath( hierarchyView.context() )
		if selectedPath is not None :
			__editTweaksNode( hierarchyView.context(), hierarchyView.scene(), selectedPath )
		return True

def __nodeEditorKeyPress( nodeEditor, event ) :

	focusNode = nodeEditor.scriptNode().getFocus()
	if focusNode is None :
		return False

	scene = next(
		( p for p in GafferScene.ScenePlug.RecursiveOutputRange( focusNode ) if not p.getName().startswith( "__" ) ),
		None
	)

	if scene is None :
		return False

	context = nodeEditor.scriptNode().context()

	if event == __editSourceKeyPress :
		selectedPath = __contextSelectedPath( context )
		if selectedPath is not None :
			__editSourceNode( context, scene, selectedPath, nodeEditor )
		return True
	elif event == __editTweaksKeyPress :
		selectedPath = __contextSelectedPath( context )
		if selectedPath is not None :
			__editTweaksNode( context, scene, selectedPath, nodeEditor )
		return True
