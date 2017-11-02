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

#include "boost/algorithm/string/predicate.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/bind.hpp"

#include "IECore/VectorTypedData.h"

#include "Gaffer/TypedPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/CompoundDataPlug.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Switch.h"

#include "GafferScene/Shader.h"

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

} // namespace

//////////////////////////////////////////////////////////////////////////
// Shader::NetworkBuilder implementation
//////////////////////////////////////////////////////////////////////////

class Shader::NetworkBuilder
{

	public :

		NetworkBuilder( const Gaffer::Plug *output )
			:	m_output( output ), m_handleCount( 0 )
		{
		}

		IECore::MurmurHash stateHash()
		{
			if( const Gaffer::Plug *p = effectiveParameter( m_output ) )
			{
				if( isOutputParameter( p ) )
				{
					return shaderHash( static_cast<const Shader *>( p->node() ) );
				}
			}

			return IECore::MurmurHash();
		}

		IECore::ConstObjectVectorPtr state()
		{
			if( !m_state )
			{
				m_state = new IECore::ObjectVector;
				if( const Gaffer::Plug *p = effectiveParameter( m_output ) )
				{
					if( isOutputParameter( p ) )
					{
						shader( static_cast<const Shader *>( p->node() ) );
					}
				}
			}
			return m_state;
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

					if( const SwitchComputeNode *switchNode = source->parent<SwitchComputeNode>() )
					{
						// Special case for switches with context-varying index values.
						// Query the active input for this context, and manually traverse
						// out the other side.
						if( const Plug *activeInPlug = switchNode->activeInPlug() )
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

			ShaderAndHash &shaderAndHash = m_shaders[shaderNode];
			if( shaderAndHash.hash != IECore::MurmurHash() )
			{
				return shaderAndHash.hash;
			}

			shaderAndHash.hash.append( shaderNode->typeId() );
			shaderNode->namePlug()->hash( shaderAndHash.hash );
			shaderNode->typePlug()->hash( shaderAndHash.hash );

			parameterHashWalk( shaderNode->parametersPlug(), shaderAndHash.hash );

			shaderNode->nodeNamePlug()->hash( shaderAndHash.hash );
			shaderNode->nodeColorPlug()->hash( shaderAndHash.hash );

			return shaderAndHash.hash;
		}

		IECore::Shader *shader( const Shader *shaderNode )
		{
			assert( shaderNode );
			assert( shaderNode->enabledPlug()->getValue() );

			CycleDetector cycleDetector( m_downstreamShaders, shaderNode );

			ShaderAndHash &shaderAndHash = m_shaders[shaderNode];
			if( shaderAndHash.shader )
			{
				return shaderAndHash.shader.get();
			}

			shaderAndHash.shader = new IECore::Shader( shaderNode->namePlug()->getValue(), shaderNode->typePlug()->getValue() );
			parameterValueWalk( shaderNode->parametersPlug(), IECore::InternedString(), shaderAndHash.shader->parameters() );

			shaderAndHash.shader->blindData()->writable()["gaffer:nodeName"] = new IECore::StringData( shaderNode->nodeNamePlug()->getValue() );
			shaderAndHash.shader->blindData()->writable()["gaffer:nodeColor"] = new IECore::Color3fData( shaderNode->nodeColorPlug()->getValue() );

			m_state->members().push_back( shaderAndHash.shader );

			return shaderAndHash.shader.get();
		}

		const std::string &shaderHandle( const Shader *shaderNode )
		{
			IECore::Shader *s = shader( shaderNode );
			if( !s )
			{
				static std::string emptyString;
				return emptyString;
			}

			IECore::StringDataPtr handleData = s->parametersData()->member<IECore::StringData>( "__handle" );
			if( !handleData )
			{
				// Some renderers (Arnold for one) allow surface shaders to be connected
				// as inputs to other shaders, so we may need to change the shader type to
				// convert it into a standard shader. We must take care to preserve any
				// renderer specific prefix when doing this.
				const std::string &type = s->getType();
				if( !boost::ends_with( type, "shader" ) )
				{
					size_t i = type.find_first_of( ":" );
					if( i != std::string::npos )
					{
						s->setType( type.substr( 0, i + 1 ) + "shader" );
					}
					else
					{
						s->setType( "shader" );
					}
				}
				// the handle includes the node name so as to help with debugging, but also
				// includes an integer unique to this shader group, as two shaders could have
				// the same name if they don't have the same parent - because one is inside a
				// Box for instance.
				handleData = new IECore::StringData(
					 boost::lexical_cast<std::string>( ++m_handleCount ) + "_" +
					 s->blindData()->member<IECore::StringData>( "gaffer:nodeName" )->readable()
				);
				s->parameters()["__handle"] = handleData;
			}
			return handleData->readable();
		}

		std::string link( const Shader *shaderNode, const Gaffer::Plug *outputParameter )
		{
			std::string result = this->shaderHandle( shaderNode );
			if( shaderNode->outPlug()->isAncestorOf( outputParameter ) )
			{
				result += "." + outputParameter->relativeName( shaderNode->outPlug() );
			}
			result = "link:" + result;
			return result;
		}

		void parameterHashWalk( const Gaffer::Plug *parameter, IECore::MurmurHash &h )
		{
			if( !isLeafParameter( parameter ) || parameter->parent<Node>() )
			{
				// Compound parameter - recurse
				for( InputPlugIterator it( parameter ); !it.done(); ++it )
				{
					parameterHashWalk( it->get(), h );
				}
			}
			else if( const Gaffer::ArrayPlug *arrayParameter = IECore::runTimeCast<const Gaffer::ArrayPlug>( parameter ) )
			{
				// Array parameter
				arrayParameterHash( arrayParameter, h );
			}
			else
			{
				// Leaf parameter
				parameterHash( parameter, h );
			}
		}

		void parameterValueWalk( const Gaffer::Plug *parameter, const IECore::InternedString &parameterName, IECore::CompoundDataMap &values )
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

					parameterValueWalk( it->get(), childParameterName, values );
				}
			}
			else if( const Gaffer::ArrayPlug *arrayParameter = IECore::runTimeCast<const Gaffer::ArrayPlug>( parameter ) )
			{
				// Array parameter
				if( IECore::DataPtr value = arrayParameterValue( arrayParameter ) )
				{
					values[parameterName] = value;
				}
			}
			else
			{
				// Leaf parameter
				if( IECore::DataPtr value = parameterValue( parameter ) )
				{
					values[parameterName] = value;
				}
			}
		}

		void parameterHash( const Gaffer::Plug *parameter, IECore::MurmurHash &h )
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

		IECore::DataPtr parameterValue( const Gaffer::Plug *parameter )
		{
			const Gaffer::Plug *effectiveParameter = this->effectiveParameter( parameter );
			if( !effectiveParameter )
			{
				return nullptr;
			}

			const Shader *effectiveShader = static_cast<const Shader *>( effectiveParameter->node() );
			if( isInputParameter( effectiveParameter ) )
			{
				return effectiveShader->parameterValue( effectiveParameter );
			}
			else
			{
				assert( isOutputParameter( effectiveParameter ) );
				return new IECore::StringData( link( effectiveShader, effectiveParameter ) );
			}
		}

		void arrayParameterHash( const Gaffer::ArrayPlug *parameter, IECore::MurmurHash &h )
		{
			for( InputPlugIterator it( parameter ); !it.done(); ++it )
			{
				parameterHash( it->get(), h );
			}
		}

		IECore::DataPtr arrayParameterValue( const Gaffer::ArrayPlug *parameter )
		{
			/// \todo We're just supporting arrays of connections - support arrays of values too.
			IECore::StringVectorDataPtr resultData = new IECore::StringVectorData;
			std::vector<std::string> &result = resultData->writable();
			for( InputPlugIterator it( parameter ); !it.done(); ++it )
			{
				const Gaffer::Plug *effectiveParameter = this->effectiveParameter( it->get() );
				if( effectiveParameter && isOutputParameter( effectiveParameter ) )
				{
					const Shader *effectiveShader = static_cast<const Shader *>( effectiveParameter->node() );
					result.push_back( link( effectiveShader, effectiveParameter ) );
				}
				else
				{
					result.push_back( "" );
				}
			}

			return resultData;
		}

		const Plug *m_output;
		IECore::ObjectVectorPtr m_state;

		struct ShaderAndHash
		{
			IECore::ShaderPtr shader;
			IECore::MurmurHash hash;
		};

		typedef std::map<const Shader *, ShaderAndHash> ShaderMap;
		ShaderMap m_shaders;

		ShaderSet m_downstreamShaders; // Used for detecting cycles

		unsigned int m_handleCount;

};

//////////////////////////////////////////////////////////////////////////
// Shader implementation
//////////////////////////////////////////////////////////////////////////

static IECore::InternedString g_nodeColorMetadataName( "nodeGadget:color" );

IE_CORE_DEFINERUNTIMETYPED( Shader );

size_t Shader::g_firstPlugIndex = 0;

Shader::Shader( const std::string &name )
	:	DependencyNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "name" ) );
	addChild( new StringPlug( "type" ) );
	addChild( new StringPlug( "attributeSuffix", Gaffer::Plug::In, "" ) );
	addChild( new Plug( "parameters", Plug::In, Plug::Default & ~Plug::AcceptsInputs ) );
	addChild( new BoolPlug( "enabled", Gaffer::Plug::In, true ) );
	addChild( new StringPlug( "__nodeName", Gaffer::Plug::In, name, Plug::Default & ~(Plug::Serialisable | Plug::AcceptsInputs), Context::NoSubstitutions ) );
	addChild( new Color3fPlug( "__nodeColor", Gaffer::Plug::In, Color3f( 0.0f ) ) );
	nodeColorPlug()->setFlags( Plug::Serialisable | Plug::AcceptsInputs, false );

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
	return getChild<Plug>( "out" );
}

const Gaffer::Plug *Shader::outPlug() const
{
	return getChild<Plug>( "out" );
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

IECore::MurmurHash Shader::attributesHash() const
{
	IECore::MurmurHash h;
	attributesHash( h );
	return h;
}

void Shader::attributesHash( IECore::MurmurHash &h ) const
{
	attributesHash( outPlug(), h );
}

IECore::ConstCompoundObjectPtr Shader::attributes() const
{
	return attributes( outPlug() );
}

void Shader::attributesHash( const Gaffer::Plug *output, IECore::MurmurHash &h ) const
{
	attributeSuffixPlug()->hash( h );

	NetworkBuilder networkBuilder( output );
	h.append( networkBuilder.stateHash() );
}

IECore::ConstCompoundObjectPtr Shader::attributes( const Gaffer::Plug *output ) const
{
	IECore::CompoundObjectPtr result = new IECore::CompoundObject;
	NetworkBuilder networkBuilder( output );
	if( !networkBuilder.state()->members().empty() )
	{
		std::string attr = typePlug()->getValue();
		std::string postfix = attributeSuffixPlug()->getValue();
		if( postfix != "" )
		{
			attr += ":" + postfix;
		}
		result->members()[attr] = boost::const_pointer_cast<IECore::ObjectVector>(networkBuilder.state());
	}
	return result;
}

IECore::MurmurHash Shader::stateHash() const
{
	NetworkBuilder networkBuilder( outPlug() );
	return networkBuilder.stateHash();
}

void Shader::stateHash( IECore::MurmurHash &h ) const
{
	h.append( stateHash() );
}

IECore::ConstObjectVectorPtr Shader::state() const
{
	NetworkBuilder networkBuilder( outPlug() );
	return networkBuilder.state();
}

void Shader::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	DependencyNode::affects( input, outputs );

	if(
		parametersPlug()->isAncestorOf( input ) ||
		input == enabledPlug() ||
		input == nodeNamePlug() ||
		input == namePlug() ||
		input == typePlug() ||
		input->parent<Plug>() == nodeColorPlug()
	)
	{
		const Plug *out = outPlug();
		if( out )
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
		return Gaffer::CompoundDataPlug::extractDataFromPlug( valuePlug );
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
