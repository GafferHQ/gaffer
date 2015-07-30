##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
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

__import__( "IECore" )

from _Gaffer import *
from About import About
from Application import Application
from WeakMethod import WeakMethod
from BlockedConnection import BlockedConnection
from FileNamePathFilter import FileNamePathFilter
from UndoContext import UndoContext
from Context import Context
from InfoPathFilter import InfoPathFilter
from LazyModule import lazyImport, LazyModule
from DictPath import DictPath
from PythonExpressionEngine import PythonExpressionEngine
from SequencePath import SequencePath
from GraphComponentPath import GraphComponentPath
from OutputRedirection import OutputRedirection
from LocalDispatcher import LocalDispatcher
from SystemCommand import SystemCommand
from TaskList import TaskList
from TaskContextProcessor import TaskContextProcessor
from Wedge import Wedge
from TaskContextVariables import TaskContextVariables

import NodeAlgo

__import__( "IECore" ).loadConfig( "GAFFER_STARTUP_PATHS", {}, subdirectory = "Gaffer" )
