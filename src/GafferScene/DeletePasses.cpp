//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/DeletePasses.h"

#include "Gaffer/StringPlug.h"

#include "IECore/StringAlgo.h"

using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( DeletePasses );

const std::string g_passNamesOptionName = "option:pass:names";

size_t DeletePasses::g_firstPlugIndex = 0;

DeletePasses::DeletePasses( const std::string &name )
	:	GlobalsProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "mode", Plug::In, Delete, Delete, Keep ) );
	addChild( new StringPlug( "names" ) );
}

DeletePasses::~DeletePasses()
{
}

Gaffer::IntPlug *DeletePasses::modePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *DeletePasses::modePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *DeletePasses::namesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *DeletePasses::namesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

void DeletePasses::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	GlobalsProcessor::affects( input, outputs );

	if( input == modePlug() || input == namesPlug() )
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void DeletePasses::hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	modePlug()->hash( h );
	namesPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr DeletePasses::computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const
{
	if( !inputGlobals->members().count( g_passNamesOptionName ) )
	{
		return inputGlobals;
	}

	const Mode mode = static_cast<Mode>( modePlug()->getValue() );
	const std::string names = namesPlug()->getValue();
	if( !mode && !names.size() )
	{
		return inputGlobals;
	}

	IECore::CompoundObjectPtr result = new IECore::CompoundObject();
	result->members() = inputGlobals->members();

	auto copy = result->member<IECore::StringVectorData>( g_passNamesOptionName )->copy();
	copy->writable().erase(
		std::remove_if(
			copy->writable().begin(),
			copy->writable().end(),
			[names, mode]( const auto &elem )
			{
				return IECore::StringAlgo::matchMultiple( elem, names ) == ( mode == Delete );
			}
		),
		copy->writable().end()
	);

	result->members()[g_passNamesOptionName] = copy;

	return result;
}
