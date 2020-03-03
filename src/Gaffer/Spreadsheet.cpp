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

#include "Gaffer/Spreadsheet.h"

#include "Gaffer/StringPlug.h"

#include "IECore/NullObject.h"

#include "boost/bind.hpp"
#include "boost/container/small_vector.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/multi_index/member.hpp"
#include "boost/multi_index/hashed_index.hpp"
#include "boost/multi_index_container.hpp"

#include <unordered_map>

using namespace std;
using namespace boost;
using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

void appendLeafPlugs( const Gaffer::Plug *p, DependencyNode::AffectedPlugsContainer &container )
{
	if( !p->children().size() )
	{
		container.push_back( p );
	}
	else
	{
		for( const auto &c : Plug::Range( *p ) )
		{
			appendLeafPlugs( c.get(), container );
		}
	}
}

// Data type stored on `rowsMapPlug()` and used for quickly
// finding the right row for a selector.
class RowsMap : public IECore::Data
{

	public :

		// Rows without wildcards. We can look these up
		// directly.
		using Map = std::unordered_map<std::string, size_t>;
		Map plainRows;

		// Rows with wildcards. These require a linear search.
		struct Row
		{
			std::string name;
			size_t index;
		};
		using Vector = std::vector<Row>;
		Vector wildcardRows;

		// List of active row names for `activeRowNamesPlug()`.
		ConstStringVectorDataPtr activeRowNames;

};

IE_CORE_DECLAREPTR( RowsMap )

// Context scope used for accessing `rowsMapPlug()`. This
// removes all context variables referred to by `selectorPlug()`,
// for two reasons :
//
// 1. Performance. A common use case is to use `${someVariable}`
//    as the selector, and then to have N rows, one for each
//    value that `${someVariable}` will take. This would lead to
//    N calls to `Spreadsheet::hash( rowsMapPlug() )` (one per
//    unique context), each of which would need to visit all N
//    rows. For some uses of the Spreadsheet, N can be large enough
//    that the resultant quadratic scaling is unacceptable. We can
//    avoid this by making a clean context omitting `${someVariable}`,
//    meaning that `rowsMapPlug()` will be hashed only once.
// 2. Sanity. We can't think of any good reason to have row names
//    that include the same context variable as the selector.
//    Trying to reason about them would be mindbending.
class RowsMapScope : boost::noncopyable, public Context::SubstitutionProvider
{

	public :

		RowsMapScope( const Context *context, const std::string &selector )
			:	SubstitutionProvider( context ), m_context( context )
		{
			// (Ab)use `StringAlgo::substitute()` as a parser for
			// variable references in the `selector`. We pass
			// ourselves as the VariableProvider so that
			// our `variable()` method is called once for each
			// variable. We could instead implement our
			// own parsing, but that would be non-trivial, particularly
			// because `substitute()` allows recursive substitutions.
			m_selector = IECore::StringAlgo::substitute( selector, *this );
		}

		// Returns the selector with Context substitutions applied.
		const std::string &selector() const
		{
			return m_selector;
		}

		// Methods used by `StringAlgo::substitute()`. We use
		// these to parse variable references in `selector`.

		int frame() const override
		{
			return SubstitutionProvider::frame();
		}

		const std::string &variable( const boost::string_view &name, bool &recurse ) const override
		{
			if( !m_scope )
			{
				m_scope.emplace( m_context );
			}
			m_scope->remove( name );
			return SubstitutionProvider::variable( name, recurse );
		}

	private :

		const Context *m_context;
		mutable boost::optional<Context::EditableScope> m_scope;
		string m_selector;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// RowsPlug
//////////////////////////////////////////////////////////////////////////

GAFFER_PLUG_DEFINE_TYPE( Spreadsheet::RowsPlug );

// Manages a data structure mapping between row name
// and row, so we can implement `RowsPlug::row()` without
// linear search.
class Spreadsheet::RowsPlug::RowNameMap
{

	public :

		RowNameMap( Spreadsheet::RowsPlug *rowsPlug )
			:	m_rowsPlug( rowsPlug )
		{
			rowsPlug->childAddedSignal().connect( boost::bind( &RowNameMap::childAdded, this, ::_2 ) );
			rowsPlug->childRemovedSignal().connect( boost::bind( &RowNameMap::childRemoved, this, ::_2 ) );
			rowsPlug->parentChangedSignal().connect( boost::bind( &RowNameMap::parentChanged, this ) );
		}

		RowPlug *row( const string &rowName )
		{
			if( !m_plugSetConnection.connected() )
			{
				// If we can't track name changes, we must do
				// a brute force update. This should basically never
				// happen, so we put no effort into making something more
				// performant.
				updateRowNames();
			}

			const auto &index = m_map.get<1>();
			auto range = index.equal_range( rowName );
			if( range.first == index.end() )
			{
				return nullptr;
			}
			else if( range.first == range.second )
			{
				// Single row with the requested name.
				// This is the common case we are optimising
				// for.
				return range.first->plug;
			}
			else
			{
				// Multiple rows with the requested name.
				// We must return the first one.
				size_t minIndex = std::numeric_limits<size_t>::max();
				RowPlug *result = nullptr;
				for( auto it = range.first; it != range.second; ++it )
				{
					/// \todo We need GraphComponent to provide constant-time
					/// access to a child's index.
					const auto childIt = find( m_rowsPlug->children().begin(), m_rowsPlug->children().end(), it->plug );
					const size_t index = childIt - m_rowsPlug->children().begin();
					if( index < minIndex )
					{
						minIndex = index;
						result = it->plug;
					}
				}
				return result;
			}
		}

	private :

		string rowName( const RowPlug *row )
		{
			auto namePlug = row->namePlug()->source<StringPlug>();
			if( namePlug->direction() == Plug::Out )
			{
				return "__rowNameMap::computedNameSentinel__";
			}
			else
			{
				return row->namePlug()->getValue();
			}
		}

		void childAdded( GraphComponent *child )
		{
			auto row = static_cast<RowPlug *>( child ); // Guaranteed by `RowsPlug::acceptsChild()`.
			if( row != m_rowsPlug->defaultRow() )
			{
				m_map.insert( { row, rowName( row ) } );
			}
		}

		void childRemoved( GraphComponent *child )
		{
			auto row = static_cast<RowPlug *>( child ); // Guaranteed by `RowsPlug::acceptsChild()`.
			m_map.erase( row );
		}

		void parentChanged()
		{
			if( auto node = m_rowsPlug->node() )
			{
				m_plugSetConnection = node->plugSetSignal().connect( boost::bind( &RowNameMap::plugSet, this, ::_1 ) );
				m_plugInputChangedConnection = node->plugInputChangedSignal().connect( boost::bind( &RowNameMap::plugInputChanged, this, ::_1 ) );
				// While we had no parent, we couldn't track
				// value or input changes, so we must manually
				// update all the names.
				updateRowNames();
			}
			else
			{
				m_plugSetConnection.disconnect();
				m_plugInputChangedConnection.disconnect();
			}
		}

		void plugSet( Plug *plug )
		{
			updateRowName( plug );
		}

		void plugInputChanged( Plug *plug )
		{
			updateRowName( plug );
		}

		void updateRowName( Plug *plug )
		{
			if( auto row = plug->parent<RowPlug>() )
			{
				if( plug == row->namePlug() && row->parent() == m_rowsPlug && row != m_rowsPlug->defaultRow() )
				{
					auto it = m_map.find( row );
					assert( it != m_map.end() );
					m_map.get<1>().modify_key(
						m_map.project<1>( it ),
						[row, this] ( string &name ) {
							name = this->rowName( row );
						}
					);
				}
			}
		}

		void updateRowNames()
		{
			auto &index = m_map.get<1>();

			// `modify_key()` doesn't invalidate iterators, but it does
			// reorder them, so to visit everything we must first grab
			// all the iterators.
			std::vector<Map::nth_index<1>::type::iterator> iterators;
			for( auto it = index.begin(); it != index.end(); ++it )
			{
				iterators.push_back( it );
			}

			for( const auto &it : iterators )
			{
				index.modify_key(
					it,
					[it, this] ( string &name ) {
						name = this->rowName( it->plug );
					}
				);
			}
		}

		RowsPlug *m_rowsPlug;

		boost::signals::scoped_connection m_plugSetConnection;
		boost::signals::scoped_connection m_plugInputChangedConnection;

		struct Row
		{
			RowPlug *plug;
			string name;
		};

		using Map = multi_index::multi_index_container<
			Row,
			multi_index::indexed_by<
				multi_index::hashed_unique<
					multi_index::member<Row, RowPlug *, &Row::plug>
				>,
				multi_index::hashed_non_unique<
					multi_index::member<Row, string, &Row::name>
				>
			>
		>;

		Map m_map;

};

Spreadsheet::RowsPlug::RowsPlug( const std::string &name, Direction direction, unsigned flags )
	:	ValuePlug( name, direction, flags ), m_rowNameMap( new RowNameMap( this ) )
{
	RowPlugPtr defaultRow = new RowPlug( "default" );
	addChild( defaultRow );
}

Spreadsheet::RowsPlug::~RowsPlug()
{
}

Spreadsheet::RowPlug *Spreadsheet::RowsPlug::defaultRow()
{
	return getChild<RowPlug>( 0 );
}

const Spreadsheet::RowPlug *Spreadsheet::RowsPlug::defaultRow() const
{
	return getChild<RowPlug>( 0 );
}

Spreadsheet::RowPlug *Spreadsheet::RowsPlug::row( const std::string &rowName )
{
	return m_rowNameMap->row( rowName );
}

const Spreadsheet::RowPlug *Spreadsheet::RowsPlug::row( const std::string &rowName ) const
{
	return m_rowNameMap->row( rowName );
}

size_t Spreadsheet::RowsPlug::addColumn( const ValuePlug *value, IECore::InternedString name )
{
	if( name.string().empty() )
	{
		name = value->getName();
	}

	for( auto &row : RowPlug::Range( *this ) )
	{
		CellPlugPtr cellPlug = new CellPlug( name, value );
		cellPlug->valuePlug()->setFrom( value );
		row->cellsPlug()->addChild( cellPlug );
	}
	for( auto o : outPlugs() )
	{
		PlugPtr outColumn = value->createCounterpart( name, Plug::Out );
		outColumn->setFlags( Plug::Dynamic, false );
		o->addChild( outColumn );
	}
	return defaultRow()->cellsPlug()->children().size() - 1;

}

void Spreadsheet::RowsPlug::removeColumn( size_t columnIndex )
{
	if( columnIndex >= defaultRow()->cellsPlug()->children().size() )
	{
		throw IECore::Exception( "Column index out of range" );
	}

	for( auto o : outPlugs() )
	{
		o->removeChild( o->getChild( columnIndex ) );
	}
	for( auto &row : RowPlug::Range( *this ) )
	{
		row->cellsPlug()->removeChild( row->cellsPlug()->getChild( columnIndex ) );
	}
}

Spreadsheet::RowPlug *Spreadsheet::RowsPlug::addRow()
{
	// We need to use the `Dynamic` flag so that we get dirty propagation via
	// `Plug::propagateDirtinessForParentChange()`.
	RowPlugPtr newRow = new RowPlug( "row" + boost::lexical_cast<std::string>( children().size() ), direction(), Default | Dynamic );
	for( auto &defaultCell : CellPlug::Range( *defaultRow()->cellsPlug() ) )
	{
		CellPlugPtr newCell = boost::static_pointer_cast<CellPlug>(
			defaultCell->createCounterpart( defaultCell->getName(), Plug::In )
		);
		newCell->setFrom( defaultCell.get() );
		newRow->cellsPlug()->addChild( newCell );
	}
	addChild( newRow );
	return newRow.get();
}

void Spreadsheet::RowsPlug::addRows( size_t numRows )
{
	for( ; numRows; --numRows )
	{
		addRow();
	}
}

void Spreadsheet::RowsPlug::removeRow( Spreadsheet::RowPlugPtr row )
{
	if( row->parent() != this )
	{
		throw Exception( boost::str(
			boost::format( "Row \"%1%\" is not a child of \"%2%\"." ) % row->fullName() % fullName()
		) );
	}

	if( row == getChild( 0 ) )
	{
		throw Exception( boost::str(
			boost::format( "Cannot remove default row from \"%1%\"." ) % fullName()
		) );
	}

	removeChild( row );
}

std::vector<Gaffer::ValuePlug *> Spreadsheet::RowsPlug::outPlugs()
{
	// Find `Spreadsheet::outPlug()` on all the Spreadsheet nodes
	// driven by this plug. Because of plug promotion, an `outPlug()`
	// may belong to a different node than ours, and if someone has
	// been really creative we might even be driving multiple
	// spreadsheets.
	//
	// We use this from `add/removeColumn()` so that we can add the
	// appropriate columns to the output plugs. It's not ideal that
	// this responsibility falls to us. What might be nice would be
	// to rename RowsPlug to SheetPlug and let it manage both "rows"
	// and "out" children, so that it's more natural to modify "out".
	// We can't do that at present because we don't allow connections
	// to plugs which have a mix of input and output children.

	vector<Gaffer::ValuePlug *> result;
	if( auto *s = parent<Spreadsheet>() )
	{
		if( s->rowsPlug() == this )
		{
			result.push_back( s->outPlug() );
		}
	}

	for( auto output : outputs() )
	{
		if( auto outputRow = runTimeCast<Spreadsheet::RowsPlug>( output ) )
		{
			auto v = outputRow->outPlugs();
			result.insert( result.end(), v.begin(), v.end() );
		}
	}

	return result;
}

bool Spreadsheet::RowsPlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	return runTimeCast<const RowPlug>( potentialChild );
}

Gaffer::PlugPtr Spreadsheet::RowsPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	RowsPlugPtr result = new RowsPlug( name, direction, getFlags() );
	for( const auto &row : RowPlug::Range( *this ) )
	{
		// Using `setChild()` rather than `addChild()` because we want to replace
		// the default-constructed default row with one with the right number of
		// cells.
		result->setChild( row->getName(), row->createCounterpart( row->getName(), direction ) );
	}
	return result;
}

//////////////////////////////////////////////////////////////////////////
// RowPlug
//////////////////////////////////////////////////////////////////////////

GAFFER_PLUG_DEFINE_TYPE( Spreadsheet::RowPlug );

Spreadsheet::RowPlug::RowPlug( const std::string &name, Plug::Direction direction, unsigned flags )
	:	ValuePlug( name, direction, flags )
{
	addChild( new StringPlug( "name", direction ) );
	addChild( new BoolPlug( "enabled",direction, true ) );
	addChild( new ValuePlug( "cells", direction ) );
}

StringPlug *Spreadsheet::RowPlug::namePlug()
{
	return getChild<StringPlug>( 0 );
}

const StringPlug *Spreadsheet::RowPlug::namePlug() const
{
	return getChild<StringPlug>( 0 );
}

BoolPlug *Spreadsheet::RowPlug::enabledPlug()
{
	return getChild<BoolPlug>( 1 );
}

const BoolPlug *Spreadsheet::RowPlug::enabledPlug() const
{
	return getChild<BoolPlug>( 1 );
}

ValuePlug *Spreadsheet::RowPlug::cellsPlug()
{
	return getChild<ValuePlug>( 2 );
}

const ValuePlug *Spreadsheet::RowPlug::cellsPlug() const
{
	return getChild<ValuePlug>( 2 );
}

Gaffer::PlugPtr Spreadsheet::RowPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	RowPlugPtr result = new RowPlug( name, direction );
	for( const auto &cell : CellPlug::Range( *cellsPlug() ) )
	{
		result->cellsPlug()->addChild( cell->createCounterpart( cell->getName(), direction ) );
	}
	return result;
}

//////////////////////////////////////////////////////////////////////////
// CellPlug
//////////////////////////////////////////////////////////////////////////

GAFFER_PLUG_DEFINE_TYPE( Spreadsheet::CellPlug );

Spreadsheet::CellPlug::CellPlug( const std::string &name, const Gaffer::Plug *value, Plug::Direction direction )
	:	ValuePlug( name, direction )
{
	addChild( new BoolPlug( "enabled", direction, true ) );
	addChild( value->createCounterpart( "value", direction ) );
	valuePlug()->setFlags( Plug::Dynamic, false );
}

BoolPlug *Spreadsheet::CellPlug::enabledPlug()
{
	return getChild<BoolPlug>( 0 );
}

const BoolPlug *Spreadsheet::CellPlug::enabledPlug() const
{
	return getChild<BoolPlug>( 0 );
}

Gaffer::PlugPtr Spreadsheet::CellPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new CellPlug( name, valuePlug(), direction );
}

//////////////////////////////////////////////////////////////////////////
// Spreadsheet
//////////////////////////////////////////////////////////////////////////

size_t Spreadsheet::g_firstPlugIndex = 0;
GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Spreadsheet );

Spreadsheet::Spreadsheet( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new BoolPlug( "enabled", Plug::In, true ) );
	addChild( new StringPlug( "selector", Plug::In, "", Plug::Default, IECore::StringAlgo::NoSubstitutions ) );
	addChild( new RowsPlug( "rows" ) );
	addChild( new ValuePlug( "out", Plug::Out ) );
	addChild( new StringVectorDataPlug( "activeRowNames", Plug::Out, new IECore::StringVectorData ) );
	addChild( new ObjectPlug( "__rowsMap", Plug::Out, IECore::NullObject::defaultNullObject() ) );
	addChild( new IntPlug( "__rowIndex", Plug::Out ) );
}

Spreadsheet::~Spreadsheet()
{
}

BoolPlug *Spreadsheet::enabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

const BoolPlug *Spreadsheet::enabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

StringPlug *Spreadsheet::selectorPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const StringPlug *Spreadsheet::selectorPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Spreadsheet::RowsPlug *Spreadsheet::rowsPlug()
{
	return getChild<RowsPlug>( g_firstPlugIndex + 2 );
}

const Spreadsheet::RowsPlug *Spreadsheet::rowsPlug() const
{
	return getChild<RowsPlug>( g_firstPlugIndex + 2 );
}

ValuePlug *Spreadsheet::outPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 3 );
}

const ValuePlug *Spreadsheet::outPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 3 );
}

StringVectorDataPlug *Spreadsheet::activeRowNamesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 4 );
}

const StringVectorDataPlug *Spreadsheet::activeRowNamesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 4 );
}

ObjectPlug *Spreadsheet::rowsMapPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 5 );
}

const ObjectPlug *Spreadsheet::rowsMapPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 5 );
}

IntPlug *Spreadsheet::rowIndexPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 6 );
}

const IntPlug *Spreadsheet::rowIndexPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 6 );
}

void Spreadsheet::affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( const auto *row = input->parent<RowPlug>() )
	{
		if(
			input == row->namePlug() ||
			input == row->enabledPlug()
		)
		{
			outputs.push_back( rowsMapPlug() );
		}
	}

	if(
		input == enabledPlug() ||
		input == selectorPlug() ||
		input == rowsMapPlug()
	)
	{
		outputs.push_back( rowIndexPlug() );
	}

	if( input == rowIndexPlug() )
	{
		appendLeafPlugs( outPlug(), outputs );
	}

	if( const auto *cell = input->ancestor<CellPlug>() )
	{
		if( const Plug *out = outPlug()->getChild<ValuePlug>( cell->getName() ) )
		{
			if( input == cell->enabledPlug() )
			{
				appendLeafPlugs( out, outputs );
			}
			else if( input == cell->valuePlug() )
			{
				outputs.push_back( out );
			}
			else
			{
				outputs.push_back(
					out->descendant<Plug>( input->relativeName( cell->valuePlug() ) )
				);
			}
		}
	}

	if( input == rowsMapPlug() )
	{
		outputs.push_back( activeRowNamesPlug() );
	}
}

Plug *Spreadsheet::correspondingInput( const Plug *output )
{
	return const_cast<Plug *>( const_cast<const Spreadsheet *>( this)->correspondingInput( output ) );
}

const Plug *Spreadsheet::correspondingInput( const Plug *output ) const
{
	if( const Plug *p = correspondingInput( output, /* rowIndex = */ 0 ) )
	{
		return p;
	}

	return DependencyNode::correspondingInput( output );
}

void Spreadsheet::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	if( output == rowsMapPlug() )
	{
		ComputeNode::hash( output, context, h );
		for( int i = 1, e = rowsPlug()->children().size(); i < e; ++i )
		{
			const auto *row = rowsPlug()->getChild<RowPlug>( i );
			row->namePlug()->hash( h );
			row->enabledPlug()->hash( h );
		}
		return;
	}
	else if( output == rowIndexPlug() )
	{
		ComputeNode::hash( output, context, h );
		enabledPlug()->hash( h );
		RowsMapScope rowsMapScope( context, selectorPlug()->getValue() );
		rowsMapPlug()->hash( h );
		h.append( rowsMapScope.selector() );
		return;
	}
	else if( outPlug()->isAncestorOf( output ) )
	{
		h = correspondingInput( output, rowIndexPlug()->getValue() )->hash();
		return;
	}
	else if( output == activeRowNamesPlug() )
	{
		ComputeNode::hash( output, context, h );
		RowsMapScope rowsMapScope( context, selectorPlug()->getValue() );
		rowsMapPlug()->hash( h );
		return;
	}

	ComputeNode::hash( output, context, h );
}

void Spreadsheet::compute( ValuePlug *output, const Context *context ) const
{
	if( output == rowsMapPlug() )
	{
		StringVectorDataPtr activeRowNamesData = new StringVectorData;
		vector<string> &activeRowNames = activeRowNamesData->writable();
		RowsMapPtr result = new RowsMap;
		result->activeRowNames = activeRowNamesData;

		for( size_t i = 1, e = rowsPlug()->children().size(); i < e; ++i )
		{
			const auto *row = rowsPlug()->getChild<RowPlug>( i );
			if( !row->enabledPlug()->getValue() )
			{
				continue;
			}

			const std::string name = row->namePlug()->getValue();
			activeRowNames.push_back( name );

			if(
				StringAlgo::hasWildcards( name ) ||
				name.find( ' ' ) != string::npos
			)
			{
				result->wildcardRows.push_back( { name, i } );
			}
			else
			{
				result->plainRows.insert( { name, i } );
			}
		}

		static_cast<ObjectPlug *>( output )->setValue( result );
		return;
	}
	else if( output == rowIndexPlug() )
	{
		size_t result = 0;
		if( enabledPlug()->getValue() )
		{
			RowsMapScope rowsMapScope( context, selectorPlug()->getValue() );
			ConstRowsMapPtr rowsMap = boost::static_pointer_cast<const RowsMap>( rowsMapPlug()->getValue() );

			RowsMap::Map::const_iterator it = rowsMap->plainRows.find( rowsMapScope.selector() );
			if( it != rowsMap->plainRows.end() )
			{
				result = it->second;
			}
			for( auto &row : rowsMap->wildcardRows )
			{
				if( result && row.index > result )
				{
					break;
				}

				if( StringAlgo::matchMultiple( rowsMapScope.selector(), row.name ) )
				{
					result = row.index;
					break;
				}
			}
		}
		static_cast<IntPlug *>( output )->setValue( result );
		return;
	}
	else if( outPlug()->isAncestorOf( output ) )
	{
		output->setFrom( correspondingInput( output, rowIndexPlug()->getValue() ) );
		return;
	}
	else if( output == activeRowNamesPlug() )
	{
		RowsMapScope rowsMapScope( context, selectorPlug()->getValue() );
		ConstRowsMapPtr rowsMap = boost::static_pointer_cast<const RowsMap>( rowsMapPlug()->getValue() );
		static_cast<StringVectorDataPlug *>( output )->setValue( rowsMap->activeRowNames );
		return;
	}

	ComputeNode::compute( output, context );
}

const ValuePlug *Spreadsheet::correspondingInput( const Plug *plug, size_t rowIndex ) const
{
	const ValuePlug *out = outPlug();
	boost::container::small_vector<IECore::InternedString, 4> names;
	while( plug && plug != out )
	{
		names.push_back( plug->getName() );
		plug = plug->parent<Plug>();
	}

	if( !plug || names.empty() )
	{
		return nullptr;
	}

	const CellPlug *cell = rowsPlug()->getChild<RowPlug>( rowIndex )->cellsPlug()->getChild<CellPlug>( names.back() );
	if( rowIndex && !cell->enabledPlug()->getValue() )
	{
		cell = rowsPlug()->defaultRow()->cellsPlug()->getChild<CellPlug>( names.back() );
	}

	names.pop_back();
	const ValuePlug *result = cell->valuePlug();
	for( auto it = names.rbegin(), eIt = names.rend(); it != eIt; ++it )
	{
		result = result->getChild<ValuePlug>( *it );
	}

	return result;
}

ValuePlug *Spreadsheet::activeInPlug( const ValuePlug *output )
{
	return const_cast<ValuePlug *>( correspondingInput( output, rowIndexPlug()->getValue() ) );
}

const ValuePlug *Spreadsheet::activeInPlug( const ValuePlug *output ) const
{
	return correspondingInput( output, rowIndexPlug()->getValue() );
}
