//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "boost/multi_index_container.hpp"
#include "boost/multi_index/sequenced_index.hpp"
#include "boost/multi_index/ordered_index.hpp"
#include "boost/multi_index/member.hpp"

#include "IECore/Display.h"

#include "Gaffer/CompoundDataPlug.h"

#include "GafferScene/Displays.h"

using namespace std;
using namespace boost;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Data structure for the registry
//////////////////////////////////////////////////////////////////////////

typedef std::pair<std::string, DisplayPtr> NamedDisplay;
typedef multi_index::multi_index_container<
	NamedDisplay,
	multi_index::indexed_by<
		multi_index::ordered_unique<
			multi_index::member<NamedDisplay, std::string, &NamedDisplay::first>
		>,
		multi_index::sequenced<>
	>
> DisplayMap;

static DisplayMap &displayMap()
{
	static DisplayMap m;
	return m;
}

//////////////////////////////////////////////////////////////////////////
// Displays implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Displays );

size_t Displays::g_firstPlugIndex = 0;

Displays::Displays( const std::string &name )
	:	GlobalsProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new CompoundPlug( "displays" ) );
}

Displays::~Displays()
{
}

Gaffer::CompoundPlug *Displays::displaysPlug()
{
	return getChild<CompoundPlug>( g_firstPlugIndex );
}

const Gaffer::CompoundPlug *Displays::displaysPlug() const
{
	return getChild<CompoundPlug>( g_firstPlugIndex );
}

Gaffer::CompoundPlug *Displays::addDisplay( const std::string &label )
{
	DisplayMap::nth_index<0>::type &index = displayMap().get<0>();
	DisplayMap::const_iterator it = index.find( label );
	if( it == index.end() )
	{
		throw Exception( "Display not registered" );
	}
	return addDisplay( it->first, it->second.get() );
}

Gaffer::CompoundPlug *Displays::addDisplay( const std::string &label, const IECore::Display *display )
{
	CompoundPlugPtr displayPlug = new CompoundPlug( "display1" );
	displayPlug->setFlags( Plug::Dynamic, true );
	
	StringPlugPtr labelPlug = new StringPlug( "label" );
	labelPlug->setValue( label );
	labelPlug->setFlags( Plug::Dynamic, true );
	displayPlug->addChild( labelPlug );
	
	BoolPlugPtr activePlug = new BoolPlug( "active", Plug::In, true );
	activePlug->setFlags( Plug::Dynamic, true );
	displayPlug->addChild( activePlug );
	
	StringPlugPtr namePlug = new StringPlug( "name" );
	namePlug->setValue( display->getName() );
	namePlug->setFlags( Plug::Dynamic, true );
	displayPlug->addChild( namePlug );

	StringPlugPtr typePlug = new StringPlug( "type" );
	typePlug->setValue( display->getType() );
	typePlug->setFlags( Plug::Dynamic, true );
	displayPlug->addChild( typePlug );
	
	StringPlugPtr dataPlug = new StringPlug( "data" );
	dataPlug->setValue( display->getData() );
	dataPlug->setFlags( Plug::Dynamic, true );
	displayPlug->addChild( dataPlug );
	
	CompoundDataPlugPtr parametersPlug = new CompoundDataPlug( "parameters" );
	parametersPlug->setFlags( Plug::Dynamic, true );
	parametersPlug->addMembers( const_cast<Display *>( display )->parametersData() );
	displayPlug->addChild( parametersPlug );
	
	displaysPlug()->addChild( displayPlug );
	
	return displayPlug;
}

void Displays::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	GlobalsProcessor::affects( input, outputs );
	
	if( displaysPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void Displays::hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	displaysPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr Displays::computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const
{
	const CompoundPlug *dsp = displaysPlug(); 
	if( !dsp->children().size() )
	{
		return inputGlobals;
	}
	
	CompoundObjectPtr result = inputGlobals->copy();
	
	// add our displays to the result
	for( InputCompoundPlugIterator it( dsp ); it != it.end(); it++ )
	{
		const CompoundPlug *displayPlug = *it;
		if( displayPlug->getChild<BoolPlug>( "active" )->getValue() )
		{
			std::string name = displayPlug->getChild<StringPlug>( "name" )->getValue();
			std::string type = displayPlug->getChild<StringPlug>( "type" )->getValue();
			std::string data = displayPlug->getChild<StringPlug>( "data" )->getValue();
			if( name.size() && type.size() && data.size() )
			{
				DisplayPtr d = new Display( name, type, data );
				displayPlug->getChild<CompoundDataPlug>( "parameters" )->fillCompoundData( d->parameters() );
				result->members()["display:" + name] = d;
			}
		}
	}
	
	return result;
}

void Displays::registerDisplay( const std::string &label, const IECore::Display *display )
{
	NamedDisplay d( label, display->copy() );
	
	DisplayMap::nth_index<0>::type &index = displayMap().get<0>();
	DisplayMap::const_iterator it = index.find( label );
	if( it == index.end() )
	{
		index.insert( d );
	}
	else
	{
		index.replace( it, d );
	}
}

void Displays::registeredDisplays( std::vector<std::string> &labels )
{
	const DisplayMap::nth_index<1>::type &index = displayMap().get<1>();
	for( DisplayMap::nth_index<1>::type::const_iterator it=index.begin(); it!=index.end(); it++ )
	{
		labels.push_back( it->first );
	}
}
