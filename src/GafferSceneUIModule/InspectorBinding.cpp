//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

#include "boost/python.hpp"

#include "InspectorBinding.h"

#include "GafferSceneUI/Private/Inspector.h"
#include "GafferSceneUI/Private/ParameterInspector.h"

#include "GafferBindings/SignalBinding.h"

#include "IECorePython/ExceptionAlgo.h"
#include "IECorePython/RefCountedBinding.h"

using namespace boost::python;
using namespace IECorePython;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferScene;
using namespace GafferSceneUI::Private;

namespace
{

GafferSceneUI::Private::Inspector::ResultPtr inspectWrapper( const GafferSceneUI::Private::Inspector &inspector )
{
	ScopedGILRelease gilRelease;
	return inspector.inspect();
}

IECore::ObjectPtr valueWrapper( const GafferSceneUI::Private::Inspector::Result &result )
{
	return result.value() ? result.value()->copy() : nullptr;
}

Gaffer::ValuePlugPtr acquireEditWrapper( GafferSceneUI::Private::Inspector::Result &result )
{
	ScopedGILRelease gilRelease;
	return result.acquireEdit();
}

struct DirtiedSlotCaller
{
	void operator()( boost::python::object slot, InspectorPtr inspector )
	{
		try
		{
			slot( inspector );
		}
		catch( const error_already_set &e )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}
};

} // namespace

void GafferSceneUIModule::bindInspector()
{

	object privateModule( borrowed( PyImport_AddModule( "GafferSceneUI.Private" ) ) );
	scope().attr( "Private" ) = privateModule;
	scope privateScope( privateModule );

	{
		scope inspectorScope = RefCountedClass<Inspector, IECore::RefCounted>( "Inspector" )
			.def( "name", &Inspector::name, return_value_policy<copy_const_reference>() )
			.def( "inspect", &inspectWrapper )
			.def( "dirtiedSignal", &Inspector::dirtiedSignal, return_internal_reference<1>() )
		;

		SignalClass<Inspector::InspectorSignal, DefaultSignalCaller<Inspector::InspectorSignal>, DirtiedSlotCaller>( "ChangedSignal" );

		scope resultScope = RefCountedClass<Inspector::Result, IECore::RefCounted>( "Result" )
			.def( "value", &valueWrapper )
			.def( "source", &Inspector::Result::source, return_value_policy<CastToIntrusivePtr>() )
			.def( "editScope", &Inspector::Result::editScope, return_value_policy<CastToIntrusivePtr>() )
			.def( "sourceType", &Inspector::Result::sourceType )
			.def( "editable", &Inspector::Result::editable )
			.def( "nonEditableReason", &Inspector::Result::nonEditableReason )
			.def( "acquireEdit", &acquireEditWrapper )
			.def( "editWarning", &Inspector::Result::editWarning )
		;

		enum_<Inspector::Result::SourceType>( "SourceType" )
			.value( "Upstream", Inspector::Result::SourceType::Upstream )
			.value( "EditScope", Inspector::Result::SourceType::EditScope )
			.value( "Downstream", Inspector::Result::SourceType::Downstream )
			.value( "Other", Inspector::Result::SourceType::Other )
		;
	}

	RefCountedClass<ParameterInspector, Inspector>( "ParameterInspector" )
		.def(
			init<const ScenePlugPtr &, const PlugPtr &, IECore::InternedString, const ShaderNetwork::Parameter &>(
				( arg( "scene" ), arg( "attribute" ), arg( "parameter" ) )
			)
		)
	;

}
