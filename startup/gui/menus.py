##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import os

import IECore

import Gaffer
import GafferScene
import GafferUI
import GafferSceneUI

# ScriptWindow menu

scriptWindowMenu = GafferUI.ScriptWindow.menuDefinition()

GafferUI.ApplicationMenu.appendDefinitions( scriptWindowMenu, prefix="/Gaffer" )
GafferUI.FileMenu.appendDefinitions( scriptWindowMenu, prefix="/File" )
GafferUI.EditMenu.appendDefinitions( scriptWindowMenu, prefix="/Edit" )
GafferUI.LayoutMenu.appendDefinitions( scriptWindowMenu, name="/Layout" )

# Node menu

GafferUI.NodeMenu.append( "/Scene/Source/ModelCache", GafferScene.ModelCacheSource )
GafferUI.NodeMenu.append( "/Scene/Add/AttributeCache", GafferScene.AttributeCache )
GafferUI.NodeMenu.append( "/Scene/Merge/Group", GafferScene.GroupScenes )
GafferUI.NodeMenu.append( "/Scene/Delete/Primitive Variables", GafferScene.DeletePrimitiveVariables )

GafferUI.NodeMenu.append( "/File/Read", Gaffer.ReadNode )
GafferUI.NodeMenu.append( "/File/Write", Gaffer.WriteNode )

GafferUI.NodeMenu.append( "/Primitive/Sphere", Gaffer.SphereNode )
GafferUI.NodeMenu.append( "/Group", Gaffer.GroupNode )

GafferUI.NodeMenu.append( "/Utility/Expression", Gaffer.ExpressionNode )

GafferUI.NodeMenu.appendParameterisedHolders( "/Cortex/Ops", Gaffer.OpHolder, "IECORE_OP_PATHS" )
GafferUI.NodeMenu.appendParameterisedHolders( "/Cortex/Procedurals", Gaffer.ProceduralHolder, "IECORE_PROCEDURAL_PATHS" )
