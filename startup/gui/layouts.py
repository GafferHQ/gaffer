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
layouts.registerEditor( "SceneInspector" )
layouts.registerEditor( "PythonEditor" )
layouts.registerEditor( "Timeline" )
layouts.registerEditor( "UIEditor" )
layouts.registerEditor( "AnimationEditor" )
layouts.registerEditor( "PrimitiveInspector")
layouts.registerEditor( "UVInspector")

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

layouts.add( 'Standard', "GafferUI.CompoundEditor( scriptNode, _state={ 'children' : ( GafferUI.SplitContainer.Orientation.Vertical, 0.953488, ( ( GafferUI.SplitContainer.Orientation.Horizontal, 0.699857, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.479580, ( {'tabs': (GafferUI.Viewer( scriptNode ), GafferSceneUI.UVInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False, False]}, {'tabs': (GafferUI.GraphEditor( scriptNode ), GafferUI.AnimationEditor( scriptNode ), GafferSceneUI.PrimitiveInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [None, False, False]} ) ), ( GafferUI.SplitContainer.Orientation.Vertical, 0.539090, ( {'tabs': (GafferUI.NodeEditor( scriptNode ), GafferSceneUI.SceneInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False, False]}, {'tabs': (GafferSceneUI.HierarchyView( scriptNode ), GafferUI.PythonEditor( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False, None]} ) ) ) ), {'tabs': (GafferUI.Timeline( scriptNode ),), 'tabsVisible': False, 'currentTab': 0, 'pinned': [None]} ) ), 'detachedPanels' : (), 'windowState' : { 'fullScreen' : False, 'screen' : -1, 'bound' : imath.Box2f( imath.V2f( 0.0473958328, 0.108751059 ), imath.V2f( 0.781770825, 0.906542063 ) ), 'maximized' : True }, 'editorState' : { 'c-0-0-0-0-0': {'nodeSet': 'Gaffer.FocusNodeSet( scriptNode )'}, 'c-0-1-1-0-0': {'nodeSet': 'Gaffer.FocusNodeSet( scriptNode )'}, 'c-0-1-0-0-1': {'nodeSet': 'Gaffer.FocusNodeSet( scriptNode )'}, 'c-0-0-1-0-2': {'nodeSet': 'Gaffer.FocusNodeSet( scriptNode )'}, 'c-0-0-0-0-1': {'nodeSet': 'Gaffer.FocusNodeSet( scriptNode )'}} } )" )
layouts.add( 'Standard (multi-monitor)', "GafferUI.CompoundEditor( scriptNode, _state={ 'children' : ( GafferUI.SplitContainer.Orientation.Vertical, 0.953488, ( ( GafferUI.SplitContainer.Orientation.Horizontal, 0.699857, ( {'tabs': (GafferUI.GraphEditor( scriptNode ), GafferUI.AnimationEditor( scriptNode ), GafferSceneUI.PrimitiveInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [None, False, False]}, ( GafferUI.SplitContainer.Orientation.Vertical, 0.539090, ( {'tabs': (GafferUI.NodeEditor( scriptNode ), GafferSceneUI.SceneInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False, False]}, {'tabs': (GafferSceneUI.HierarchyView( scriptNode ), GafferUI.PythonEditor( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False, None]} ) ) ) ), {'tabs': (GafferUI.Timeline( scriptNode ),), 'tabsVisible': False, 'currentTab': 0, 'pinned': [None]} ) ), 'detachedPanels' : ( { 'children' : {'tabs': (GafferUI.Viewer( scriptNode ), GafferSceneUI.UVInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False, False]}, 'windowState' : { 'fullScreen' : False, 'screen' : 1, 'bound' : imath.Box2f( imath.V2f( 0.0472222231, 0.108888887 ), imath.V2f( 0.781944454, 0.906666696 ) ), 'maximized' : True } }, ), 'windowState' : { 'fullScreen' : False, 'screen' : -1, 'bound' : imath.Box2f( imath.V2f( 0.0473958328, 0.108751059 ), imath.V2f( 0.781770825, 0.906542063 ) ), 'maximized' : True }, 'editorState' : {'c-0-0-0-2': {'nodeSet': 'Gaffer.FocusNodeSet( scriptNode )'}, 'c-0-1-0-0-1': {'nodeSet': 'Gaffer.FocusNodeSet( scriptNode )'}, 'c-0-1-1-0-0': {'nodeSet': 'Gaffer.FocusNodeSet( scriptNode )'}, 'p-0-0-1': {'nodeSet': 'Gaffer.FocusNodeSet( scriptNode )'}} } )" )
layouts.add( "Empty", "GafferUI.CompoundEditor( scriptNode, windowState = {'fullScreen': False, 'screen': -1, 'bound': imath.Box2f(imath.V2f(0.0479166657, 0.108269393), imath.V2f(0.782812476, 0.906223357)), 'maximized': True} )" )
layouts.add( 'Scene', "GafferUI.CompoundEditor( scriptNode, _state={ 'children' : ( GafferUI.SplitContainer.Orientation.Horizontal, 0.772206, ( ( GafferUI.SplitContainer.Orientation.Horizontal, 0.256052, ( {'tabs': (GafferSceneUI.HierarchyView( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False]}, ( GafferUI.SplitContainer.Orientation.Vertical, 0.500554, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.906250, ( {'tabs': (GafferUI.Viewer( scriptNode ), GafferSceneUI.UVInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False, False]}, {'tabs': (GafferUI.Timeline( scriptNode ),), 'tabsVisible': False, 'currentTab': 0, 'pinned': [None]} ) ), {'tabs': (GafferUI.GraphEditor( scriptNode ), GafferUI.AnimationEditor( scriptNode ), GafferSceneUI.PrimitiveInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [None, False, False]} ) ) ) ), ( GafferUI.SplitContainer.Orientation.Vertical, 0.500554, ( {'tabs': (GafferUI.NodeEditor( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False]}, {'tabs': (GafferSceneUI.SceneInspector( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False]} ) ) ) ), 'detachedPanels' : (), 'windowState' : { 'fullScreen' : False, 'screen' : -1, 'bound' : imath.Box2f( imath.V2f( 0.046875, 0.109600678 ), imath.V2f( 0.78125, 0.907391667 ) ), 'maximized' : True }, 'editorState' : {'c-0-1-1-0-2': {'nodeSet': 'Gaffer.FocusNodeSet( scriptNode )'}, 'c-0-0-0-0': {'nodeSet': 'Gaffer.FocusNodeSet( scriptNode )'}, 'c-1-1-0-0': {'nodeSet': 'Gaffer.FocusNodeSet( scriptNode )'}, 'c-0-1-0-0-0-1': {'nodeSet': 'Gaffer.FocusNodeSet( scriptNode )'}} } )" )

layouts.setDefault( "Standard" )

