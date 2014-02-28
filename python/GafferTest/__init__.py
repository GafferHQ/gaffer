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

from _GafferTest import *

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

from TestCase import TestCase
from AddNode import AddNode
from SphereNode import SphereNode
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
from SpeedTest import SpeedTest
from KeywordPlugNode import KeywordPlugNode
from CompoundNumericPlugTest import CompoundNumericPlugTest
from CompoundNumericNode import CompoundNumericNode
from CompoundPlugTest import CompoundPlugTest
from CompoundPlugNode import CompoundPlugNode
from TypedObjectPlugTest import TypedObjectPlugTest
from SplinePlugTest import SplinePlugTest
from AboutTest import AboutTest
from ParameterisedHolderTest import ParameterisedHolderTest
from ParameterHandlerTest import ParameterHandlerTest
from ChildSetTest import ChildSetTest
from PythonApplicationTest import PythonApplicationTest
from ObjectReaderTest import ObjectReaderTest
from OpHolderTest import OpHolderTest
from ProceduralHolderTest import ProceduralHolderTest
from ApplicationRootTest import ApplicationRootTest
from ObjectWriterTest import ObjectWriterTest
from ExecuteApplicationTest import ExecuteApplicationTest
from ContextTest import ContextTest
from CompoundPathFilterTest import CompoundPathFilterTest
from BadNode import BadNode
from CapturingSlot import CapturingSlot
from LazyModuleTest import LazyModuleTest
from NodeBindingTest import NodeBindingTest
from DictPathTest import DictPathTest
from IndexedIOPathTest import IndexedIOPathTest
from ClassLoaderPathTest import ClassLoaderPathTest
from ExpressionTest import ExpressionTest
from BlockedConnectionTest import BlockedConnectionTest
from TimeWarpComputeNodeTest import TimeWarpComputeNodeTest
from TransformPlugTest import TransformPlugTest
from Transform2DPlugTest import Transform2DPlugTest
from SequencePathTest import SequencePathTest
from OpMatcherTest import OpMatcherTest
from WeakMethodTest import WeakMethodTest
from StringInOutNode import StringInOutNode
from StringPlugTest import StringPlugTest
from ContextVariablesTest import ContextVariablesTest
from ValuePlugTest import ValuePlugTest
from RandomTest import RandomTest
from ParameterPathTest import ParameterPathTest
from CompoundDataPlugTest import CompoundDataPlugTest
from DependencyNodeTest import DependencyNodeTest
from ComputeNodeTest import ComputeNodeTest
from BoxPlugTest import BoxPlugTest
from BoxTest import BoxTest
from OutputRedirectionTest import OutputRedirectionTest
from ExecutableNodeTest import ExecutableNodeTest
from ExecutableOpHolderTest import ExecutableOpHolderTest
from DespatcherTest import DespatcherTest
from RecursiveChildIteratorTest import RecursiveChildIteratorTest
from FilteredRecursiveChildIteratorTest import FilteredRecursiveChildIteratorTest
from ReferenceTest import ReferenceTest
from OrphanRemoverTest import OrphanRemoverTest
from GraphComponentPathTest import GraphComponentPathTest
from InputGeneratorNode import InputGeneratorNode
from InputGeneratorTest import InputGeneratorTest
from ArrayPlugNode import ArrayPlugNode
from ArrayPlugTest import ArrayPlugTest
from SerialisationTest import SerialisationTest
from SwitchTest import SwitchTest
from MetadataTest import MetadataTest
from StringAlgoTest import StringAlgoTest

if __name__ == "__main__":
	import unittest
	unittest.main()
