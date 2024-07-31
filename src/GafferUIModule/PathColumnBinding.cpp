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

#include "PathColumnBinding.h"

#include "GafferUI/PathColumn.h"

#include "GafferBindings/DataBinding.h"
#include "GafferBindings/SignalBinding.h"

#include "IECorePython/ExceptionAlgo.h"
#include "IECorePython/RefCountedBinding.h"
#include "IECorePython/ScopedGILLock.h"

#include "boost/mpl/vector.hpp"
#include "boost/python/suite/indexing/container_utils.hpp"

using namespace boost::python;
using namespace IECore;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferUI;

//////////////////////////////////////////////////////////////////////////
// PathListingWidgetAccessor class
//////////////////////////////////////////////////////////////////////////

namespace
{

// Provides a C++ interface to the functionality implemented in the Python
// PathListingWidget class.
class PathListingWidgetAccessor : public GafferUI::PathListingWidget
{

	public :

		PathListingWidgetAccessor( object widget )
			:	m_widget( widget )
		{
		}

		object widget()
		{
			return m_widget;
		}

		void setColumns( const Columns &columns ) override
		{
			IECorePython::ScopedGILLock gilLock;
			list pythonColumns;
			for( auto & c : columns )
			{
				pythonColumns.append( c );
			}
			m_widget.attr( "setColumns" )( pythonColumns );
		}

		Columns getColumns() const override
		{
			IECorePython::ScopedGILLock gilLock;
			object pythonColumns = m_widget.attr( "getColumns" )();
			Columns columns;
			boost::python::container_utils::extend_container( columns, pythonColumns );
			return columns;
		}

		void setSelection( const Selection &selection ) override
		{
			IECorePython::ScopedGILLock gilLock;

			object pythonSelection;
			if( std::holds_alternative<IECore::PathMatcher>( selection ) )
			{
				pythonSelection = object( std::get<IECore::PathMatcher>( selection ) );
			}
			else
			{
				list pythonList;
				for( const auto &c : std::get<std::vector<IECore::PathMatcher>>( selection ) )
				{
					pythonList.append( c );
				}
				pythonSelection = pythonList;
			}

			m_widget.attr( "setSelection" )( pythonSelection );
		}

		Selection getSelection() const override
		{
			IECorePython::ScopedGILLock gilLock;
			object pythonSelection = m_widget.attr( "getSelection" )();
			extract<IECore::PathMatcher> e( pythonSelection );
			if( e.check() )
			{
				return e();
			}
			else
			{
				std::vector<IECore::PathMatcher> selection;
				container_utils::extend_container( selection, pythonSelection );
				return selection;
			}
		}

	private :

		// The Python PathListingWidget object.
		object m_widget;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// MenuDefinitionAccessor class
//////////////////////////////////////////////////////////////////////////

namespace
{

struct GILReleaseMenuCommand
{

	GILReleaseMenuCommand( MenuDefinition::MenuItem::Command command )
		:	m_command( command )
	{
	}

	void operator()()
	{
		IECorePython::ScopedGILRelease gilRelease;
		m_command();
	}

	private :

		MenuDefinition::MenuItem::Command m_command;

};

// Provides a C++ interface to the functionality implemented in the Python
// MenuDefinition class.
class MenuDefinitionAccessor : public GafferUI::MenuDefinition
{

	public :

		MenuDefinitionAccessor( object menuDefinition )
			:	m_menuDefinition( menuDefinition )
		{
		}

		object menuDefinition()
		{
			return m_menuDefinition;
		}

		void append( const std::string &path, const MenuItem &item ) override
		{
			IECorePython::ScopedGILLock gilLock;

			dict pythonItem;

			if( item.command != nullptr )
			{
				pythonItem["command"] = make_function(
					GILReleaseMenuCommand( item.command ),
					boost::python::default_call_policies(),
					boost::mpl::vector<void>()
				);
			}

			pythonItem["description"] = item.description;
			pythonItem["icon"] = item.icon;
			pythonItem["shortCut"] = item.shortCut;
			pythonItem["divider"] = item.divider;
			pythonItem["active"] = item.active;

			m_menuDefinition.attr( "append" )( path, pythonItem );
		}

	private :

		// The Python MenuDefinition object.
		object m_menuDefinition;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Bindings
//////////////////////////////////////////////////////////////////////////

namespace
{

class PathColumnWrapper : public IECorePython::RefCountedWrapper<PathColumn>
{

	public :

		PathColumnWrapper( PyObject *self, PathColumn::SizeMode sizeMode )
			:	 IECorePython::RefCountedWrapper<PathColumn>( self, sizeMode )
		{
		}

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller = nullptr ) const override
		{
			if( isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					object f = this->methodOverride( "cellData" );
					if( f )
					{
						return extract<CellData>(
							// See note of caution about `ptr( canceller )` in PathWrapper.
							f( PathPtr( const_cast<Path *>( &path ) ), boost::python::ptr( canceller ) )
						);
					}
				}
				catch( const error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}

			throw IECore::Exception( "PathColumn::cellData() python method not defined" );
		}

		CellData headerData( const IECore::Canceller *canceller = nullptr ) const override
		{
			if( isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					object f = this->methodOverride( "headerData" );
					if( f )
					{
						return extract<CellData>(
							f( boost::python::ptr( canceller ) )
						);
					}
				}
				catch( const error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}

			throw IECore::Exception( "PathColumn::headerData() python method not defined" );
		}
};

object cellDataGetValue( PathColumn::CellData &cellData )
{
	return dataToPython( cellData.value.get(), /* copy = */ false );
}

void cellDataSetValue( PathColumn::CellData &cellData, const ConstDataPtr &data )
{
	cellData.value = data;
}

object cellDataGetIcon( PathColumn::CellData &cellData )
{
	return dataToPython( cellData.icon.get(), /* copy = */ false );
}

void cellDataSetIcon( PathColumn::CellData &cellData, const ConstDataPtr &data )
{
	cellData.icon = data;
}

object cellDataGetBackground( PathColumn::CellData &cellData )
{
	return dataToPython( cellData.background.get(), /* copy = */ false );
}

void cellDataSetBackground( PathColumn::CellData &cellData, const ConstDataPtr &data )
{
	cellData.background = data;
}

object cellDataGetToolTip( PathColumn::CellData &cellData )
{
	return dataToPython( cellData.toolTip.get(), /* copy = */ false );
}

void cellDataSetToolTip( PathColumn::CellData &cellData, const ConstDataPtr &data )
{
	cellData.toolTip = data;
}

object cellDataGetSortValue( PathColumn::CellData &cellData )
{
	return dataToPython( cellData.sortValue.get(), /* copy = */ false );
}

void cellDataSetSortValue( PathColumn::CellData &cellData, const ConstDataPtr &data )
{
	cellData.sortValue = data;
}

object cellDataGetForeground( PathColumn::CellData &cellData )
{
	return dataToPython( cellData.foreground.get(), /* copy = */ false );
}

void cellDataSetForeground( PathColumn::CellData &cellData, const ConstDataPtr &data )
{
	cellData.foreground = data;
}

PathColumn::CellData cellDataWrapper( PathColumn &pathColumn, const Path &path, const Canceller *canceller )
{
	IECorePython::ScopedGILRelease gilRelease;
	return pathColumn.cellData( path, canceller );
}

PathColumn::CellData headerDataWrapper( PathColumn &pathColumn, const Canceller *canceller )
{
	IECorePython::ScopedGILRelease gilRelease;
	return pathColumn.headerData( canceller );
}

struct ChangedSignalSlotCaller
{
	void operator()( boost::python::object slot, PathColumnPtr c )
	{
		try
		{
			slot( c );
		}
		catch( const error_already_set & )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}
};

struct ButtonSignalCaller
{
	static bool call( PathColumn::ButtonSignal &s, Gaffer::Path &path, object widget, const ButtonEvent &event )
	{
		// C++-based slots are passed a PathListingWidgetAccessor which gives them limited
		// access to the functionality of the Python PathListingWidget.
		PathListingWidgetAccessor accessor( widget );
		IECorePython::ScopedGILRelease gilRelease;
		return s( path, accessor, event );
	}
};

struct ButtonSignalSlotCaller
{
	bool operator()( boost::python::object slot, Path &path, PathListingWidget &widget, const ButtonEvent &event )
	{
		try
		{
			// Python-based slots are passed the original Python
			// PathListingWidget, so they have full access to everything.
			return slot( PathPtr( &path ), static_cast<PathListingWidgetAccessor&>( widget ).widget(), event );
		}
		catch( const error_already_set & )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}
};

struct ContextMenuSignalCaller
{
	static void call( PathColumn::ContextMenuSignal &s, PathColumn &column, object pathListingWidget, object menuDefinition )
	{
		PathListingWidgetAccessor pathListingWidgetAccessor( pathListingWidget );
		MenuDefinitionAccessor menuDefinitionAccessor( menuDefinition );
		IECorePython::ScopedGILRelease gilRelease;
		s( column, pathListingWidgetAccessor, menuDefinitionAccessor );
	}
};

struct ContextMenuSignalSlotCaller
{
	void operator()( boost::python::object slot, PathColumn &column, PathListingWidget &pathListingWidget, MenuDefinition &menuDefinition )
	{
		try
		{
			slot(
				PathColumnPtr( &column ),
				static_cast<PathListingWidgetAccessor &>( pathListingWidget ).widget(),
				static_cast<MenuDefinitionAccessor &>( menuDefinition ).menuDefinition()

			);
		}
		catch( const error_already_set & )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}
};

template<typename T>
const char *pathColumnProperty( const T &column )
{
	return column.property().c_str();
}

} // namespace

void GafferUIModule::bindPathColumn()
{
	IECorePython::RefCountedClass<PathColumn, IECore::RefCounted, PathColumnWrapper> pathColumnClass( "PathColumn" );
	{
		scope s = pathColumnClass;
		enum_<PathColumn::SizeMode>( "SizeMode" )
			.value( "Interactive", PathColumn::SizeMode::Interactive )
			.value( "Stretch", PathColumn::SizeMode::Stretch )
			.value( "Default", PathColumn::SizeMode::Default )
		;

		class_<PathColumn::CellData>( "CellData" )
			.def(
				init<const IECore::ConstDataPtr &, const IECore::ConstDataPtr &, const IECore::ConstDataPtr &, const IECore::ConstDataPtr &, const IECore::ConstDataPtr &, const IECore::ConstDataPtr &>(
					(
						arg( "value" ) = object(),
						arg( "icon" ) = object(),
						arg( "background" ) = object(),
						arg( "toolTip" ) = object(),
						arg( "sortValue" ) = object(),
						arg( "foreground" ) = object()
					)
				)
			)
			.add_property(
				"value", &cellDataGetValue, &cellDataSetValue
			)
			.add_property(
				"icon", &cellDataGetIcon, &cellDataSetIcon
			)
			.add_property(
				"background", &cellDataGetBackground, &cellDataSetBackground
			)
			.add_property(
				"toolTip", &cellDataGetToolTip, &cellDataSetToolTip
			)
			.add_property(
				"sortValue", &cellDataGetSortValue, &cellDataSetSortValue
			)
			.add_property(
				"foreground", &cellDataGetForeground, &cellDataSetForeground
			)
		;

		SignalClass<PathColumn::PathColumnSignal, DefaultSignalCaller<PathColumn::PathColumnSignal>, ChangedSignalSlotCaller>( "PathColumnSignal" );
		SignalClass<PathColumn::ButtonSignal, ButtonSignalCaller, ButtonSignalSlotCaller>( "ButtonSignal" );
		SignalClass<PathColumn::ContextMenuSignal, ContextMenuSignalCaller, ContextMenuSignalSlotCaller>( "ContextMenuSignal" );
	}

	pathColumnClass.def( init<PathColumn::SizeMode>( arg( "sizeMode" ) = PathColumn::SizeMode::Default ) )
		.def( "changedSignal", &PathColumn::changedSignal, return_internal_reference<1>() )
		.def( "cellData", &cellDataWrapper, ( arg( "path" ), arg( "canceller" ) = object() ) )
		.def( "headerData", &headerDataWrapper, ( arg( "canceller" ) = object() ) )
		.def( "buttonPressSignal", &PathColumn::buttonPressSignal, return_internal_reference<1>() )
		.def( "buttonReleaseSignal", &PathColumn::buttonReleaseSignal, return_internal_reference<1>() )
		.def( "buttonDoubleClickSignal", &PathColumn::buttonDoubleClickSignal, return_internal_reference<1>() )
		.def( "contextMenuSignal", &PathColumn::contextMenuSignal, return_internal_reference<1>() )
		.def( "instanceCreatedSignal", &PathColumn::instanceCreatedSignal, return_value_policy<reference_existing_object>() )
		.staticmethod( "instanceCreatedSignal" )
		.def( "getSizeMode", (PathColumn::SizeMode (PathColumn::*)() const )&PathColumn::getSizeMode )
		.def( "setSizeMode", &PathColumn::setSizeMode, ( arg( "sizeMode" ) ) )
	;

	IECorePython::RefCountedClass<StandardPathColumn, PathColumn>( "StandardPathColumn" )
		.def( init<const std::string &, IECore::InternedString, PathColumn::SizeMode>( arg( "sizeMode" ) = PathColumn::Default ) )
		.def( init<const PathColumn::CellData &, IECore::InternedString, PathColumn::SizeMode>( arg( "sizeMode" ) = PathColumn::Default ) )
		.def( "property", &pathColumnProperty<StandardPathColumn> )
	;

	IECorePython::RefCountedClass<IconPathColumn, PathColumn>( "IconPathColumn" )
		.def( init<const std::string &, const std::string &, IECore::InternedString, PathColumn::SizeMode>( arg( "sizeMode" ) = PathColumn::Default ) )
		.def( init<const PathColumn::CellData &, const std::string &, IECore::InternedString, PathColumn::SizeMode>( arg( "sizeMode" ) = PathColumn::Default ) )
		.def( "prefix", &IconPathColumn::prefix, return_value_policy<copy_const_reference>() )
		.def( "property", &pathColumnProperty<IconPathColumn> )
	;

	IECorePython::RefCountedClass<FileIconPathColumn, PathColumn>( "FileIconPathColumn" )
		.def( init<PathColumn::SizeMode>( arg( "sizeMode" ) = PathColumn::Default ) )
	;
}
