//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

#include "InspectorColumnBinding.h"

#include "GafferSceneUI/Private/Inspector.h"
#include "GafferSceneUI/Private/InspectorColumn.h"
#include "GafferSceneUI/Private/VisibilityColumn.h"

#include "GafferUI/PathColumn.h"

#include "IECorePython/RefCountedBinding.h"

using namespace boost::python;
using namespace IECorePython;
using namespace GafferUI;
using namespace GafferSceneUI::Private;

namespace
{

InspectorPtr inspectorColumnInspectorBinding( const InspectorColumn &column, const Gaffer::Path &path, const IECore::Canceller *canceller )
{
	IECorePython::ScopedGILRelease gilRelease;
	return boost::const_pointer_cast<Inspector>( column.inspector( path, canceller ) );
}

Inspector::ResultPtr inspectorColumnInspectBinding( const InspectorColumn &column, const Gaffer::Path &path, const IECore::Canceller *canceller )
{
	IECorePython::ScopedGILRelease gilRelease;
	return column.inspect( path, canceller );
}

Gaffer::PathPtr inspectorColumnHistoryPathBinding( const InspectorColumn &column, const Gaffer::Path &path, const IECore::Canceller *canceller )
{
	IECorePython::ScopedGILRelease gilRelease;
	return column.historyPath( path, canceller );
}

Gaffer::ContextPtr inspectorColumnInspectorContextBinding( const InspectorColumn &column, const Gaffer::Path &path, const IECore::Canceller *canceller )
{
	IECorePython::ScopedGILRelease gilRelease;
	return boost::const_pointer_cast<Gaffer::Context>( column.inspectorContext( path, canceller ) );
}

PathColumn::CellData inspectorColumnCellDataFromDataValue( const IECore::DataPtr &data )
{
	return InspectorColumn::cellDataFromValue( data.get() );
}

} // namespace

void GafferSceneUIModule::bindInspectorColumn()
{

	object privateModule( borrowed( PyImport_AddModule( "GafferSceneUI.Private" ) ) );
	scope().attr( "Private" ) = privateModule;
	scope privateScope( privateModule );

	RefCountedClass<GafferSceneUI::Private::InspectorColumn, GafferUI::PathColumn>( "InspectorColumn" )
		.def( init<GafferSceneUI::Private::InspectorPtr, const std::string &, const std::string &, PathColumn::SizeMode>(
			(
				arg_( "inspector" ),
				arg_( "label" ) = "",
				arg_( "toolTip" ) = "",
				arg( "sizeMode" ) = PathColumn::Default
			)
		) )
		.def( init<GafferSceneUI::Private::InspectorPtr, const PathColumn::CellData &, PathColumn::SizeMode>(
			(
				arg_( "inspector" ),
				arg_( "headerData" ),
				arg_( "sizeMode" ) = PathColumn::Default
			)
		) )
		.def( init<IECore::InternedString, const PathColumn::CellData &, IECore::InternedString, PathColumn::SizeMode>(
			(
				arg_( "inspectorProperty" ),
				arg_( "headerData" ),
				arg_( "contextProperty") = "inspector:context",
				arg_( "sizeMode" ) = PathColumn::Default
			)
		) )
		.def( "inspector", &inspectorColumnInspectorBinding, ( arg( "path" ), arg( "canceller" ) = object() ) )
		.def( "inspect", &inspectorColumnInspectBinding, ( arg( "path" ), arg( "canceller" ) = object() ) )
		.def( "historyPath", &inspectorColumnHistoryPathBinding, ( arg( "path" ), arg( "canceller" ) = object() ) )
		.def( "inspectorContext", &inspectorColumnInspectorContextBinding, ( arg( "path" ), arg( "canceller" ) = object() ) )
		.def( "cellDataFromValue", &InspectorColumn::cellDataFromValue )
		// Overload accepting DataPtr is needed to allow automatic type
		// conversion from simple types - string, int etc. Those exist for
		// DataPtr but not ObjectPtr.
		.def( "cellDataFromValue", &inspectorColumnCellDataFromDataValue )
		.staticmethod( "cellDataFromValue" )
	;

	RefCountedClass<GafferSceneUI::Private::VisibilityColumn, GafferSceneUI::Private::InspectorColumn>( "VisibilityColumn" )
		.def( init<const GafferScene::ScenePlugPtr &, const Gaffer::PlugPtr &>(
			(
				arg_( "scene" ),
				arg_( "editScope" )
			)
		) )
	;

}
