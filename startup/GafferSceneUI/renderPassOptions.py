##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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
import GafferSceneUI

Gaffer.Metadata.registerValue( "option:renderPass:type", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
Gaffer.Metadata.registerValue( "option:renderPass:type", "preset:Standard", "" )
## \todo As part of the future great metadata reckoning, it would make more sense for renderPassTypePresetNames to be defined as
# part of this global metadata rather than by GafferSceneUI.RenderPassTypeAdaptorUI and then called here. This would also allow
# the registrations in this file to be combined with those in `startup/GafferScene/renderPassOptions.py`.
Gaffer.Metadata.registerValue( "option:renderPass:type", "presetNames", GafferSceneUI.RenderPassTypeAdaptorUI.renderPassTypePresetNames )
Gaffer.Metadata.registerValue( "option:renderPass:type", "presetValues", GafferSceneUI.RenderPassTypeAdaptorUI.renderPassTypePresetValues )
