//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_SPREADSHEET_H
#define GAFFER_SPREADSHEET_H

#include "Gaffer/ComputeNode.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/TypedObjectPlug.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

class GAFFER_API Spreadsheet : public ComputeNode
{

	public :

		Spreadsheet( const std::string &name=defaultName<Spreadsheet>() );
		~Spreadsheet() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( Gaffer::Spreadsheet, SpreadsheetTypeId, ComputeNode );

		/// Plug types
		/// ==========
		///
		/// The spreadsheet is defined using a hierarchy of specialised plug
		/// types, organised first by row and then by column.

		class RowPlug;

		/// Top level plug that has a child for each row in the spreadsheet.
		/// This also provides methods for adding and removing rows and columns.
		/// Accessed via `Spreadsheet::rowsPlug()`.
		class RowsPlug : public ValuePlug
		{

			public :

				RowsPlug( const std::string &name = defaultName<RowsPlug>(), Direction direction = In, unsigned flags = Default );

				GAFFER_PLUG_DECLARE_TYPE( Gaffer::Spreadsheet::RowsPlug, Gaffer::SpreadsheetRowsPlugTypeId, Gaffer::ValuePlug );

				/// Methods for adjusting spreadsheet size
				/// ======================================
				///
				/// Several constraints must be maintained when adjusting the
				/// size of the spreadsheet, so these dedicated methods should
				/// be used instead of manual addition of children.
				///
				/// These methods are defined on the RowPlug rather than on the
				/// Spreadsheet so that they can be used for the editing and
				/// serialisation of promoted plugs.

				size_t addColumn( const ValuePlug *value, IECore::InternedString name = IECore::InternedString() );
				void removeColumn( size_t columnIndex );

				RowPlug *addRow();
				/// \todo Return `RowPlug::Range`, which we can't do right
				/// now because it doesn't have constructors which specify
				/// the begin/end iterators.
				void addRows( size_t numRows );

				Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

			private :

				ValuePlug *outPlug();

		};

		IE_CORE_DECLAREPTR( RowsPlug );

		/// Defines a single row of the spreadsheet. Access using
		/// `RowPlug::Range( *rowsPlug() )` or via `rowsPlug()->getChild<RowPlug>()`.
		class RowPlug : public ValuePlug
		{

			public :

				GAFFER_PLUG_DECLARE_TYPE( Gaffer::Spreadsheet::RowPlug, Gaffer::SpreadsheetRowPlugTypeId, Gaffer::ValuePlug );

				StringPlug *namePlug();
				const StringPlug *namePlug() const;

				BoolPlug *enabledPlug();
				const BoolPlug *enabledPlug() const;

				ValuePlug *cellsPlug();
				const ValuePlug *cellsPlug() const;

				Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

			private :

				RowPlug( const std::string &name, Plug::Direction direction = Plug::In );
				friend class Spreadsheet;

		};

		IE_CORE_DECLAREPTR( RowPlug );

		/// Defines a single cell in the spreadsheet. Access using
		/// `CellPlug::Range( *rowPlug->cellsPlug() )` or via
		/// `rowPlug->cellsPlug()->getChild<CellPlug>()`.
		class CellPlug : public ValuePlug
		{

			public :

				GAFFER_PLUG_DECLARE_TYPE( Gaffer::Spreadsheet::CellPlug, Gaffer::SpreadsheetCellPlugTypeId, Gaffer::ValuePlug );

				BoolPlug *enabledPlug();
				const BoolPlug *enabledPlug() const;

				template<typename T = Gaffer::ValuePlug>
				T *valuePlug();

				template<typename T = Gaffer::ValuePlug>
				const T *valuePlug() const;

				Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

			private :

				CellPlug( const std::string &name, const Gaffer::Plug *value, Plug::Direction direction = Plug::In );
				friend class Spreadsheet;

		};

		IE_CORE_DECLAREPTR( CellPlug );

		/// Plug accessors
		/// ==============

		StringPlug *selectorPlug();
		const StringPlug *selectorPlug() const;

		ValuePlug *rowsPlug();
		const ValuePlug *rowsPlug() const;

		ValuePlug *outPlug();
		const ValuePlug *outPlug() const;

		StringVectorDataPlug *activeRowNamesPlug();
		const StringVectorDataPlug *activeRowNamesPlug() const;

		/// Returns the input plug which provides the value
		/// for `output` in the current context.
		ValuePlug *activeInPlug( const ValuePlug *output );
		const ValuePlug *activeInPlug( const ValuePlug *output ) const;

		/// DependencyNode methods
		/// ======================

		void affects( const Plug *input, AffectedPlugsContainer &outputs ) const override;
		BoolPlug *enabledPlug() override;
		const BoolPlug *enabledPlug() const override;
		Plug *correspondingInput( const Plug *output ) override;
		const Plug *correspondingInput( const Plug *output ) const override;

	protected :

		void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const override;
		void compute( ValuePlug *output, const Context *context ) const override;

	private :

		IntPlug *rowIndexPlug();
		const IntPlug *rowIndexPlug() const;

		const ValuePlug *correspondingInput( const Plug *output, size_t rowIndex ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Spreadsheet )

} // namespace Gaffer

#include "Gaffer/Spreadsheet.inl"

#endif // GAFFER_SPREADSHEET_H
