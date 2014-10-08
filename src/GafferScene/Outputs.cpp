//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/CompoundDataPlug.h"

#include "GafferScene/Outputs.h"

using namespace std;
using namespace boost;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Data structure for the registry
//////////////////////////////////////////////////////////////////////////

namespace
{

typedef std::pair<std::string, DisplayPtr> NamedOutput;
typedef multi_index::multi_index_container<
	NamedOutput,
	multi_index::indexed_by<
		multi_index::ordered_unique<
			multi_index::member<NamedOutput, std::string, &NamedOutput::first>
		>,
		multi_index::sequenced<>
	>
> OutputMap;

OutputMap &outputMap()
{
	static OutputMap m;
	return m;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Outputs implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Outputs );

size_t Outputs::g_firstPlugIndex = 0;

Outputs::Outputs( const std::string &name )
	:	GlobalsProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new CompoundPlug( "outputs" ) );
}

Outputs::~Outputs()
{
}

Gaffer::CompoundPlug *Outputs::outputsPlug()
{
	return getChild<CompoundPlug>( g_firstPlugIndex );
}

const Gaffer::CompoundPlug *Outputs::outputsPlug() const
{
	return getChild<CompoundPlug>( g_firstPlugIndex );
}

Gaffer::CompoundPlug *Outputs::addOutput( const std::string &name )
{
	OutputMap::nth_index<0>::type &index = outputMap().get<0>();
	OutputMap::const_iterator it = index.find( name );
	if( it == index.end() )
	{
		throw Exception( "Output not registered" );
	}
	return addOutput( it->first, it->second.get() );
}

Gaffer::CompoundPlug *Outputs::addOutput( const std::string &name, const IECore::Display *output )
{
	CompoundPlugPtr outputPlug = new CompoundPlug( "output1" );
	outputPlug->setFlags( Plug::Dynamic, true );

	StringPlugPtr namePlug = new StringPlug( "name" );
	namePlug->setValue( name );
	namePlug->setFlags( Plug::Dynamic, true );
	outputPlug->addChild( namePlug );

	BoolPlugPtr activePlug = new BoolPlug( "active", Plug::In, true );
	activePlug->setFlags( Plug::Dynamic, true );
	outputPlug->addChild( activePlug );

	StringPlugPtr fileNamePlug = new StringPlug( "fileName" );
	fileNamePlug->setValue( output->getName() );
	fileNamePlug->setFlags( Plug::Dynamic, true );
	outputPlug->addChild( fileNamePlug );

	StringPlugPtr typePlug = new StringPlug( "type" );
	typePlug->setValue( output->getType() );
	typePlug->setFlags( Plug::Dynamic, true );
	outputPlug->addChild( typePlug );

	StringPlugPtr dataPlug = new StringPlug( "data" );
	dataPlug->setFlags( Plug::Dynamic, true );
	outputPlug->addChild( dataPlug );

	CompoundDataPlugPtr parametersPlug = new CompoundDataPlug( "parameters" );
	parametersPlug->setFlags( Plug::Dynamic, true );
	parametersPlug->addMembers( const_cast<Display *>( output )->parametersData(), /* useNameAsPlugName = */ true );
	outputPlug->addChild( parametersPlug );

	outputsPlug()->addChild( outputPlug );

	// set one of the values _after_ adding the plug, otherwise
	// affects() is not called and we have no opportunity to
	// propagate dirtiness to our output globals.
	dataPlug->setValue( output->getData() );

	return outputPlug.get();
}

void Outputs::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	GlobalsProcessor::affects( input, outputs );

	if( outputsPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void Outputs::hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	outputsPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr Outputs::computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const
{
	const CompoundPlug *dsp = outputsPlug();
	if( !dsp->children().size() )
	{
		return inputGlobals;
	}

	IECore::CompoundObjectPtr result = new IECore::CompoundObject;
	// Since we're not going to modify any existing members (only add new ones),
	// and our result becomes const on returning it, we can directly reference
	// the input members in our result without copying. Be careful not to modify
	// them though!
	result->members() = inputGlobals->members();

	// add our outputs to the result
	for( InputCompoundPlugIterator it( dsp ); it != it.end(); it++ )
	{
		const CompoundPlug *outputPlug = it->get();
		if( outputPlug->getChild<BoolPlug>( "active" )->getValue() )
		{
			// backwards compatibility with old plug layout
			const StringPlug *namePlug = outputPlug->getChild<StringPlug>( "label" );
			if( !namePlug )
			{
				namePlug = outputPlug->getChild<StringPlug>( "name" );
			}
			const std::string name = namePlug->getValue();

			const StringPlug *fileNamePlug = outputPlug->getChild<StringPlug>( "fileName" );
			if( !fileNamePlug )
			{
				// backwards compatibility with old plug layout
				fileNamePlug = outputPlug->getChild<StringPlug>( "name" );
			}
			const std::string fileName = fileNamePlug->getValue();

			const std::string type = outputPlug->getChild<StringPlug>( "type" )->getValue();
			const std::string data = outputPlug->getChild<StringPlug>( "data" )->getValue();
			if( name.size() && fileName.size() && type.size() && data.size() )
			{
				DisplayPtr d = new Display( fileName, type, data );
				outputPlug->getChild<CompoundDataPlug>( "parameters" )->fillCompoundData( d->parameters() );
				result->members()["output:" + name] = d;
			}
		}
	}

	return result;
}

void Outputs::registerOutput( const std::string &name, const IECore::Display *output )
{
	NamedOutput d( name, output->copy() );

	OutputMap::nth_index<0>::type &index = outputMap().get<0>();
	OutputMap::const_iterator it = index.find( name );
	if( it == index.end() )
	{
		index.insert( d );
	}
	else
	{
		index.replace( it, d );
	}
}

void Outputs::registeredOutputs( std::vector<std::string> &names )
{
	const OutputMap::nth_index<1>::type &index = outputMap().get<1>();
	for( OutputMap::nth_index<1>::type::const_iterator it=index.begin(); it!=index.end(); it++ )
	{
		names.push_back( it->first );
	}
}
