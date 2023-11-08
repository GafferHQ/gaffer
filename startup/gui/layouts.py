##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

layouts = GafferUI.Layouts.acquire( application )

# register the editors we want to be available to the user

layouts.registerEditor( "Viewer" )
layouts.registerEditor( "NodeEditor" )
layouts.registerEditor( "GraphEditor" )
layouts.registerEditor( "HierarchyView" )
layouts.registerEditor( "LightEditor" )
layouts.registerEditor( "SceneInspector" )
layouts.registerEditor( "SetEditor" )
layouts.registerEditor( "PythonEditor" )
layouts.registerEditor( "Timeline" )
layouts.registerEditor( "UIEditor" )
layouts.registerEditor( "AnimationEditor" )
layouts.registerEditor( "PrimitiveInspector")
layouts.registerEditor( "UVInspector")
layouts.registerEditor( "LocalJobs" )

# Register some predefined layouts
#
# > Note : The easiest way to edit these layouts is to :
# >
# >  - Edit the layout in Gaffer itself
# >  - Save the layout so that it is serialised to `${HOME}/gaffer/startup/gui/layouts.py`
# >  - Copy the layout back into this file
#
# > Caution : You _must_ omit the `persistent = True` argument when copying layouts into
# > this file, to prevent the standard layouts from being serialised into the user's own
# > preferences.

layouts.add( 'Standard', "GafferUI.CompoundEditor( scriptNode, _state={ 'children' : ( GafferUI.SplitContainer.Orientation.Vertical, 0.974608, ( ( GafferUI.SplitContainer.Orientation.Horizontal, 0.699765, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.479631, ( {'tabs': (GafferUI.Viewer( scriptNode ), GafferSceneUI.UVInspector( scriptNode ), GafferDispatchUI.LocalJobs( scriptNode )), 'currentTab': 0, 'tabsVisible': True}, {'tabs': (GafferUI.GraphEditor( scriptNode ), GafferSceneUI.LightEditor( scriptNode ), GafferUI.AnimationEditor( scriptNode ), GafferSceneUI.PrimitiveInspector( scriptNode )), 'currentTab': 0, 'tabsVisible': True} ) ), ( GafferUI.SplitContainer.Orientation.Vertical, 0.538816, ( {'tabs': (GafferUI.NodeEditor( scriptNode ), GafferSceneUI.SceneInspector( scriptNode ), GafferSceneUI.SetEditor( scriptNode )), 'currentTab': 0, 'tabsVisible': True}, {'tabs': (GafferSceneUI.HierarchyView( scriptNode ), GafferUI.PythonEditor( scriptNode )), 'currentTab': 0, 'tabsVisible': True} ) ) ) ), {'tabs': (GafferUI.Timeline( scriptNode ),), 'currentTab': 0, 'tabsVisible': False} ) ), 'detachedPanels' : (), 'windowState' : { 'screen' : -1, 'fullScreen' : False, 'maximized' : True, 'bound' : imath.Box2f( imath.V2f( 0, 0.377211601 ), imath.V2f( 0.384375006, 0.973814607 ) ) }, 'editorState' : {'c-0-0-0-0-0': {'nodeSet': 'scriptNode.focusSet()'}, 'c-0-0-0-0-1': {'nodeSet': 'scriptNode.focusSet()'}, 'c-0-0-1-0-1': {'nodeSet': 'scriptNode.focusSet()'}, 'c-0-0-1-0-3': {'nodeSet': 'scriptNode.focusSet()'}, 'c-0-1-0-0-1': {'nodeSet': 'scriptNode.focusSet()'}, 'c-0-1-0-0-2': {'nodeSet': 'scriptNode.focusSet()'}, 'c-0-1-1-0-0': {'nodeSet': 'scriptNode.focusSet()'}} } )" )
layouts.add( 'Standard (multi-monitor)', "GafferUI.CompoundEditor( scriptNode, _state={ 'children' : ( GafferUI.SplitContainer.Orientation.Vertical, 0.974608, ( ( GafferUI.SplitContainer.Orientation.Horizontal, 0.699765, ( {'tabs': (GafferUI.GraphEditor( scriptNode ), GafferSceneUI.LightEditor( scriptNode ), GafferUI.AnimationEditor( scriptNode ), GafferSceneUI.PrimitiveInspector( scriptNode )), 'currentTab': 0, 'tabsVisible': True}, ( GafferUI.SplitContainer.Orientation.Vertical, 0.538816, ( {'tabs': (GafferUI.NodeEditor( scriptNode ), GafferSceneUI.SceneInspector( scriptNode ), GafferSceneUI.SetEditor( scriptNode )), 'currentTab': 0, 'tabsVisible': True}, {'tabs': (GafferSceneUI.HierarchyView( scriptNode ), GafferUI.PythonEditor( scriptNode )), 'currentTab': 0, 'tabsVisible': True} ) ) ) ), {'tabs': (GafferUI.Timeline( scriptNode ),), 'currentTab': 0, 'tabsVisible': False} ) ), 'detachedPanels' : ( { 'children' : {'tabs': (GafferUI.Viewer( scriptNode ), GafferSceneUI.UVInspector( scriptNode ), GafferDispatchUI.LocalJobs( scriptNode )), 'currentTab': 0, 'tabsVisible': True}, 'windowState' : { 'screen' : -1, 'fullScreen' : False, 'maximized' : False, 'bound' : imath.Box2f( imath.V2f( 0.104492188, 0.107572541 ), imath.V2f( 0.838867188, 0.903750896 ) ) } }, ), 'windowState' : { 'screen' : -1, 'fullScreen' : False, 'maximized' : True, 'bound' : imath.Box2f( imath.V2f( 0, 0.377211601 ), imath.V2f( 0.384375006, 0.973814607 ) ) }, 'editorState' : {'c-0-0-0-1': {'nodeSet': 'scriptNode.focusSet()'}, 'c-0-0-0-3': {'nodeSet': 'scriptNode.focusSet()'}, 'c-0-1-0-0-1': {'nodeSet': 'scriptNode.focusSet()'}, 'c-0-1-0-0-2': {'nodeSet': 'scriptNode.focusSet()'}, 'c-0-1-1-0-0': {'nodeSet': 'scriptNode.focusSet()'}, 'p-0-0-0': {'nodeSet': 'scriptNode.focusSet()'}, 'p-0-0-1': {'nodeSet': 'scriptNode.focusSet()'}} } )" )
layouts.add( "Empty", "GafferUI.CompoundEditor( scriptNode, windowState = {'fullScreen': False, 'screen': -1, 'bound': imath.Box2f(imath.V2f(0.0479166657, 0.108269393), imath.V2f(0.782812476, 0.906223357)), 'maximized': True} )" )
layouts.add( 'Scene', "GafferUI.CompoundEditor( scriptNode, _state={ 'children' : ( GafferUI.SplitContainer.Orientation.Horizontal, 0.772425, ( ( GafferUI.SplitContainer.Orientation.Horizontal, 0.255838, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.501120, ( {'tabs': (GafferSceneUI.HierarchyView( scriptNode ),), 'currentTab': 0, 'tabsVisible': True}, {'tabs': (GafferSceneUI.SetEditor( scriptNode ),), 'currentTab': 0, 'tabsVisible': True} ) ), ( GafferUI.SplitContainer.Orientation.Vertical, 0.501120, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.949025, ( {'tabs': (GafferUI.Viewer( scriptNode ), GafferSceneUI.UVInspector( scriptNode ), GafferDispatchUI.LocalJobs( scriptNode )), 'currentTab': 0, 'tabsVisible': True}, {'tabs': (GafferUI.Timeline( scriptNode ),), 'currentTab': 0, 'tabsVisible': False} ) ), {'tabs': (GafferUI.GraphEditor( scriptNode ), GafferSceneUI.LightEditor( scriptNode ), GafferUI.AnimationEditor( scriptNode ), GafferSceneUI.PrimitiveInspector( scriptNode )), 'currentTab': 0, 'tabsVisible': True} ) ) ) ), ( GafferUI.SplitContainer.Orientation.Vertical, 0.501120, ( {'tabs': (GafferUI.NodeEditor( scriptNode ),), 'currentTab': 0, 'tabsVisible': True}, {'tabs': (GafferSceneUI.SceneInspector( scriptNode ),), 'currentTab': 0, 'tabsVisible': True} ) ) ) ), 'detachedPanels' : (), 'windowState' : { 'screen' : -1, 'fullScreen' : False, 'maximized' : True, 'bound' : imath.Box2f( imath.V2f( 0, 0.377211601 ), imath.V2f( 0.384375006, 0.973814607 ) ) }, 'editorState' : {'c-0-0-0-0-0': {'nodeSet': 'scriptNode.focusSet()'}, 'c-0-0-1-0-0': {'nodeSet': 'scriptNode.focusSet()'}, 'c-0-1-0-0-0-0': {'nodeSet': 'scriptNode.focusSet()'}, 'c-0-1-0-0-0-1': {'nodeSet': 'scriptNode.focusSet()'}, 'c-0-1-1-0-1': {'nodeSet': 'scriptNode.focusSet()'}, 'c-0-1-1-0-3': {'nodeSet': 'scriptNode.focusSet()'}, 'c-1-1-0-0': {'nodeSet': 'scriptNode.focusSet()'}} } )" )

layouts.setDefault( "Standard" )

