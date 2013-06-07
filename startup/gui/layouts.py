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

layouts.add( "Default", "GafferUI.CompoundEditor( scriptNode, children = ( GafferUI.SplitContainer.Orientation.Horizontal, 0.5, ( ( GafferUI.SplitContainer.Orientation.Vertical, 0.5, ( (GafferUI.Viewer( scriptNode ),), (GafferUI.NodeGraph( scriptNode ),) ) ), ( GafferUI.SplitContainer.Orientation.Vertical, 0.5, ( (GafferUI.NodeEditor( scriptNode ),), (GafferUI.ScriptEditor( scriptNode ),) ) ) ) ) )" )
layouts.add( "Scene", "GafferUI.CompoundEditor( scriptNode, children = ( GafferUI.SplitContainer.Orientation.Horizontal, 0.772664, ( ( GafferUI.SplitContainer.Orientation.Horizontal, 0.255898, ( (GafferSceneUI.SceneHierarchy( scriptNode ),), ( GafferUI.SplitContainer.Orientation.Vertical, 0.500000, ( ( GafferUI.SplitContainer.Orientation.Vertical, 1.000000, ( (GafferUI.Viewer( scriptNode ),), (GafferUI.Timeline( scriptNode ),) ) ), (GafferUI.NodeGraph( scriptNode ),) ) ) ) ), ( GafferUI.SplitContainer.Orientation.Vertical, 0.500000, ( (GafferUI.NodeEditor( scriptNode ),), (GafferSceneUI.SceneInspector( scriptNode ),) ) ) ) ) )" )
layouts.add( "Empty", "GafferUI.CompoundEditor( scriptNode )" )

del layouts # avoid polluting the namespace for other config files
