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
layouts.registerEditor( "ScriptEditor" )
layouts.registerEditor( "Timeline" )
layouts.registerEditor( "UIEditor" )
layouts.registerEditor( "AnimationEditor" )

# register some predefined layouts

layouts.add( "Standard", "GafferUI.CompoundEditor( scriptNode, children = ( GafferUI.SplitContainer.Orientation.Vertical, 0.97, ( ( GafferUI.SplitContainer.Orientation.Horizontal, 0.70, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.48, ( {'tabs': (GafferUI.Viewer( scriptNode ),), 'tabsVisible': True, 'currentTab': 0}, {'tabs': (GafferUI.GraphEditor( scriptNode ), GafferUI.AnimationEditor( scriptNode )), 'tabsVisible': True, 'currentTab': 0} ) ), ( GafferUI.SplitContainer.Orientation.Vertical, 0.54, ( {'tabs': (GafferUI.NodeEditor( scriptNode ), GafferSceneUI.SceneInspector( scriptNode )), 'tabsVisible': True, 'currentTab': 0}, {'tabs': (GafferSceneUI.HierarchyView( scriptNode ), GafferUI.ScriptEditor( scriptNode )), 'tabsVisible': True, 'currentTab': 0} ) ) ) ), {'tabs': (GafferUI.Timeline( scriptNode ),), 'tabsVisible': False, 'currentTab': 0} ) ) )" )
layouts.add( "Scene", "GafferUI.CompoundEditor( scriptNode, children = ( GafferUI.SplitContainer.Orientation.Horizontal, 0.772395, ( ( GafferUI.SplitContainer.Orientation.Horizontal, 0.256257, ( {'tabs': (GafferSceneUI.HierarchyView( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False]}, ( GafferUI.SplitContainer.Orientation.Vertical, 0.500620, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.929648, ( {'tabs': (GafferUI.Viewer( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False]}, {'tabs': (GafferUI.Timeline( scriptNode ),), 'tabsVisible': False, 'currentTab': 0, 'pinned': [None]} ) ), {'tabs': (GafferUI.GraphEditor( scriptNode ), GafferUI.AnimationEditor( scriptNode )), 'tabsVisible': True, 'currentTab': 0, 'pinned': [None, None]} ) ) ) ), ( GafferUI.SplitContainer.Orientation.Vertical, 0.500620, ( {'tabs': (GafferUI.NodeEditor( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False]}, {'tabs': (GafferSceneUI.SceneInspector( scriptNode ),), 'tabsVisible': True, 'currentTab': 0, 'pinned': [False]} ) ) ) ) )" )
layouts.add( "Empty", "GafferUI.CompoundEditor( scriptNode )" )

layouts.setDefault( "Standard" )
