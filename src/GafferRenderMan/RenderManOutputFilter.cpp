//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Alex Fuller. All rights reserved.
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.

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

#include "GafferRenderMan/RenderManOutputFilter.h"

#include "GafferScene/Shader.h"
#include "GafferScene/ShaderPlug.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/ShaderNetwork.h"
#include "IECoreScene/ShaderNetworkAlgo.h"

#include <regex>

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferRenderMan;

namespace
{

const std::array<std::string, 2> g_shaderPlugNames = { "displayFilter", "sampleFilter" };
const std::array<InternedString, 2> g_options = { "option:ri:displayfilter", "option:ri:samplefilter" };
const std::array<InternedString, 2> g_shaderTypes = { "ri:displayfilter", "ri:samplefilter" };
const std::array<std::string, 2> g_combinerShaders = { "PxrDisplayFilterCombiner", "PxrSampleFilterCombiner" };

const InternedString g_out( "out" );
const InternedString g_filter0( "filter[0]" );

const std::regex g_filterIndexRegex( R"(filter\[([0-9]+)\])" );
int connectionIndex( const ShaderNetwork::Connection &connection )
{
	std::smatch filterIndexMatch;
	if( std::regex_match( connection.destination.name.string(), filterIndexMatch, g_filterIndexRegex ) )
	{
		return std::stoi( filterIndexMatch.str( 1 ) );
	}
	return -1;
}

} // namespace

GAFFER_NODE_DEFINE_TYPE( RenderManOutputFilter );

size_t RenderManOutputFilter::g_firstPlugIndex = 0;

RenderManOutputFilter::RenderManOutputFilter( const std::string &name, FilterType filterType )
	:	GlobalsProcessor( name ), m_filterType( filterType )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ShaderPlug( g_shaderPlugNames[(int)filterType] ) );
	addChild( new IntPlug( "mode", Plug::In, (int)Mode::Replace, (int)Mode::Replace, (int)Mode::InsertLast ) );
}

RenderManOutputFilter::~RenderManOutputFilter()
{
}

GafferScene::ShaderPlug *RenderManOutputFilter::shaderPlug()
{
	return getChild<ShaderPlug>( g_firstPlugIndex );
}

const GafferScene::ShaderPlug *RenderManOutputFilter::shaderPlug() const
{
	return getChild<ShaderPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *RenderManOutputFilter::modePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *RenderManOutputFilter::modePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

bool RenderManOutputFilter::acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const
{
	if( !GlobalsProcessor::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}

	if( plug != shaderPlug() )
	{
		return true;
	}

	if( !inputPlug )
	{
		return true;
	}

	const Plug *sourcePlug = inputPlug->source();
	auto *sourceShader = runTimeCast<const GafferScene::Shader>( sourcePlug->node() );
	if( !sourceShader )
	{
		return true;
	}

	const Plug *sourceShaderOutPlug = sourceShader->outPlug();
	if( !sourceShaderOutPlug )
	{
		return true;
	}

	if( sourcePlug != sourceShaderOutPlug && !sourceShaderOutPlug->isAncestorOf( sourcePlug ) )
	{
		return true;
	}

	return sourceShader->typePlug()->getValue() == g_shaderTypes[(int)m_filterType].string();
}

void RenderManOutputFilter::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	GlobalsProcessor::affects( input, outputs );

	if( input == shaderPlug() || input == modePlug() )
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void RenderManOutputFilter::hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h.append( shaderPlug()->attributesHash() );
	modePlug()->hash( h );
}

IECore::ConstCompoundObjectPtr RenderManOutputFilter::computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const
{
	ConstCompoundObjectPtr attributes = shaderPlug()->attributes();
	if( attributes->members().empty() )
	{
		return inputGlobals;
	}

	const InternedString shaderType = g_shaderTypes[(int)m_filterType];
	const IECoreScene::ShaderNetwork *network = attributes->member<IECoreScene::ShaderNetwork>( shaderType );
	if( !network )
	{
		throw IECore::Exception( fmt::format( "Shader of type \"{}\" not found", shaderType.string() ) );
	}

	CompoundObjectPtr result = new CompoundObject;
	// Since we're not going to modify any existing members (only add new ones),
	// and our result becomes const on returning it, we can directly reference
	// the input members in our result without copying. Be careful not to modify
	// them though!
	result->members() = inputGlobals->members();

	const Mode mode = (Mode)modePlug()->getValue();
	const ShaderNetwork *inputNetwork = inputGlobals->member<ShaderNetwork>( g_options[(int)m_filterType] );

	ConstShaderNetworkPtr outputNetwork;
	if( !inputNetwork || mode == Mode::Replace )
	{
		outputNetwork = network;
	}
	else
	{
		// Copy network, and make sure we have a combiner shader
		ShaderNetworkPtr combinedNetwork = inputNetwork->copy();
		InternedString combinerHandle;
		if( combinedNetwork->outputShader()->getName() == g_combinerShaders[(int)m_filterType] )
		{
			combinerHandle = combinedNetwork->getOutput().shader;
		}
		else
		{
			// Insert combiner shader.
			IECoreScene::ShaderPtr combinerShader = new IECoreScene::Shader( g_combinerShaders[(int)m_filterType], g_shaderTypes[(int)m_filterType] );
			combinerHandle = combinedNetwork->addShader( combinerShader->getName(), std::move( combinerShader ) );
			combinedNetwork->addConnection( { combinedNetwork->getOutput(), { combinerHandle, g_filter0 } } );
			combinedNetwork->setOutput( { combinerHandle, g_out } );
		}

		// Insert new shader, and connect it to the combiner appropriately.
		ShaderNetwork::Parameter insertedOut = ShaderNetworkAlgo::addShaders( combinedNetwork.get(), network );
		ShaderNetwork::ConnectionRange connectionRange = combinedNetwork->inputConnections( combinedNetwork->getOutput().shader );

		if( mode == Mode::InsertLast )
		{
			int lastIndex = -1;
			for( const auto &connection : connectionRange )
			{
				lastIndex = std::max( lastIndex, connectionIndex( connection ) );
			}
			combinedNetwork->addConnection( { insertedOut, { combinerHandle, fmt::format( "filter[{}]", lastIndex + 1 ) } } );
		}
		else
		{
			assert( mode == Mode::InsertFirst );
			// Remove old connections.
			const std::vector<ShaderNetwork::Connection> connections( connectionRange.begin(), connectionRange.end() );
			for( const auto &c : connections )
			{
				if( connectionIndex( c ) != -1 )
				{
					combinedNetwork->removeConnection( c );
				}
			}
			// Insert new connection at front.
			combinedNetwork->addConnection( { insertedOut, { combinerHandle, g_filter0 } } );
			// Add old connections back again, with their indices incremented.
			for( const auto &c : connections )
			{
				const int i = connectionIndex( c );
				if( i != -1 )
				{
					combinedNetwork->addConnection( { c.source, { combinerHandle, fmt::format( "filter[{}]", i + 1 ) } } );
				}
			}
		}

		outputNetwork = combinedNetwork;
	}

	result->members()[g_options[(int)m_filterType]] = boost::const_pointer_cast<ShaderNetwork>( outputNetwork );
	return result;
}
