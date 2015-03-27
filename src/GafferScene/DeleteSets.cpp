//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/StringAlgo.h"

#include "GafferScene/DeleteSets.h"

using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( DeleteSets );

size_t DeleteSets::g_firstPlugIndex(0);

DeleteSets::DeleteSets( const std::string &name )
	:	GlobalsProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "names" ) );
	addChild( new BoolPlug( "invertNames" ) );
}

DeleteSets::~DeleteSets()
{
}


Gaffer::StringPlug *DeleteSets::namesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *DeleteSets::namesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *DeleteSets::invertNamesPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *DeleteSets::invertNamesPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

void DeleteSets::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	GlobalsProcessor::affects( input, outputs );

	if( input == namesPlug() || input == invertNamesPlug() )
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void DeleteSets::hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	namesPlug()->hash(h);
	invertNamesPlug()->hash(h);
}

IECore::ConstCompoundObjectPtr DeleteSets::computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const
{
	IECore::CompoundObjectPtr outputGlobals = new IECore::CompoundObject;
	outputGlobals->members() = inputGlobals->members();

	IECore::ConstCompoundDataPtr inSets = inputGlobals->member<IECore::CompoundData>("gaffer:sets");

	if( inSets )
	{
		IECore::CompoundData* outSets = new IECore::CompoundData;
		outputGlobals->members()["gaffer:sets"] = outSets;

		const std::string names = namesPlug()->getValue();

		bool invert = invertNamesPlug()->getValue();
		for( IECore::CompoundDataMap::const_iterator it = inSets->readable().begin(); it != inSets->readable().end(); ++it )
		{
			if( matchMultiple( it->first, names ) != (!invert) )
			{
				outSets->writable()[it->first] = const_cast<IECore::Data*>( it->second.get() );
			}
		}
	}

	return outputGlobals;
}
