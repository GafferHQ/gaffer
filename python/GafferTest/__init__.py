##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2015, Image Engine Design Inc. All rights reserved.
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

from _GafferTest import *

import os
import unittest

# workaround lack of expectedFailure decorator for
# python < 2.7.
try :
	expectedFailure = unittest.expectedFailure
except AttributeError :
	def expectedFailure( f ) :
		def wrapper( self ) :
			try :
				f( self )
			except :
				print "Expected failure"
		return wrapper

## Determines if the tests are running in a Continuous Integration
# environment.
def inCI( platforms = set() ) :

	platformVars = {
		# There isn't a specific 'We're on Azure' var (other than some azure specific
		# vars that are set that would be 'magic words'), so we set our own in our
		# azure-pipelines.yaml
		'azure' : 'AZURE'
	}

	targets = platforms or platformVars.keys()
	for t in targets :
		if platformVars[ t ] in os.environ :
			return True

	return False

from TestCase import TestCase
from TestRunner import TestRunner
from AddNode import AddNode
from SignalsTest import SignalsTest
from GraphComponentTest import GraphComponentTest
from FrameNode import FrameNode
from CachingTestNode import CachingTestNode
from NodeTest import NodeTest
from PlugTest import PlugTest
from NumericPlugTest import NumericPlugTest
from TypedPlugTest import TypedPlugTest
from ScriptNodeTest import ScriptNodeTest
from StandardSetTest import StandardSetTest
from FileSystemPathTest import FileSystemPathTest
from PathTest import PathTest
from PathFilterTest import PathFilterTest
from UndoTest import UndoTest
from KeywordPlugNode import KeywordPlugNode
from CompoundNumericPlugTest import CompoundNumericPlugTest
from CompoundNumericNode import CompoundNumericNode
from CompoundPlugNode import CompoundPlugNode
from TypedObjectPlugTest import TypedObjectPlugTest
from SplinePlugTest import SplinePlugTest
from AboutTest import AboutTest
from ChildSetTest import ChildSetTest
from PythonApplicationTest import PythonApplicationTest
from ApplicationRootTest import ApplicationRootTest
from ContextTest import ContextTest
from CompoundPathFilterTest import CompoundPathFilterTest
from BadNode import BadNode
from CapturingSlot import CapturingSlot
from LazyModuleTest import LazyModuleTest
from NodeBindingTest import NodeBindingTest
from DictPathTest import DictPathTest
from ExpressionTest import ExpressionTest
from BlockedConnectionTest import BlockedConnectionTest
from TimeWarpTest import TimeWarpTest
from TransformPlugTest import TransformPlugTest
from Transform2DPlugTest import Transform2DPlugTest
from SequencePathTest import SequencePathTest
from WeakMethodTest import WeakMethodTest
from StringInOutNode import StringInOutNode
from StringPlugTest import StringPlugTest
from ContextVariablesTest import ContextVariablesTest
from DeleteContextVariablesTest import DeleteContextVariablesTest
from ValuePlugTest import ValuePlugTest
from RandomTest import RandomTest
from CompoundDataPlugTest import CompoundDataPlugTest
from DependencyNodeTest import DependencyNodeTest
from ComputeNodeTest import ComputeNodeTest
from BoxPlugTest import BoxPlugTest
from BoxTest import BoxTest
from OutputRedirectionTest import OutputRedirectionTest
from RecursiveChildIteratorTest import RecursiveChildIteratorTest
from FilteredRecursiveChildIteratorTest import FilteredRecursiveChildIteratorTest
from ReferenceTest import ReferenceTest
from GraphComponentPathTest import GraphComponentPathTest
from ArrayPlugNode import ArrayPlugNode
from ArrayPlugTest import ArrayPlugTest
from SerialisationTest import SerialisationTest
from SwitchTest import SwitchTest
from MetadataTest import MetadataTest
from NodeAlgoTest import NodeAlgoTest
from DotTest import DotTest
from ApplicationTest import ApplicationTest
from LeafPathFilterTest import LeafPathFilterTest
from MatchPatternPathFilterTest import MatchPatternPathFilterTest
from LoopTest import LoopTest
from SubGraphTest import SubGraphTest
from FileSequencePathFilterTest import FileSequencePathFilterTest
from AnimationTest import AnimationTest
from StatsApplicationTest import StatsApplicationTest
from DownstreamIteratorTest import DownstreamIteratorTest
from PerformanceMonitorTest import PerformanceMonitorTest
from MetadataAlgoTest import MetadataAlgoTest
from ContextMonitorTest import ContextMonitorTest
from PlugAlgoTest import PlugAlgoTest
from BoxInTest import BoxInTest
from BoxOutTest import BoxOutTest
from DirtyPropagationScopeTest import DirtyPropagationScopeTest
from BoxIOTest import BoxIOTest
from ParallelAlgoTest import ParallelAlgoTest
from BackgroundTaskTest import BackgroundTaskTest
from ProcessMessageHandlerTest import ProcessMessageHandlerTest
from MonitorAlgoTest import MonitorAlgoTest
from NameValuePlugTest import NameValuePlugTest
from ExtensionAlgoTest import ExtensionAlgoTest
from ModuleTest import ModuleTest
from NumericBookmarkSetTest import NumericBookmarkSetTest
from NameSwitchTest import NameSwitchTest
from SpreadsheetTest import SpreadsheetTest

from IECorePreviewTest import *

if __name__ == "__main__":
	import unittest
	unittest.main()
