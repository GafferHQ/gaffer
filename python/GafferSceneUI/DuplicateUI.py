##########################################################################
#  
#  Copyright (c) 2014, John Haddon. All rights reserved.
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

import Gaffer
import GafferUI

import GafferScene

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNodeDescription(

GafferScene.Duplicate,

"""Duplicates elements of a scene.""",

"target",
"The element to be duplicated.",

"copies",
"""The number of copies to be made.""",

"transform",
"""The transform to be applied to the copies.""",

)

##########################################################################
# Widgets and nodules
##########################################################################

# we hide the parent (which comes from the base class) because the value for it is
# computed from the target plug automatically.
GafferUI.PlugValueWidget.registerCreator( GafferScene.Duplicate.staticTypeId(), "parent", None )

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.Duplicate.staticTypeId(),
	"target",
	lambda plug : GafferUI.PathPlugValueWidget(
		plug,
		path = GafferScene.ScenePath( plug.node()["in"], plug.node().scriptNode().context(), "/" ),
	),
)

GafferUI.PlugValueWidget.registerCreator( GafferScene.Duplicate.staticTypeId(), "transform", GafferUI.TransformPlugValueWidget, collapsed=None )
