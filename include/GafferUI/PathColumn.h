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

#pragma once

#include "GafferUI/ButtonEvent.h"
#include "GafferUI/EventSignalCombiner.h"
#include "GafferUI/Export.h"

#include "Gaffer/Path.h"

#include "IECore/PathMatcher.h"
#include "IECore/SimpleTypedData.h"

#include <variant>

namespace GafferUI
{

class MenuDefinition;
class PathListingWidget;

/// Abstract class for extracting properties from a Path in a form
/// suitable for display in a table column. Primarily intended for
/// use in the PathListingWidget.
class GAFFERUI_API PathColumn : public IECore::RefCounted, public Gaffer::Signals::Trackable
{

	public :

		IE_CORE_DECLAREMEMBERPTR( PathColumn )

		/// Defines the UI size behaviour of the column.
		enum SizeMode
		{
			/// The column is user resizable.
			Interactive = 0,
			/// The column will automatically resize to fill available space.
			Stretch = 1,

			Default = Interactive,
		};

		explicit PathColumn( SizeMode sizeMode = Default );

		/// Returns the current column size mode.
		SizeMode getSizeMode() const;
		/// Sets the column size mode.
		void setSizeMode( SizeMode sizeMode );

		/// Display data
		/// ============

		struct CellData
		{
			CellData(
				const IECore::ConstDataPtr &value = nullptr,
				const IECore::ConstDataPtr &icon = nullptr,
				const IECore::ConstDataPtr &background = nullptr,
				const IECore::ConstDataPtr &toolTip = nullptr,
				const IECore::ConstDataPtr &sortValue = nullptr,
				const IECore::ConstDataPtr &foreground = nullptr
			)	:	value( value ), icon( icon ), background( background ), toolTip( toolTip ),
					sortValue( sortValue ), foreground( foreground ) {}

			CellData( const CellData &other ) = default;

			/// The primary value to be displayed in a cell or header.
			/// Supported types :
			///
			/// - StringData
			/// - IntData, UIntData, UInt64Data
			/// - FloatData, DoubleData
			/// - DateTimeData
			/// - V2fData, V3fData, Color3fData, Color4fData
			IECore::ConstDataPtr value;
			/// An additional icon to be displayed next to the primary
			/// value. Supported types :
			///
			/// - StringData (providing icon name)
			/// - Color3fData (drawn as swatch)
			/// - CompoundData (containing `state:normal` and/or `state:highlighted`
			//    keys mapping to StringData providing an icon name for each state)
			IECore::ConstDataPtr icon;
			/// The background colour for the cell. Supported types :
			///
			/// - Color3fData
			/// - Color4fData
			IECore::ConstDataPtr background;
			/// Tip to be displayed on hover. Supported types :
			///
			/// - StringData
			IECore::ConstDataPtr toolTip;
			/// Used to determine sort order. If not specified, `value` is
			/// used for sorting instead.
			IECore::ConstDataPtr sortValue;
			/// The foreground colour for the cell value. Supported types :
			///
			/// - Color3fData
			/// - Color4fData
			IECore::ConstDataPtr foreground;

			private :

				IECore::ConstDataPtr m_reserved1;
				IECore::ConstDataPtr m_reserved2;

		};

		/// Returns the data needed to draw a column cell.
		virtual CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller = nullptr ) const = 0;
		/// Returns the data needed to draw a column header.
		virtual CellData headerData( const IECore::Canceller *canceller = nullptr ) const = 0;

		using PathColumnSignal = Gaffer::Signals::Signal<void ( PathColumn * ), Gaffer::Signals::CatchingCombiner<void>>;
		/// Subclasses should emit this signal when something changes
		/// in a way that would affect the results of `cellValue()`
		/// or `headerValue()`.
		PathColumnSignal &changedSignal();

		/// Event handling
		/// ==============
		///
		/// These signals are emitted when the user interacts with the
		/// column. Subclasses may connect to them to implement custom
		/// behaviours.

		using ButtonSignal = Gaffer::Signals::Signal<bool ( Gaffer::Path &path, PathListingWidget &widget, const ButtonEvent &event ), EventSignalCombiner<bool>>;
		ButtonSignal &buttonPressSignal();
		ButtonSignal &buttonReleaseSignal();
		ButtonSignal &buttonDoubleClickSignal();

		using ContextMenuSignal = Gaffer::Signals::Signal<void ( PathColumn &column, PathListingWidget &widget, MenuDefinition &menuDefinition ), Gaffer::Signals::CatchingCombiner<void>>;
		ContextMenuSignal &contextMenuSignal();

		/// Creation
		/// ========

		/// Signal emitted whenever a new PathColumn is created. This provides
		/// an opportunity for the customisation of columns anywhere, no matter how
		/// they are created or where they are hosted.
		static PathColumnSignal &instanceCreatedSignal();

	private :

		PathColumnSignal m_changedSignal;

		ButtonSignal m_buttonPressSignal;
		ButtonSignal m_buttonReleaseSignal;
		ButtonSignal m_buttonDoubleClickSignal;
		ContextMenuSignal m_contextMenuSignal;

		SizeMode m_sizeMode;

};

IE_CORE_DECLAREPTR( PathColumn )

/// Standard column type which simply displays a property of the path.
class GAFFERUI_API StandardPathColumn : public PathColumn
{

	public :

		IE_CORE_DECLAREMEMBERPTR( StandardPathColumn )

		StandardPathColumn( const std::string &label, IECore::InternedString property, PathColumn::SizeMode sizeMode = Default );
		StandardPathColumn( const CellData &headerData, IECore::InternedString property, PathColumn::SizeMode sizeMode = Default );

		IECore::InternedString property() const;

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const override;
		CellData headerData( const IECore::Canceller *canceller ) const override;

	private :

		const CellData m_headerData;
		IECore::InternedString m_property;

};

IE_CORE_DECLAREPTR( StandardPathColumn )

/// Column which uses a property of the path to specify an icon.
class GAFFERUI_API IconPathColumn : public PathColumn
{

	public :

		IE_CORE_DECLAREMEMBERPTR( IconPathColumn )

		/// The name for the icon is `<prefix><property>`, with `property` being queried
		/// by `Path::property()`. Supported property types :
		///
		/// - StringData
		/// - IntData, UInt44Data
		/// - BoolData
		IconPathColumn( const std::string &label, const std::string &prefix, IECore::InternedString property, PathColumn::SizeMode sizeMode = Default );
		IconPathColumn( const CellData &headerData, const std::string &prefix, IECore::InternedString property, PathColumn::SizeMode sizeMode = Default );

		const std::string &prefix() const;
		IECore::InternedString property() const;

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const override;
		CellData headerData( const IECore::Canceller *canceller ) const override;

	private :

		const CellData m_headerData;
		std::string m_prefix;
		IECore::InternedString m_property;

};

IE_CORE_DECLAREPTR( IconPathColumn )

/// Column type suitable for displaying an icon for
/// FileSystemPaths.
class GAFFERUI_API FileIconPathColumn : public PathColumn
{

	public :

		IE_CORE_DECLAREMEMBERPTR( FileIconPathColumn )

		FileIconPathColumn( PathColumn::SizeMode sizeMode = Default );

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const override;
		CellData headerData( const IECore::Canceller *canceller ) const override;

	private :

		const IECore::StringDataPtr m_label;

};

IE_CORE_DECLAREPTR( FileIconPathColumn )

/// C++ interface for the `GafferUI.PathListingWidget` Python class. Provided for
/// use in PathColumn event signals, so that event handling may be implemented
/// from C++ if desired.
class PathListingWidget
{

	public :

		using Columns = std::vector<PathColumnPtr>;
		virtual void setColumns( const Columns &columns ) = 0;
		virtual Columns getColumns() const = 0;

		using Selection = std::variant<IECore::PathMatcher, std::vector<IECore::PathMatcher>>;
		virtual void setSelection( const Selection &selection ) = 0;
		virtual Selection getSelection() const = 0;

};

/// C++ interface for the `IECore.MenuDefinition` Python class. Provided for use
/// in `PathColumn::contextMenuSignal()`, so that event handling may be
/// implemented from C++ if desired.
class MenuDefinition
{

	public :

		struct MenuItem
		{
			using Command = std::function<void ()>;
			Command command;
			std::string description;
			std::string icon;
			std::string shortCut;
			bool divider = false;
			bool active = true;
		};

		virtual void append( const std::string &path, const MenuItem &item ) = 0;

};

/// Overload for the standard `intrusive_ptr_add_ref` defined in RefCounted.h.
/// This allows us to emit `instanceCreatedSignal()` once the object is fully
/// constructed and it is safe for slots (especially Python slots) to add
/// additional references.
///
/// > Caution : This won't be called if you assign a new PathColumn to
/// > RefCountedPtr rather than PathColumnPtr. Don't do that!
inline void intrusive_ptr_add_ref( PathColumn *column )
{
	bool firstRef = column->refCount() == 0;
	column->addRef();
	if( firstRef )
	{
		PathColumn::instanceCreatedSignal()( column );
	}
}

} // namespace GafferUI
