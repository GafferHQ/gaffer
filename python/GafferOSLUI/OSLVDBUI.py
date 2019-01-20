##########################################################################
#
#  Copyright (c) 2013-2014, Don Boogert. All rights reserved.
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
#      * Neither the name of Don Boogert nor the names of
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

import IECore
import IECoreScene
import Gaffer
import GafferUI

import GafferOSL

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

    GafferOSL.OSLVDB,

    "description",
    """
    Executes OSL shaders to perform VDB processing. Use the shaders from
    the OSL/ObjectProcessing menu to read grid data from the input
    VDB object and then write grids data back to it.
    """,

    plugs = {

        "shader" : [

            "description",
            """
            The shader to be executed - connect the output from an OSL network here.
            A minimal shader network to process P would look like this :

                InPoint->ProcessingNodes->OutPoint->OutObject
            """,

            "nodule:type", "GafferUI::StandardNodule",
            "noduleLayout:section", "left",

        ],

        "grid" : [

            "description",
            """
            Which grid to iterate over. Other grids can be read in the shader network but this grid is used to define
            the shading domain & sampling rate. If a new grid is created in shader network then it will be created
            with a matching resolution to this grid. 
            """,

        ],

        "mode" : [
            "description",
            """
            Should we shade or all cells in the grid or only active cells or inactive cells.
            """,

            "preset:AllCells", 0,
            "preset:ActiveCells", 1,
            "preset:InactiveCells", 2,

            "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

        ]

    }

)

