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

layouts.add( "Standard", "GafferUI.CompoundEditor( scriptNode, children = ( GafferUI.SplitContainer.Orientation.Vertical, 0.953556, ( ( GafferUI.SplitContainer.Orientation.Horizontal, 0.699552, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.479263, ( {'tabs': (GafferUI.Viewer( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False]}, {'tabs': (GafferUI.GraphEditor( scriptNode ), GafferUI.AnimationEditor( scriptNode ), GafferSceneUI.PrimitiveInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [None, False, False]} ) ), ( GafferUI.SplitContainer.Orientation.Vertical, 0.539171, ( {'tabs': (GafferUI.NodeEditor( scriptNode ), GafferSceneUI.SceneInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False, False]}, {'tabs': (GafferSceneUI.HierarchyView( scriptNode ), GafferUI.PythonEditor( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False, None]} ) ) ) ), {'tabs': (GafferUI.Timeline( scriptNode ),), 'tabsVisible': False, 'currentTab': 0, 'pinned': [None]} ) ), windowState = {'fullScreen': False, 'screen': -1, 'bound': imath.Box2f(imath.V2f(0.0479166657, 0.108269393), imath.V2f(0.782812476, 0.906223357)), 'maximized': True} )" )
layouts.add( "Scene", "GafferUI.CompoundEditor( scriptNode, children = ( GafferUI.SplitContainer.Orientation.Horizontal, 0.772595, ( ( GafferUI.SplitContainer.Orientation.Horizontal, 0.256020, ( {'tabs': (GafferSceneUI.HierarchyView( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False]}, ( GafferUI.SplitContainer.Orientation.Vertical, 0.500726, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.905605, ( {'tabs': (GafferUI.Viewer( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False]}, {'tabs': (GafferUI.Timeline( scriptNode ),), 'tabsVisible': False, 'currentTab': 0, 'pinned': [None]} ) ), {'tabs': (GafferUI.GraphEditor( scriptNode ), GafferUI.AnimationEditor( scriptNode ), GafferSceneUI.PrimitiveInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [None, False, False]} ) ) ) ), ( GafferUI.SplitContainer.Orientation.Vertical, 0.500726, ( {'tabs': (GafferUI.NodeEditor( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False]}, {'tabs': (GafferSceneUI.SceneInspector( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False]} ) ) ) ), windowState = {'fullScreen': False, 'screen': -1, 'bound': imath.Box2f(imath.V2f(0.0479166657, 0.108269393), imath.V2f(0.782812476, 0.906223357)), 'maximized': True} )" )
layouts.add( "Empty", "GafferUI.CompoundEditor( scriptNode, windowState = {'fullScreen': False, 'screen': -1, 'bound': imath.Box2f(imath.V2f(0.0479166657, 0.108269393), imath.V2f(0.782812476, 0.906223357)), 'maximized': True} )" )
layouts.add( "Standard (multi-monitor)", "GafferUI.CompoundEditor( scriptNode, children = ( GafferUI.SplitContainer.Orientation.Vertical, 0.962667, ( ( GafferUI.SplitContainer.Orientation.Horizontal, 0.699582, ( {'tabs': (GafferUI.GraphEditor( scriptNode ), GafferUI.AnimationEditor( scriptNode ), GafferSceneUI.PrimitiveInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [None, False, False]}, ( GafferUI.SplitContainer.Orientation.Vertical, 0.539461, ( {'tabs': (GafferUI.NodeEditor( scriptNode ), GafferSceneUI.SceneInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False, False]}, {'tabs': (GafferSceneUI.HierarchyView( scriptNode ), GafferUI.PythonEditor( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False, None]} ) ) ) ), {'tabs': (GafferUI.Timeline( scriptNode ),), 'tabsVisible': False, 'currentTab': 0, 'pinned': [None]} ) ), detachedPanels = [ { 'children': {'tabs': (GafferUI.Viewer( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False]}, 'windowState': {'fullScreen': False, 'screen': 1, 'bound': imath.Box2f(imath.V2f(0.0479166657, 0.108269393), imath.V2f(0.782812476, 0.906223357)), 'maximized': True} } ], windowState = {'fullScreen': False, 'screen': -1, 'bound': imath.Box2f(imath.V2f(0.0479166657, 0.108269393), imath.V2f(0.782812476, 0.906223357)), 'maximized': True} )" )

layouts.setDefault( "Standard" )

