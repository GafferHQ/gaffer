//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "Gaffer/ContextVariables.h"

#include "Gaffer/Context.h"

#include "IECore/SimpleTypedData.h"
#include "IECore/DataAlgo.h"

using namespace Gaffer;

namespace {

struct SetFromReadable
{
	template< class T>
	void operator()( const T *data, Gaffer::Context::EditableScope &scope, const IECore::InternedString &name )
	{
		scope.set( name, &data->readable() );
	}
};

}

GAFFER_NODE_DEFINE_TYPE( ContextVariables );

size_t ContextVariables::g_firstPlugIndex;

ContextVariables::ContextVariables( const std::string &name )
	:	ContextProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new CompoundDataPlug( "variables" ) );
	addChild( new AtomicCompoundDataPlug( "extraVariables", Plug::In, new IECore::CompoundData ) );
	addChild( new AtomicCompoundDataPlug( "__combinedVariables", Plug::Out, new IECore::CompoundData ) );
}

ContextVariables::~ContextVariables()
{
}

CompoundDataPlug *ContextVariables::variablesPlug()
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex );
}

const CompoundDataPlug *ContextVariables::variablesPlug() const
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex );
}

AtomicCompoundDataPlug *ContextVariables::extraVariablesPlug()
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 1 );
}

const AtomicCompoundDataPlug *ContextVariables::extraVariablesPlug() const
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 1 );
}

AtomicCompoundDataPlug *ContextVariables::combinedVariablesPlug()
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 2 );
}

const AtomicCompoundDataPlug *ContextVariables::combinedVariablesPlug() const
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 2 );
}

void ContextVariables::affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const
{
	ContextProcessor::affects( input, outputs );

	if( variablesPlug()->isAncestorOf( input ) || input == extraVariablesPlug() )
	{
		outputs.push_back( combinedVariablesPlug() );
	}
}


bool ContextVariables::affectsContext( const Plug *input ) const
{
	return input == combinedVariablesPlug();
}

void ContextVariables::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ContextProcessor::hash( output, context, h );

	if( output == combinedVariablesPlug() )
	{
		variablesPlug()->hash( h );
		extraVariablesPlug()->hash( h );
	}
}

void ContextVariables::compute( ValuePlug *output, const Context *context ) const
{
	if( output == combinedVariablesPlug() )
	{
		IECore::CompoundDataPtr resultData = new IECore::CompoundData( extraVariablesPlug()->getValue()->readable() );
		IECore::CompoundDataMap &result = resultData->writable();

		std::string name;
		for( NameValuePlug::Iterator it( variablesPlug() ); !it.done(); ++it )
		{
			IECore::DataPtr data = variablesPlug()->memberDataAndName( it->get(), name );
			if( data )
			{
				result.insert( { IECore::InternedString( name ), data } );
			}
		}
		static_cast<AtomicCompoundDataPlug *>( output )->setValue( resultData );
		return;
	}

	return ContextProcessor::compute( output, context );
}


void ContextVariables::processContext( Context::EditableScope &context, IECore::ConstRefCountedPtr &storage ) const
{
	SetFromReadable setFromReadable;
	IECore::ConstCompoundDataPtr combinedVariables = combinedVariablesPlug()->getValue();
	for( const auto &variable : combinedVariables->readable() )
	{
		IECore::dispatch( variable.second.get(), setFromReadable, context, variable.first );
	}
	storage = combinedVariables;
}
