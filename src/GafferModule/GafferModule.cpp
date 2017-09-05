//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2015, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

#include "tbb/tbb.h"

#include "Gaffer/TimeWarp.h"
#include "Gaffer/ContextVariables.h"
#include "Gaffer/DeleteContextVariables.h"
#include "Gaffer/Backdrop.h"
#include "Gaffer/Loop.h"

#include "GafferBindings/DependencyNodeBinding.h"

#include "ActionBinding.h"
#include "AnimationBinding.h"
#include "ApplicationRootBinding.h"
#include "ArrayPlugBinding.h"
#include "BoxPlugBinding.h"
#include "CompoundDataPlugBinding.h"
#include "CompoundNumericPlugBinding.h"
#include "CompoundPlugBinding.h"
#include "ConnectionBinding.h"
#include "ContextBinding.h"
#include "DirtyPropagationScopeBinding.h"
#include "DotBinding.h"
#include "ExpressionBinding.h"
#include "GraphComponentBinding.h"
#include "MetadataAlgoBinding.h"
#include "MetadataBinding.h"
#include "MonitorBinding.h"
#include "NodeBinding.h"
#include "NumericPlugBinding.h"
#include "PathBinding.h"
#include "PathFilterBinding.h"
#include "PlugAlgoBinding.h"
#include "PlugBinding.h"
#include "RandomBinding.h"
#include "ScriptNodeBinding.h"
#include "SerialisationBinding.h"
#include "SetBinding.h"
#include "SignalBinding.h"
#include "SplinePlugBinding.h"
#include "StringAlgoBinding.h"
#include "StringPlugBinding.h"
#include "SubGraphBinding.h"
#include "SwitchBinding.h"
#include "Transform2DPlugBinding.h"
#include "TransformPlugBinding.h"
#include "TypedObjectPlugBinding.h"
#include "TypedPlugBinding.h"
#include "UndoScopeBinding.h"
#include "ValuePlugBinding.h"

using namespace boost::python;
using namespace Gaffer;
using namespace GafferModule;
using namespace GafferBindings;

namespace
{

// Wraps task_scheduler_init so it can be used as a python
// context manager.
class TaskSchedulerInitWrapper : public tbb::task_scheduler_init
{

	public :

		TaskSchedulerInitWrapper( int max_threads )
			:	tbb::task_scheduler_init( deferred ), m_maxThreads( max_threads )
		{
			if( max_threads != automatic && max_threads <= 0 )
			{
				PyErr_SetString( PyExc_ValueError, "max_threads must be either automatic or a positive integer" );
				throw_error_already_set();
			}
		}

		void enter()
		{
			initialize( m_maxThreads );
		}

		bool exit( boost::python::object excType, boost::python::object excValue, boost::python::object excTraceBack )
		{
			terminate();
			return false; // don't suppress exceptions
		}

	private :

		int m_maxThreads;

};


bool isDebug()
{
#ifdef NDEBUG
	return false;
#else
	return true;
#endif
}

} // namespace

BOOST_PYTHON_MODULE( _Gaffer )
{

	bindConnection();
	bindSignal();
	bindGraphComponent();
	bindContext();
	bindNode();
	bindPlug();
	bindValuePlug();
	bindNumericPlug();
	bindTypedPlug();
	bindStringPlug();
	bindTypedObjectPlug();
	bindScriptNode();
	bindApplicationRoot();
	bindSet();
	bindDirtyPropagationScope();
	bindUndoScope();
	bindCompoundPlug();
	bindCompoundNumericPlug();
	bindSplinePlug();
	bindBoxPlug();
	bindExpression();
	bindTransformPlug();
	bindTransform2DPlug();
	bindCompoundDataPlug();
	bindRandom();
	bindSubGraph();
	bindAction();
	bindArrayPlug();
	bindSerialisation();
	bindMetadata();
	bindStringAlgo();
	bindDot();
	bindPath();
	bindPathFilter();
	bindAnimation();
	bindMonitor();
	bindMetadataAlgo();
	bindSwitch();
	bindPlugAlgo();

	NodeClass<Backdrop>();

	DependencyNodeClass<ContextProcessorComputeNode>();
	DependencyNodeClass<TimeWarpComputeNode>();
	DependencyNodeClass<ContextVariablesComputeNode>();
	DependencyNodeClass<DeleteContextVariablesComputeNode>();
	DependencyNodeClass<LoopComputeNode>();

	def( "isDebug", &isDebug );

	object tsi = class_<TaskSchedulerInitWrapper, boost::noncopyable>( "_tbb_task_scheduler_init", no_init )
		.def( init<int>( arg( "max_threads" ) = int( tbb::task_scheduler_init::automatic ) ) )
		.def( "__enter__", &TaskSchedulerInitWrapper::enter, return_self<>() )
		.def( "__exit__", &TaskSchedulerInitWrapper::exit )
	;
	tsi.attr( "automatic" ) = int( tbb::task_scheduler_init::automatic );

	// Various parts of gaffer create new threads from C++, and those
	// threads may call back into Python via wrapped classes at any time.
	// We must prepare Python for this by calling PyEval_InitThreads().

	PyEval_InitThreads();

}
