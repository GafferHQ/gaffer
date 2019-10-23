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

#include "boost/container/small_vector.hpp"

using namespace std;
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

} // namespace

//////////////////////////////////////////////////////////////////////////
// RowsPlug
//////////////////////////////////////////////////////////////////////////

GAFFER_PLUG_DEFINE_TYPE( Spreadsheet::RowsPlug );

Spreadsheet::RowsPlug::RowsPlug( const std::string &name, Direction direction, unsigned flags )
	:	ValuePlug( name, direction, flags )
{
	RowPlugPtr defaultRow = new RowPlug( "default" );
	addChild( defaultRow );
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
	if( auto *o = outPlug() )
	{
		PlugPtr outColumn = value->createCounterpart( name, Plug::Out );
		outColumn->setFlags( Plug::Dynamic, false );
		o->addChild( outColumn );
	}
	return getChild<RowPlug>( 0 )->cellsPlug()->children().size() - 1;

}

void Spreadsheet::RowsPlug::removeColumn( size_t columnIndex )
{
	if( columnIndex >= getChild<RowPlug>( 0 )->cellsPlug()->children().size() )
	{
		throw IECore::Exception( "Column index out of range" );
	}

	for( auto &row : RowPlug::Range( *this ) )
	{
		row->cellsPlug()->removeChild( row->cellsPlug()->getChild( columnIndex ) );
	}
	if( auto *o = outPlug() )
	{
		o->removeChild( o->getChild( columnIndex ) );
	}
}

Spreadsheet::RowPlug *Spreadsheet::RowsPlug::addRow()
{
	RowPlugPtr newRow = new RowPlug( "row1" );
	for( auto &defaultCell : CellPlug::Range( *getChild<RowPlug>( 0 )->cellsPlug() ) )
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

Gaffer::ValuePlug *Spreadsheet::RowsPlug::outPlug()
{
	// Find the `outPlug()` on our parent Spreadsheet node.
	// We use this from `add/removeColumn()` so that we can
	// add the appropriate columns to the output plug. It's
	// not ideal that this responsibility falls to us. What
	// might be nice would be to rename RowsPlug to SheetPlug
	// and let it manage both "rows" and "out" children, so
	// that it's more natural to modify "out". We can't do that
	// at present because we don't allow connections to plugs
	// which have a mix of input and output children.
	if( auto *s = parent<Spreadsheet>() )
	{
		return s->outPlug();
	}
	return nullptr;
}


Gaffer::PlugPtr Spreadsheet::RowsPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	RowsPlugPtr result = new RowsPlug( name, direction, getFlags() );
	for( const auto &row : RowPlug::Range( *this ) )
	{
		result->setChild( row->getName(), row->createCounterpart( row->getName(), direction ) );
	}
	return result;
}

//////////////////////////////////////////////////////////////////////////
// RowPlug
//////////////////////////////////////////////////////////////////////////

GAFFER_PLUG_DEFINE_TYPE( Spreadsheet::RowPlug );

Spreadsheet::RowPlug::RowPlug( const std::string &name, Plug::Direction direction )
	:	ValuePlug( name )
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
	addChild( new StringPlug( "selector" ) );
	addChild( new RowsPlug( "rows" ) );
	addChild( new ValuePlug( "out", Plug::Out ) );
	addChild( new StringVectorDataPlug( "activeRowNames", Plug::Out, new IECore::StringVectorData ) );
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

ValuePlug *Spreadsheet::rowsPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 2 );
}

const ValuePlug *Spreadsheet::rowsPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 2 );
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

IntPlug *Spreadsheet::rowIndexPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 5 );
}

const IntPlug *Spreadsheet::rowIndexPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 5 );
}

void Spreadsheet::affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	const auto *row = input->parent<RowPlug>();
	if(
		input == enabledPlug() ||
		input == selectorPlug() ||
		( row && input == row->namePlug() ) ||
		( row && input == row->enabledPlug() )
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

	if(
		( row && input == row->namePlug() ) ||
		( row && input == row->enabledPlug() )
	)
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
	if( output == rowIndexPlug() )
	{
		ComputeNode::hash( output, context, h );
		enabledPlug()->hash( h );
		selectorPlug()->hash( h );
		for( int i = 1, e = rowsPlug()->children().size(); i < e; ++i )
		{
			const auto *row = rowsPlug()->getChild<RowPlug>( i );
			row->namePlug()->hash( h );
			row->enabledPlug()->hash( h );
		}
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
		for( int i = 1, e = rowsPlug()->children().size(); i < e; ++i )
		{
			const auto *row = rowsPlug()->getChild<RowPlug>( i );
			row->namePlug()->hash( h );
			row->enabledPlug()->hash( h );
		}
		return;
	}

	ComputeNode::hash( output, context, h );
}

void Spreadsheet::compute( ValuePlug *output, const Context *context ) const
{
	if( output == rowIndexPlug() )
	{
		int result = 0;
		if( enabledPlug()->getValue() )
		{
			const std::string selector = selectorPlug()->getValue();
			for( int i = 1, e = rowsPlug()->children().size(); i < e; ++i )
			{
				const auto *row = rowsPlug()->getChild<RowPlug>( i );
				if( !row->enabledPlug()->getValue() )
				{
					continue;
				}
				if( StringAlgo::matchMultiple( selector, row->namePlug()->getValue() ) )
				{
					result = i;
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
		StringVectorDataPtr resultData = new StringVectorData;
		auto &result = resultData->writable();
		result.reserve( rowsPlug()->children().size() - 1 );

		for( int i = 1, e = rowsPlug()->children().size(); i < e; ++i )
		{
			const auto *row = rowsPlug()->getChild<RowPlug>( i );
			if( row->enabledPlug()->getValue() )
			{
				result.push_back( row->namePlug()->getValue() );
			}
		}
		static_cast<StringVectorDataPlug *>( output )->setValue( resultData );
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
		cell = rowsPlug()->getChild<RowPlug>( 0 )->cellsPlug()->getChild<CellPlug>( names.back() );
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
