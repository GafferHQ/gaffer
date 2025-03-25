//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/ShuffleRenderPasses.h"

#include "Gaffer/ContextAlgo.h"

#include "IECore/NullObject.h"

#include <memory>

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace std;

namespace
{

struct MappingData : public IECore::Data
{

	MappingData( const StringVectorData *renderPassNames, const ShufflesPlug *shuffles )
	{
		if( !renderPassNames )
		{
			return;
		}

		unordered_map<string, size_t> indexMap;
		const auto &names = renderPassNames->readable();
		for( size_t i = 0; i < names.size(); ++i )
		{
			m_mapping.insert( { names[i], names[i] } );
			indexMap.insert( { names[i], i } );
		}

		m_mapping = shuffles->shuffle( m_mapping );

		// Sort shuffled names to preserve the original order of each
		// source name. We do this to maintain the input order, preserving
		// the position of renamed render passes while newly copied
		// render passes are sorted immediately after their source.
		vector< tuple<size_t, bool, string> > shuffledNames;
		shuffledNames.reserve( m_mapping.size() );
		for( const auto &[destination, source] : m_mapping )
		{
			shuffledNames.push_back( { indexMap[source], destination != source, destination } );
		}
		std::sort( shuffledNames.begin(), shuffledNames.end() );

		vector<string> orderedNames;
		orderedNames.reserve( m_mapping.size() );
		for( const auto &n : shuffledNames )
		{
			orderedNames.push_back( get<2>( n ) );
		}

		m_outRenderPassNames = new StringVectorData( orderedNames );
	}

	const StringVectorData *outRenderPassNames() const { return m_outRenderPassNames.get(); }

	const string sourceRenderPassName( const string &renderPassName ) const
	{
		auto it = m_mapping.find( renderPassName );
		if( it == m_mapping.end() )
		{
			return renderPassName;
		}
		return it->second;
	}

	private :

		StringVectorDataPtr m_outRenderPassNames;

		using Map = unordered_map<string, string>;
		Map m_mapping;

};

IE_CORE_DECLAREPTR( MappingData )

bool enabled( const BoolPlug *enabledPlug, const Gaffer::Context *context )
{
	const BoolPlug *sourcePlug = enabledPlug->source<BoolPlug>();
	if( !sourcePlug || sourcePlug->direction() == Plug::Out )
	{
		ScenePlug::GlobalScope globalScope( context );
		return sourcePlug ? sourcePlug->getValue() : enabledPlug->getValue();
	}
	else
	{
		// Value is not computed so context is irrelevant.
		// Avoid overhead of context creation.
		return sourcePlug->getValue();
	}
}

} // namespace

class ShuffleRenderPasses::ProcessedScope : public Context::EditableScope
{

	public :

		ProcessedScope( const Context *context, const ShuffleRenderPasses *processor )
			:	EditableScope( context )
		{
			ContextAlgo::GlobalScope globalScope( context, processor->inPlug() );
			if( processor->enabledPlug()->getValue() )
			{
				processor->processContext( *this, m_storage );
			}
		}

	private :

		IECore::ConstRefCountedPtr m_storage;

};

GAFFER_NODE_DEFINE_TYPE( ShuffleRenderPasses );

const InternedString g_inPlugName( "in" );
const InternedString g_outPlugName( "out" );
const std::string g_renderPassNamesOptionName = "option:renderPass:names";
const std::string g_renderPassContextName = "renderPass";

size_t ShuffleRenderPasses::g_firstPlugIndex = 0;

ShuffleRenderPasses::ShuffleRenderPasses( const std::string &name )
	:	ContextProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ShufflesPlug( "shuffles" ) );
	addChild( new StringPlug( "__sourceName", Plug::Out, "" ) );
	addChild( new ObjectPlug( "__mapping", Plug::Out, IECore::NullObject::defaultNullObject() ) );

	setup( new ScenePlug() );
}

ShuffleRenderPasses::~ShuffleRenderPasses()
{
}

GafferScene::ScenePlug *ShuffleRenderPasses::inPlug()
{
	return static_cast<ScenePlug *>( getChild<Plug>( g_inPlugName ) );
}

const GafferScene::ScenePlug *ShuffleRenderPasses::inPlug() const
{
	return static_cast<const ScenePlug *>( getChild<Plug>( g_inPlugName ) );
}

GafferScene::ScenePlug *ShuffleRenderPasses::outPlug()
{
	return static_cast<ScenePlug *>( getChild<Plug>( g_outPlugName ) );
}

const GafferScene::ScenePlug *ShuffleRenderPasses::outPlug() const
{
	return static_cast<const ScenePlug *>( getChild<Plug>( g_outPlugName ) );
}

Gaffer::ShufflesPlug *ShuffleRenderPasses::shufflesPlug()
{
	return getChild<Gaffer::ShufflesPlug>( g_firstPlugIndex );
}

const Gaffer::ShufflesPlug *ShuffleRenderPasses::shufflesPlug() const
{
	return getChild<Gaffer::ShufflesPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *ShuffleRenderPasses::sourceNamePlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *ShuffleRenderPasses::sourceNamePlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::ObjectPlug *ShuffleRenderPasses::mappingPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::ObjectPlug *ShuffleRenderPasses::mappingPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 2 );
}

void ShuffleRenderPasses::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ContextProcessor::affects( input, outputs );

	if( shufflesPlug()->isAncestorOf( input ) || input == inPlug()->globalsPlug() )
	{
		outputs.push_back( mappingPlug() );
	}

	if( input == mappingPlug() )
	{
		outputs.push_back( sourceNamePlug() );
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void ShuffleRenderPasses::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	if( output == mappingPlug() )
	{
		ComputeNode::hash( output, context, h );
		inPlug()->globalsPlug()->hash( h );
		shufflesPlug()->hash( h );
		return;
	}
	else if( output == sourceNamePlug() )
	{
		ComputeNode::hash( output, context, h );
		h.append( context->get<string>( g_renderPassContextName, "" ) );
		mappingPlug()->hash( h );
		return;
	}
	else if( output == outPlug()->globalsPlug() && enabled( enabledPlug(), context ) )
	{
		hashGlobals( context, outPlug(), h );
		return;
	}

	ContextProcessor::hash( output, context, h );
}

void ShuffleRenderPasses::compute( ValuePlug *output, const Context *context ) const
{
	if( output == mappingPlug() )
	{
		ConstCompoundObjectPtr globals = inPlug()->globals();
		static_cast<ObjectPlug *>( output )->setValue(
			new MappingData( globals->member<IECore::StringVectorData>( g_renderPassNamesOptionName ), shufflesPlug() )
		);
		return;
	}
	else if( output == sourceNamePlug() )
	{
		auto mapping = boost::static_pointer_cast<const MappingData>( mappingPlug()->getValue() );
		static_cast<StringPlug *>( output )->setValue(
			mapping->sourceRenderPassName( context->get<string>( g_renderPassContextName, "" ) )
		);
		return;
	}
	else if( output == outPlug()->globalsPlug() && enabled( enabledPlug(), context ) )
	{
		static_cast<CompoundObjectPlug *>( output )->setValue(
			computeGlobals( context, outPlug() )
		);
		return;
	}

	ContextProcessor::compute( output, context );
}

bool ShuffleRenderPasses::affectsContext( const Gaffer::Plug *input ) const
{
	return input == sourceNamePlug();
}

void ShuffleRenderPasses::processContext( Gaffer::Context::EditableScope &context, IECore::ConstRefCountedPtr &storage ) const
{
	const auto currentRenderPass = context.context()->get<string>( g_renderPassContextName, "" );
	if( currentRenderPass != "" )
	{
		const auto sourceName = sourceNamePlug()->getValue();
		if( sourceName != currentRenderPass )
		{
			IECore::StringDataPtr nameStorage = new IECore::StringData( sourceName );
			context.set( g_renderPassContextName, &nameStorage->readable() );
			storage = std::move( nameStorage );
		}
	}
}

void ShuffleRenderPasses::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( outPlug()->globalsPlug(), context, h );
	ProcessedScope processedScope( context, this );
	inPlug()->globalsPlug()->hash( h );
	shufflesPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr ShuffleRenderPasses::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ProcessedScope processedScope( context, this );
	IECore::ConstCompoundObjectPtr inputGlobals = inPlug()->globalsPlug()->getValue();
	if( shufflesPlug()->children().empty() || inputGlobals->members().empty() || !inputGlobals->members().count( g_renderPassNamesOptionName ) )
	{
		return inputGlobals;
	}

	IECore::CompoundObjectPtr result = new IECore::CompoundObject;
	result->members() = inputGlobals->members();

	auto mapping = boost::static_pointer_cast<const MappingData>( mappingPlug()->getValue() );
	result->members()[g_renderPassNamesOptionName] = const_cast<IECore::StringVectorData *>( mapping->outRenderPassNames() );

	return result;
}
