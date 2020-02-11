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

#include "GafferScene/Shader.h"

#include "Gaffer/PlugAlgo.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/Switch.h"
#include "Gaffer/TypedPlug.h"

#include "IECoreScene/ShaderNetwork.h"

#include "IECore/VectorTypedData.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind.hpp"
#include "boost/lexical_cast.hpp"

using namespace std;
using namespace Imath;
using namespace GafferScene;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

bool isOutputParameter( const Gaffer::Plug *parameterPlug )
{
	const Shader *shaderNode = IECore::runTimeCast<const Shader>( parameterPlug->node() );
	if( !shaderNode )
	{
		return false;
	}

	const Plug *shaderNodeOutPlug = shaderNode->outPlug();
	if( !shaderNodeOutPlug )
	{
		return false;
	}

	return parameterPlug == shaderNodeOutPlug || shaderNodeOutPlug->isAncestorOf( parameterPlug );
}

bool isInputParameter( const Gaffer::Plug *parameterPlug )
{
	const Shader *shaderNode = IECore::runTimeCast<const Shader>( parameterPlug->node() );
	if( !shaderNode )
	{
		return false;
	}

	return shaderNode->parametersPlug()->isAncestorOf( parameterPlug );
}

bool isParameter( const Gaffer::Plug *parameterPlug )
{
	return isInputParameter( parameterPlug ) || isOutputParameter( parameterPlug );
}

bool isLeafParameter( const Gaffer::Plug *parameterPlug )
{
	const IECore::TypeId typeId = parameterPlug->typeId();
	if( typeId == Plug::staticTypeId() || typeId == ValuePlug::staticTypeId() )
	{
		if( !parameterPlug->children().empty() )
		{
			return false;
		}
	}
	return true;
}

bool isCompoundNumericPlug( const Gaffer::Plug *plug )
{
	switch( (Gaffer::TypeId)plug->typeId() )
	{
		case V2iPlugTypeId :
		case V2fPlugTypeId :
		case V3iPlugTypeId :
		case V3fPlugTypeId :
		case Color3fPlugTypeId :
		case Color4fPlugTypeId :
			return true;
		default :
			return false;
	}
}

typedef boost::unordered_set<const Shader *> ShaderSet;

struct CycleDetector
{

	CycleDetector( ShaderSet &downstreamShaders, const Shader *shader )
		:	m_downstreamShaders( downstreamShaders ), m_shader( shader )
	{
		if( !m_downstreamShaders.insert( m_shader ).second )
		{
			throw IECore::Exception(
				boost::str(
					boost::format( "Shader \"%s\" is involved in a dependency cycle." ) %
						m_shader->relativeName( m_shader->ancestor<ScriptNode>() )
				)
			);
		}
	}

	~CycleDetector()
	{
		m_downstreamShaders.erase( m_shader );
	}

	private :

		ShaderSet &m_downstreamShaders;
		const Shader *m_shader;

};

IECore::InternedString g_outPlugName( "out" );

} // namespace

//////////////////////////////////////////////////////////////////////////
// Shader::NetworkBuilder implementation
//////////////////////////////////////////////////////////////////////////

class Shader::NetworkBuilder
{

	public :

		NetworkBuilder( const Gaffer::Plug *output )
			:	m_output( output )
		{
		}

		IECore::MurmurHash networkHash()
		{
			if( const Gaffer::Plug *p = effectiveParameter( m_output ) )
			{
				if( isOutputParameter( p ) )
				{
					auto shader = static_cast<const Shader *>( p->node() );
					IECore::MurmurHash result = shaderHash( shader );
					if( p != shader->outPlug() )
					{
						result.append( p->relativeName( shader->outPlug() ) );
					}
					return result;
				}
			}

			return IECore::MurmurHash();
		}

		IECoreScene::ConstShaderNetworkPtr network()
		{
			if( !m_network )
			{
				m_network = new IECoreScene::ShaderNetwork;
				if( const Gaffer::Plug *p = effectiveParameter( m_output ) )
				{
					if( isOutputParameter( p ) )
					{
						auto shader = static_cast<const Shader *>( p->node() );
						const IECore::InternedString outputHandle = handle( shader );
						IECore::InternedString outputName;
						if( p != shader->outPlug() )
						{
							outputName = p->relativeName( shader->outPlug() );
						}
						m_network->setOutput( { outputHandle, outputName } );
					}
				}
			}
			return m_network;
		}

	private :

		// Returns the effective shader parameter that should be used taking into account
		// enabledPlug() and correspondingInput(). Accepts either output or input parameters
		// and may return either an output or input parameter.
		const Gaffer::Plug *effectiveParameter( const Gaffer::Plug *parameterPlug ) const
		{
			while( true )
			{
				if( !parameterPlug )
				{
					return nullptr;
				}

				if( isOutputParameter( parameterPlug ) )
				{
					const Shader *shaderNode = static_cast<const Shader *>( parameterPlug->node() );
					if( shaderNode->enabledPlug()->getValue() )
					{
						return parameterPlug;
					}
					else
					{
						// Follow pass-through, ready for next iteration.
						parameterPlug = shaderNode->correspondingInput( parameterPlug );
					}
				}
				else
				{
					assert( isInputParameter( parameterPlug ) );
					const Gaffer::Plug *source = parameterPlug->source<Gaffer::Plug>();

					if( auto switchNode = IECore::runTimeCast<const Switch>( source->node() ) )
					{
						// Special case for switches with context-varying index values.
						// Query the active input for this context, and manually traverse
						// out the other side.
						if( const Plug *activeInPlug = switchNode->activeInPlug( source ) )
						{
							source = activeInPlug->source();
						}
					}

					if( source == parameterPlug || !isParameter( source ) )
					{
						return parameterPlug;
					}
					else
					{
						// Follow connection, ready for next iteration.
						parameterPlug = source;
					}
				}
			}
		}

		IECore::MurmurHash shaderHash( const Shader *shaderNode )
		{
			assert( shaderNode );
			assert( shaderNode->enabledPlug()->getValue() );

			CycleDetector cycleDetector( m_downstreamShaders, shaderNode );

			HandleAndHash &handleAndHash = m_shaders[shaderNode];
			if( handleAndHash.hash != IECore::MurmurHash() )
			{
				return handleAndHash.hash;
			}

			handleAndHash.hash.append( shaderNode->typeId() );
			shaderNode->namePlug()->hash( handleAndHash.hash );
			shaderNode->typePlug()->hash( handleAndHash.hash );

			shaderNode->nodeNamePlug()->hash( handleAndHash.hash );
			shaderNode->nodeColorPlug()->hash( handleAndHash.hash );

			hashParameterWalk( shaderNode->parametersPlug(), handleAndHash.hash );

			return handleAndHash.hash;
		}

		IECore::InternedString handle( const Shader *shaderNode )
		{
			assert( shaderNode );
			assert( shaderNode->enabledPlug()->getValue() );

			CycleDetector cycleDetector( m_downstreamShaders, shaderNode );

			HandleAndHash &handleAndHash = m_shaders[shaderNode];
			if( !handleAndHash.handle.string().empty() )
			{
				return handleAndHash.handle;
			}

			std::string type = shaderNode->typePlug()->getValue();
			if( shaderNode != m_output->node() && !boost::ends_with( type, "shader" ) )
			{
				// Some renderers (Arnold for one) allow surface shaders to be connected
				// as inputs to other shaders, so we may need to change the shader type to
				// convert it into a standard shader. We must take care to preserve any
				// renderer specific prefix when doing this.
				size_t i = type.find_first_of( ":" );
				if( i != std::string::npos )
				{
					type = type.substr( 0, i + 1 ) + "shader";
				}
				else
				{
					type = "shader";
				}
			}

			IECoreScene::ShaderPtr shader = new IECoreScene::Shader( shaderNode->namePlug()->getValue(), type );

			const std::string nodeName = shaderNode->nodeNamePlug()->getValue();
			shader->blindData()->writable()["gaffer:nodeName"] = new IECore::StringData( nodeName );
			shader->blindData()->writable()["gaffer:nodeColor"] = new IECore::Color3fData( shaderNode->nodeColorPlug()->getValue() );

			vector<IECoreScene::ShaderNetwork::Connection> inputConnections;
			addParameterWalk( shaderNode->parametersPlug(), IECore::InternedString(), shader.get(), inputConnections );

			handleAndHash.handle = m_network->addShader( nodeName, std::move( shader ) );
			for( const auto &c : inputConnections )
			{
				m_network->addConnection( { c.source, { handleAndHash.handle, c.destination.name } } );
			}

			return handleAndHash.handle;
		}

		void hashParameterWalk( const Gaffer::Plug *parameter, IECore::MurmurHash &h )
		{
			if( !isLeafParameter( parameter ) || parameter->parent<Node>() )
			{
				// Compound parameter - recurse
				for( InputPlugIterator it( parameter ); !it.done(); ++it )
				{
					hashParameterWalk( it->get(), h );
				}
			}
			else if( const Gaffer::ArrayPlug *arrayParameter = IECore::runTimeCast<const Gaffer::ArrayPlug>( parameter ) )
			{
				// Array parameter
				for( InputPlugIterator it( arrayParameter ); !it.done(); ++it )
				{
					hashParameter( it->get(), h );
				}
			}
			else
			{
				// Leaf parameter
				hashParameter( parameter, h );
			}
		}

		void addParameterWalk( const Gaffer::Plug *parameter, const IECore::InternedString &parameterName, IECoreScene::Shader *shader, vector<IECoreScene::ShaderNetwork::Connection> &connections )
		{
			if( !isLeafParameter( parameter ) || parameter->parent<Node>() )
			{
				// Compound parameter - recurse
				for( InputPlugIterator it( parameter ); !it.done(); ++it )
				{
					IECore::InternedString childParameterName;
					if( parameterName.string().size() )
					{
						childParameterName = parameterName.string() + "." + (*it)->getName().string();
					}
					else
					{
						childParameterName = (*it)->getName();
					}

					addParameterWalk( it->get(), childParameterName, shader, connections );
				}
			}
			else if( const Gaffer::ArrayPlug *array = IECore::runTimeCast<const Gaffer::ArrayPlug>( parameter ) )
			{
				int i = 0;
				for( InputPlugIterator it( array ); !it.done(); ++it, ++i )
				{
					IECore::InternedString childParameterName = parameterName.string() + "[" + std::to_string( i ) + "]";
					addParameter( it->get(), childParameterName, shader, connections );
				}
			}
			else
			{
				addParameter( parameter, parameterName, shader, connections );
			}
		}

		void hashParameter( const Gaffer::Plug *parameter, IECore::MurmurHash &h )
		{
			const Gaffer::Plug *effectiveParameter = this->effectiveParameter( parameter );
			if( !effectiveParameter )
			{
				return;
			}

			const Shader *effectiveShader = static_cast<const Shader *>( effectiveParameter->node() );
			if( isInputParameter( effectiveParameter ) )
			{
				effectiveShader->parameterHash( effectiveParameter, h );
				hashParameterComponentConnections( parameter, h );
			}
			else
			{
				assert( isOutputParameter( effectiveParameter ) );
				h.append( shaderHash( effectiveShader ) );
				if( effectiveShader->outPlug()->isAncestorOf( effectiveParameter ) )
				{
					h.append( effectiveParameter->relativeName( effectiveShader->outPlug() ) );
				}
				return;
			}
		}

		void addParameter( const Gaffer::Plug *parameter, const IECore::InternedString &parameterName, IECoreScene::Shader *shader, vector<IECoreScene::ShaderNetwork::Connection> &connections )
		{
			const Gaffer::Plug *effectiveParameter = this->effectiveParameter( parameter );
			if( !effectiveParameter )
			{
				return;
			}

			const Shader *effectiveShader = static_cast<const Shader *>( effectiveParameter->node() );
			if( isInputParameter( effectiveParameter ) )
			{
				if( IECore::DataPtr value = effectiveShader->parameterValue( effectiveParameter ) )
				{
					shader->parameters()[parameterName] = value;
				}
				addParameterComponentConnections( parameter, parameterName, connections );
			}
			else
			{
				IECore::InternedString outputName;
				if( effectiveShader->outPlug()->isAncestorOf( effectiveParameter ) )
				{
					outputName = effectiveParameter->relativeName( effectiveShader->outPlug() );
				}
				connections.push_back( {
					{ this->handle( effectiveShader ), outputName },
					{ IECore::InternedString(), parameterName }
				} );
			}
		}

		void hashParameterComponentConnections( const Gaffer::Plug *parameter, IECore::MurmurHash &h )
		{
			if( !isCompoundNumericPlug( parameter ) )
			{
				return;
			}
			for( InputPlugIterator it( parameter ); !it.done(); ++it )
			{
				const Gaffer::Plug *effectiveParameter = this->effectiveParameter( it->get() );
				if( effectiveParameter && isOutputParameter( effectiveParameter ) )
				{
					const Shader *effectiveShader = static_cast<const Shader *>( effectiveParameter->node() );
					h.append( shaderHash( effectiveShader ) );
					if( effectiveShader->outPlug()->isAncestorOf( effectiveParameter ) )
					{
						h.append( effectiveParameter->relativeName( effectiveShader->outPlug() ) );
					}
					h.append( (*it)->getName() );
				}
			}
		}

		void addParameterComponentConnections( const Gaffer::Plug *parameter, const IECore::InternedString &parameterName, vector<IECoreScene::ShaderNetwork::Connection> &connections )
		{
			if( !isCompoundNumericPlug( parameter ) )
			{
				return;
			}
			for( InputPlugIterator it( parameter ); !it.done(); ++it )
			{
				const Gaffer::Plug *effectiveParameter = this->effectiveParameter( it->get() );
				if( effectiveParameter && isOutputParameter( effectiveParameter ) )
				{
					const Shader *effectiveShader = static_cast<const Shader *>( effectiveParameter->node() );
					IECore::InternedString outputName;
					if( effectiveShader->outPlug()->isAncestorOf( effectiveParameter ) )
					{
						outputName = effectiveParameter->relativeName( effectiveShader->outPlug() );
					}
					IECore::InternedString inputName = parameterName.string() + "." + (*it)->getName().string();
					connections.push_back( {
						{ this->handle( effectiveShader ), outputName },
						{ IECore::InternedString(), inputName }
					} );
				}
			}
		}

		const Plug *m_output;
		IECoreScene::ShaderNetworkPtr m_network;

		struct HandleAndHash
		{
			IECore::InternedString handle;
			IECore::MurmurHash hash;
		};

		typedef std::map<const Shader *, HandleAndHash> ShaderMap;
		ShaderMap m_shaders;

		ShaderSet m_downstreamShaders; // Used for detecting cycles

};

//////////////////////////////////////////////////////////////////////////
// Shader implementation
//////////////////////////////////////////////////////////////////////////

static IECore::InternedString g_nodeColorMetadataName( "nodeGadget:color" );

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Shader );

size_t Shader::g_firstPlugIndex = 0;
const IECore::InternedString Shader::g_outputParameterContextName( "scene:shader:outputParameter" );

Shader::Shader( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "name", Gaffer::Plug::In, "", Plug::Default & ~Plug::Serialisable ) );
	addChild( new StringPlug( "type", Gaffer::Plug::In, "", Plug::Default & ~Plug::Serialisable ) );
	addChild( new StringPlug( "attributeSuffix", Gaffer::Plug::In, "" ) );
	addChild( new Plug( "parameters", Plug::In, Plug::Default & ~Plug::AcceptsInputs ) );
	addChild( new BoolPlug( "enabled", Gaffer::Plug::In, true ) );
	addChild( new StringPlug( "__nodeName", Gaffer::Plug::In, name, Plug::Default & ~(Plug::Serialisable | Plug::AcceptsInputs), IECore::StringAlgo::NoSubstitutions ) );
	addChild( new Color3fPlug( "__nodeColor", Gaffer::Plug::In, Color3f( 0.0f ) ) );
	nodeColorPlug()->setFlags( Plug::Serialisable | Plug::AcceptsInputs, false );
	addChild( new CompoundObjectPlug( "__outAttributes", Plug::Out, new IECore::CompoundObject ) );

	nameChangedSignal().connect( boost::bind( &Shader::nameChanged, this ) );
	Metadata::nodeValueChangedSignal().connect( boost::bind( &Shader::nodeMetadataChanged, this, ::_1, ::_2, ::_3 ) );
}

Shader::~Shader()
{
}

Gaffer::StringPlug *Shader::namePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Shader::namePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *Shader::typePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *Shader::typePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *Shader::attributeSuffixPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *Shader::attributeSuffixPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::Plug *Shader::parametersPlug()
{
	return getChild<Plug>( g_firstPlugIndex + 3 );
}

const Gaffer::Plug *Shader::parametersPlug() const
{
	return getChild<Plug>( g_firstPlugIndex + 3 );
}

Gaffer::Plug *Shader::outPlug()
{
	// not getting by index, because it is created by the
	// derived classes in loadShader().
	return getChild<Plug>( g_outPlugName );
}

const Gaffer::Plug *Shader::outPlug() const
{
	return getChild<Plug>( g_outPlugName );
}

Gaffer::BoolPlug *Shader::enabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::BoolPlug *Shader::enabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

Gaffer::StringPlug *Shader::nodeNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::StringPlug *Shader::nodeNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

Gaffer::Color3fPlug *Shader::nodeColorPlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::Color3fPlug *Shader::nodeColorPlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 6 );
}

Gaffer::CompoundObjectPlug *Shader::outAttributesPlug()
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::CompoundObjectPlug *Shader::outAttributesPlug() const
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 7 );
}

IECore::MurmurHash Shader::attributesHash() const
{
	return outAttributesPlug()->hash();
}

void Shader::attributesHash( IECore::MurmurHash &h ) const
{
	outAttributesPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr Shader::attributes() const
{
	return outAttributesPlug()->getValue();
}

void Shader::attributesHash( const Gaffer::Plug *output, IECore::MurmurHash &h ) const
{
	attributeSuffixPlug()->hash( h );

	NetworkBuilder networkBuilder( output );
	h.append( networkBuilder.networkHash() );
}

IECore::ConstCompoundObjectPtr Shader::attributes( const Gaffer::Plug *output ) const
{
	IECore::CompoundObjectPtr result = new IECore::CompoundObject;
	NetworkBuilder networkBuilder( output );
	if( networkBuilder.network()->size() )
	{
		std::string attr = typePlug()->getValue();
		std::string postfix = attributeSuffixPlug()->getValue();
		if( postfix != "" )
		{
			attr += ":" + postfix;
		}
		result->members()[attr] = boost::const_pointer_cast<IECoreScene::ShaderNetwork>( networkBuilder.network() );
	}
	return result;
}

void Shader::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if(
		parametersPlug()->isAncestorOf( input ) ||
		input == enabledPlug() ||
		input == nodeNamePlug() ||
		input == namePlug() ||
		input == typePlug() ||
		input->parent<Plug>() == nodeColorPlug()
	)
	{
		if( const Plug *out = outPlug() )
		{
			if( !out->children().empty() )
			{
				for( RecursivePlugIterator it( out ); !it.done(); it++ )
				{
					if( (*it)->children().empty() )
					{
						outputs.push_back( it->get() );
					}
				}
			}
			else
			{
				outputs.push_back( out );
			}
		}
		outputs.push_back( outAttributesPlug() );
	}
}

void Shader::loadShader( const std::string &shaderName, bool keepExistingValues )
{
	// A base shader doesn't know anything about what sort of parameters you might want to load.
	//
	// The only reason why this isn't pure virtual is because it is occasionally useful to
	// manually create a shader type which doesn't actually correspond to any real shader on disk.
	// IERendering using this to create a generic mesh light shader which is later translated into
	// the correct shader type for whichever renderer you are using.  Similarly, ArnoldDisplacement
	// doesn't need a loadShader override because it's not really a shader.
}

void Shader::reloadShader()
{
	// Sub-classes should take care of any necessary cache clearing before calling this

	loadShader( namePlug()->getValue(), true );
}

void Shader::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == outAttributesPlug() )
	{
		ComputeNode::hash( output, context, h );
		const Plug *outputParameter = outPlug();
		if( auto *name = context->get<IECore::StringData>( g_outputParameterContextName, nullptr ) )
		{
			outputParameter = outputParameter->descendant<Plug>( name->readable() );
		}
		attributesHash( outputParameter, h );
		return;
	}
	else if( const Plug *o = outPlug() )
	{
		if( output == o || o->isAncestorOf( output ) )
		{
			ComputeNode::hash( output, context, h );
			namePlug()->hash( h );
			typePlug()->hash( h );
			return;
		}
	}

	ComputeNode::hash( output, context, h );
}

void Shader::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == outAttributesPlug() )
	{
		const Plug *outputParameter = outPlug();
		if( auto *name = context->get<IECore::StringData>( g_outputParameterContextName, nullptr ) )
		{
			outputParameter = outputParameter->descendant<Plug>( name->readable() );
		}
		static_cast<CompoundObjectPlug *>( output )->setValue( attributes( outputParameter ) );
		return;
	}
	else if( const Plug *o = outPlug() )
	{
		if( output == o || o->isAncestorOf( output ) )
		{
			output->setToDefault();
			return;
		}
	}

	ComputeNode::compute( output, context );
}

void Shader::parameterHash( const Gaffer::Plug *parameterPlug, IECore::MurmurHash &h ) const
{
	const ValuePlug *vplug = IECore::runTimeCast<const ValuePlug>( parameterPlug );
	if( vplug )
	{
		vplug->hash( h );
	}
	else
	{
		h.append( parameterPlug->typeId() );
	}
}

IECore::DataPtr Shader::parameterValue( const Gaffer::Plug *parameterPlug ) const
{
	if( const Gaffer::ValuePlug *valuePlug = IECore::runTimeCast<const Gaffer::ValuePlug>( parameterPlug ) )
	{
		return Gaffer::PlugAlgo::extractDataFromPlug( valuePlug );
	}

	return nullptr;
}

void Shader::nameChanged()
{
	nodeNamePlug()->setValue( getName() );
}

void Shader::nodeMetadataChanged( IECore::TypeId nodeTypeId, IECore::InternedString key, const Gaffer::Node *node )
{
	if( node && node != this )
	{
		return;
	}

	if( key == g_nodeColorMetadataName && this->isInstanceOf( nodeTypeId ) )
	{
		IECore::ConstColor3fDataPtr d = Metadata::value<const IECore::Color3fData>( this, g_nodeColorMetadataName );
		nodeColorPlug()->setValue( d ? d->readable() : Color3f( 0.0f ) );
	}
}
