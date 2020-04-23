##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

from .ArnoldShaderTest import ArnoldShaderTest
from .ArnoldRenderTest import ArnoldRenderTest
from .ArnoldOptionsTest import ArnoldOptionsTest
from .ArnoldAttributesTest import ArnoldAttributesTest
from .ArnoldVDBTest import ArnoldVDBTest
from .ArnoldLightTest import ArnoldLightTest
from .ArnoldMeshLightTest import ArnoldMeshLightTest
from .InteractiveArnoldRenderTest import InteractiveArnoldRenderTest
from .ArnoldDisplacementTest import ArnoldDisplacementTest
from .LightToCameraTest import LightToCameraTest
from .IECoreArnoldPreviewTest import *
from .ArnoldAOVShaderTest import ArnoldAOVShaderTest
from .ArnoldAtmosphereTest import ArnoldAtmosphereTest
from .ArnoldBackgroundTest import ArnoldBackgroundTest
from .ArnoldTextureBakeTest import ArnoldTextureBakeTest
from .ModuleTest import ModuleTest
from .ArnoldShaderBallTest import ArnoldShaderBallTest
from .ArnoldCameraShadersTest import ArnoldCameraShadersTest
from .ArnoldLightFilterTest import ArnoldLightFilterTest
from .ArnoldColorManagerTest import ArnoldColorManagerTest

if __name__ == "__main__":
	import unittest
	unittest.main()
