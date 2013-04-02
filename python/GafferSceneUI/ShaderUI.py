##########################################################################
#  
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import GafferScene

##########################################################################
# PlugValueWidgets
##########################################################################

GafferUI.PlugValueWidget.registerCreator( GafferScene.Shader.staticTypeId(), "parameters", GafferUI.CompoundPlugValueWidget, collapsed=None )
GafferUI.PlugValueWidget.registerCreator( GafferScene.Shader.staticTypeId(), "out", None )

##########################################################################
# NodeGadgets and Nodules
##########################################################################

def __nodeGadgetCreator( node ) :

	return GafferUI.StandardNodeGadget( node, GafferUI.LinearContainer.Orientation.Y )

GafferUI.NodeGadget.registerNodeGadget( GafferScene.Shader.staticTypeId(), __nodeGadgetCreator )

def __parametersNoduleCreator( plug ) :

	return GafferUI.CompoundNodule( plug, GafferUI.LinearContainer.Orientation.Y )

GafferUI.Nodule.registerNodule( GafferScene.Shader.staticTypeId(), "parameters", __parametersNoduleCreator )

# we leave it to the derived class uis to register creators for the parameters.* plugs, because only the derived classes know whether
# or not networkability makes sense in each case.
