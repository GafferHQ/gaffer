//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/TimeWarp.h"
#include "Gaffer/ContextVariables.h"
#include "Gaffer/Backdrop.h"
#include "Gaffer/Switch.h"

#include "GafferBindings/ConnectionBinding.h"
#include "GafferBindings/SignalBinding.h"
#include "GafferBindings/GraphComponentBinding.h"
#include "GafferBindings/NodeBinding.h"
#include "GafferBindings/PlugBinding.h"
#include "GafferBindings/ValuePlugBinding.h"
#include "GafferBindings/NumericPlugBinding.h"
#include "GafferBindings/TypedPlugBinding.h"
#include "GafferBindings/TypedObjectPlugBinding.h"
#include "GafferBindings/ScriptNodeBinding.h"
#include "GafferBindings/ApplicationRootBinding.h"
#include "GafferBindings/SetBinding.h"
#include "GafferBindings/UndoContextBinding.h"
#include "GafferBindings/CompoundPlugBinding.h"
#include "GafferBindings/CompoundNumericPlugBinding.h"
#include "GafferBindings/SplinePlugBinding.h"
#include "GafferBindings/ParameterisedHolderBinding.h"
#include "GafferBindings/ParameterHandlerBinding.h"
#include "GafferBindings/CompoundParameterHandlerBinding.h"
#include "GafferBindings/StandardSetBinding.h"
#include "GafferBindings/ChildSetBinding.h"
#include "GafferBindings/OpHolderBinding.h"
#include "GafferBindings/ProceduralHolderBinding.h"
#include "GafferBindings/PreferencesBinding.h"
#include "GafferBindings/ContextBinding.h"
#include "GafferBindings/BoxPlugBinding.h"
#include "GafferBindings/ExpressionBinding.h"
#include "GafferBindings/TransformPlugBinding.h"
#include "GafferBindings/Transform2DPlugBinding.h"
#include "GafferBindings/CompoundDataPlugBinding.h"
#include "GafferBindings/RandomBinding.h"
#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/ComputeNodeBinding.h"
#include "GafferBindings/BoxBinding.h"
#include "GafferBindings/ActionBinding.h"
#include "GafferBindings/ExecutableOpHolderBinding.h"
#include "GafferBindings/ExecutableNodeBinding.h"
#include "GafferBindings/DespatcherBinding.h"
#include "GafferBindings/ReferenceBinding.h"
#include "GafferBindings/BehaviourBinding.h"
#include "GafferBindings/ArrayPlugBinding.h"
#include "GafferBindings/Serialisation.h"
#include "GafferBindings/MetadataBinding.h"

using namespace boost::python;
using namespace Gaffer;
using namespace GafferBindings;

BOOST_PYTHON_MODULE( _Gaffer )
{

	bindConnection();
	bindSignal();
	bindGraphComponent();
	bindNode();
	bindDependencyNode();
	bindComputeNode();
	bindPlug();
	bindValuePlug();
	bindNumericPlug();
	bindTypedPlug();
	bindTypedObjectPlug();
	bindScriptNode();
	bindApplicationRoot();
	bindSet();
	bindUndoContext();
	bindCompoundPlug();
	bindCompoundNumericPlug();
	bindSplinePlug();
	bindParameterisedHolder();
	bindParameterHandler();
	bindCompoundParameterHandler();
	bindStandardSet();
	bindChildSet();
	bindOpHolder();
	bindProceduralHolder();
	bindPreferences();
	bindContext();
	bindBoxPlug();
	bindExpression();
	bindTransformPlug();
	bindTransform2DPlug();
	bindCompoundDataPlug();
	bindRandom();
	bindBox();
	bindAction();
	bindExecutableNode();
	bindDespatcher();
	bindExecutableOpHolder();
	bindReference();
	bindArrayPlug();
	bindSerialisation();
	bindMetadata();
			
	NodeClass<Backdrop>();

	DependencyNodeClass<ContextProcessorComputeNode>();
	DependencyNodeClass<TimeWarpComputeNode>();
	DependencyNodeClass<ContextVariablesComputeNode>();
	DependencyNodeClass<SwitchDependencyNode>();
	DependencyNodeClass<SwitchComputeNode>();

	object behavioursModule( borrowed( PyImport_AddModule( "Gaffer.Behaviours" ) ) );
	scope().attr( "Behaviours" ) = behavioursModule;	

	scope behavioursScope( behavioursModule );
	
	bindBehaviours();

	// Various parts of gaffer create new threads from C++, and those
	// threads may call back into Python via wrapped classes at any time.
	// We must prepare Python for this by calling PyEval_InitThreads().

	PyEval_InitThreads();
	
}
