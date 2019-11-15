##########################################################################
#
#  Copyright (c) 2018, Alex Fuller. All rights reserved.
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

## Node creation menu
###########################################################################

import os
import re
import traceback
import functools

import IECore

import Gaffer
import GafferScene
import GafferUI
import GafferSceneUI

moduleSearchPath = IECore.SearchPath( os.environ["PYTHONPATH"] )

nodeMenu = GafferUI.NodeMenu.acquire( application )

if moduleSearchPath.find( "GafferCycles" ) :

	try :

		import GafferCycles
		import GafferCyclesUI

		GafferCyclesUI.ShaderMenu.appendShaders( nodeMenu.definition() )

		nodeMenu.append( "/Cycles/Globals/Options", GafferCycles.CyclesOptions, searchText = "CyclesOptions" )
		nodeMenu.append( "/Cycles/Globals/Background", GafferCycles.CyclesBackground, searchText = "CyclesBackground" )
		nodeMenu.append( "/Cycles/Attributes", GafferCycles.CyclesAttributes, searchText = "CyclesAttributes" )
		nodeMenu.append(
			"/Cycles/Render", GafferCycles.CyclesRender,
			searchText = "CyclesRender"
		)
		nodeMenu.append( "/Cycles/Interactive Render", GafferCycles.InteractiveCyclesRender, searchText = "InteractiveCyclesRender" )
		nodeMenu.append( "/Cycles/Shader Ball", GafferCycles.CyclesShaderBall, searchText = "CyclesShaderBall" )

	except Exception, m :

		stacktrace = traceback.format_exc()
		IECore.msg( IECore.Msg.Level.Error, "startup/gui/menus.py", "Error loading Cycles module - \"%s\".\n %s" % ( m, stacktrace ) )
