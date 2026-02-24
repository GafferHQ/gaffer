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

#include "ActionBinding.h"
#include "AnimationBinding.h"
#include "ApplicationRootBinding.h"
#include "ArrayPlugBinding.h"
#include "BoxPlugBinding.h"
#include "CollectBinding.h"
#include "CompoundDataPlugBinding.h"
#include "CompoundNumericPlugBinding.h"
#include "ContextBinding.h"
#include "ContextProcessorBinding.h"
#include "DirtyPropagationScopeBinding.h"
#include "DotBinding.h"
#include "ExpressionBinding.h"
#include "GraphComponentBinding.h"
#include "ProcessMessageHandlerBinding.h"
#include "MetadataAlgoBinding.h"
#include "MetadataBinding.h"
#include "MonitorBinding.h"
#include "NodeAlgoBinding.h"
#include "NodeBinding.h"
#include "NumericPlugBinding.h"
#include "OptionalValuePlugBinding.h"
#include "ParallelAlgoBinding.h"
#include "PathBinding.h"
#include "PathFilterBinding.h"
#include "PlugAlgoBinding.h"
#include "PlugBinding.h"
#include "ProcessBinding.h"
#include "RandomBinding.h"
#include "ScriptNodeBinding.h"
#include "SerialisationBinding.h"
#include "SetBinding.h"
#include "SignalsBinding.h"
#include "RampPlugBinding.h"
#include "SpreadsheetBinding.h"
#include "StringPlugBinding.h"
#include "SubGraphBinding.h"
#include "SwitchBinding.h"
#include "Transform2DPlugBinding.h"
#include "TransformPlugBinding.h"
#include "TypedObjectPlugBinding.h"
#include "TypedPlugBinding.h"
#include "UndoScopeBinding.h"
#include "ValuePlugBinding.h"
#include "NameValuePlugBinding.h"
#include "ShufflesBinding.h"
#include "MessagesBinding.h"
#include "TweakPlugBinding.h"

#include "GafferBindings/DependencyNodeBinding.h"

#include "Gaffer/Backdrop.h"
#include "Gaffer/PatternMatch.h"

#ifdef __APPLE__
#include <crt_externs.h>
static char **environ = *_NSGetEnviron();
#endif

using namespace boost::python;
using namespace Gaffer;
using namespace GafferModule;
using namespace GafferBindings;

namespace
{

bool isDebug()
{
#ifdef NDEBUG
	return false;
#else
	return true;
#endif
}

// Used as a replacement for `os.environ.copy()`, because
// `os.environ` doesn't preserve case on Windows.
boost::python::dict environment()
{
	boost::python::dict result;
	for( char **e = environ; *e; e++ )
	{
		const char *separator = strchr( *e, '=' );
		if( !separator )
		{
			continue;
		}
		const std::string name( *e, separator - *e );
		const std::string value( separator + 1 );
		result[name] = value;
	}

	return result;
}

} // namespace

BOOST_PYTHON_MODULE( _Gaffer )
{

	bindSignals();
	bindGraphComponent();
	bindContext();
	bindSerialisation();
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
	bindCompoundNumericPlug();
	bindRampPlug();
	bindBoxPlug();
	bindExpression();
	bindTransformPlug();
	bindTransform2DPlug();
	bindCompoundDataPlug();
	bindRandom();
	bindSubGraph();
	bindAction();
	bindArrayPlug();
	bindMetadata();
	bindDot();
	bindPath();
	bindPathFilter();
	bindAnimation();
	bindMonitor();
	bindMetadataAlgo();
	bindSwitch();
	bindPlugAlgo();
	bindParallelAlgo();
	bindContextProcessor();
	bindProcessMessageHandler();
	bindNameValuePlug();
	bindProcess();
	bindSpreadsheet();
	bindNodeAlgo();
	bindShuffles();
	bindMessages();
	bindTweakPlugs();
	bindOptionalValuePlug();
	bindCollect();

	NodeClass<Backdrop>();
	DependencyNodeClass<PatternMatch>();

	def( "isDebug", &isDebug );
	def( "environment", &environment );

}
