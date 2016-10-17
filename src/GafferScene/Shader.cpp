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

#include "Gaffer/TypedPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/CompoundDataPlug.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/ScriptNode.h"

#include "GafferScene/Shader.h"

using namespace Imath;
using namespace GafferScene;
using namespace Gaffer;

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

Gaffer::Plug *Shader::parametersPlug()
{
	return getChild<Plug>( g_firstPlugIndex + 2 );
}

const Gaffer::Plug *Shader::parametersPlug() const
{
	return getChild<Plug>( g_firstPlugIndex + 2 );
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
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::BoolPlug *Shader::enabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *Shader::nodeNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *Shader::nodeNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

Gaffer::Color3fPlug *Shader::nodeColorPlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::Color3fPlug *Shader::nodeColorPlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 5 );
}

IECore::MurmurHash Shader::attributesHash() const
{
	IECore::MurmurHash h;
	attributesHash( h );
	return h;
}

void Shader::attributesHash( IECore::MurmurHash &h ) const
{
	NetworkBuilder networkBuilder( this );
	h.append( networkBuilder.stateHash() );
}

IECore::ConstCompoundObjectPtr Shader::attributes() const
{
	IECore::CompoundObjectPtr result = new IECore::CompoundObject;
	NetworkBuilder networkBuilder( this );
	if( !networkBuilder.state()->members().empty() )
	{
		result->members()[typePlug()->getValue()] = boost::const_pointer_cast<IECore::ObjectVector>(
			networkBuilder.state()
		);
	}
	return result;
}

IECore::MurmurHash Shader::stateHash() const
{
	NetworkBuilder networkBuilder( this );
	return networkBuilder.stateHash();
}

void Shader::stateHash( IECore::MurmurHash &h ) const
{
	h.append( stateHash() );
}

IECore::ConstObjectVectorPtr Shader::state() const
{
	NetworkBuilder networkBuilder( this );
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

void Shader::parameterHash( const Gaffer::Plug *parameterPlug, NetworkBuilder &network, IECore::MurmurHash &h ) const
{
	const Plug *inputPlug = parameterPlug->source<Plug>();
	if( inputPlug != parameterPlug )
	{
		const Shader *n = IECore::runTimeCast<const Shader>( inputPlug->node() );
		if( n && ( inputPlug == n->outPlug() || n->outPlug()->isAncestorOf( inputPlug ) ) )
		{
			h.append( network.shaderHash( n ) );
			if( inputPlug != n->outPlug() )
			{
				// shader has multiple outputs - we need to make sure the particular
				// output in question is taken into account by the hash.
				h.append( inputPlug->relativeName( n->outPlug() ) );
			}
			return;
		}
		// fall through to hash plug value
	}

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

IECore::DataPtr Shader::parameterValue( const Gaffer::Plug *parameterPlug, NetworkBuilder &network ) const
{
	const Plug *inputPlug = parameterPlug->source<Plug>();
	if( inputPlug != parameterPlug )
	{
		const Shader *n = IECore::runTimeCast<const Shader>( inputPlug->node() );
		if( n && ( inputPlug == n->outPlug() || n->outPlug()->isAncestorOf( inputPlug ) ) )
		{
			const std::string &shaderHandle = network.shaderHandle( n );
			if( !shaderHandle.size() )
			{
				return NULL;
			}
			std::string result = "link:" + shaderHandle;
			if( n->outPlug()->isAncestorOf( inputPlug ) )
			{
				result += "." + inputPlug->relativeName( n->outPlug() );
			}
			return new IECore::StringData( result );
		}
		// fall through to use plug value
	}

	if( const Gaffer::ValuePlug *valuePlug = IECore::runTimeCast<const Gaffer::ValuePlug>( parameterPlug ) )
	{
		return Gaffer::CompoundDataPlug::extractDataFromPlug( valuePlug );
	}

	return NULL;
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

//////////////////////////////////////////////////////////////////////////
// NetworkBuilder implementation
//////////////////////////////////////////////////////////////////////////

struct Shader::NetworkBuilder::CycleDetector
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

Shader::NetworkBuilder::NetworkBuilder( const Shader *rootNode )
	:	m_rootNode( rootNode ), m_handleCount( 0 )
{
}

IECore::MurmurHash Shader::NetworkBuilder::stateHash()
{
	return shaderHash( m_rootNode );
}

IECore::ConstObjectVectorPtr Shader::NetworkBuilder::state()
{
	if( !m_state )
	{
		m_state = new IECore::ObjectVector;
		shader( m_rootNode );
	}
	return m_state;
}

IECore::MurmurHash Shader::NetworkBuilder::shaderHash( const Shader *shaderNode )
{
	shaderNode = effectiveNode( shaderNode );
	if( !shaderNode )
	{
		IECore::MurmurHash h;
		h.append( Shader::staticTypeId() );
		return h;
	}

	CycleDetector cycleDetector( m_downstreamShaders, shaderNode );

	ShaderAndHash &shaderAndHash = m_shaders[shaderNode];
	if( shaderAndHash.hash != IECore::MurmurHash() )
	{
		return shaderAndHash.hash;
	}

	shaderAndHash.hash.append( shaderNode->typeId() );
	shaderNode->namePlug()->hash( shaderAndHash.hash );
	shaderNode->typePlug()->hash( shaderAndHash.hash );

	parameterHashWalk( shaderNode, shaderNode->parametersPlug(), shaderAndHash.hash );

	shaderNode->nodeNamePlug()->hash( shaderAndHash.hash );
	shaderNode->nodeColorPlug()->hash( shaderAndHash.hash );

	return shaderAndHash.hash;
}

void Shader::NetworkBuilder::parameterHashWalk( const Shader *shaderNode, const Gaffer::Plug *parameterPlug, IECore::MurmurHash &h )
{
	for( InputPlugIterator it( parameterPlug ); !it.done(); ++it )
	{
		if( !isLeafParameter( it->get() ) )
		{
			parameterHashWalk( shaderNode, it->get(), h );
		}
		else
		{
			shaderNode->parameterHash( it->get(), *this, h );
		}
	}
}

IECore::Shader *Shader::NetworkBuilder::shader( const Shader *shaderNode )
{
	shaderNode = effectiveNode( shaderNode );
	if( !shaderNode )
	{
		return NULL;
	}

	CycleDetector cycleDetector( m_downstreamShaders, shaderNode );

	ShaderAndHash &shaderAndHash = m_shaders[shaderNode];
	if( shaderAndHash.shader )
	{
		return shaderAndHash.shader.get();
	}

	shaderAndHash.shader = new IECore::Shader( shaderNode->namePlug()->getValue(), shaderNode->typePlug()->getValue() );
	parameterValueWalk( shaderNode, shaderNode->parametersPlug(), IECore::InternedString(), shaderAndHash.shader->parameters() );

	shaderAndHash.shader->blindData()->writable()["gaffer:nodeName"] = new IECore::StringData( shaderNode->nodeNamePlug()->getValue() );
	shaderAndHash.shader->blindData()->writable()["gaffer:nodeColor"] = new IECore::Color3fData( shaderNode->nodeColorPlug()->getValue() );

	m_state->members().push_back( shaderAndHash.shader );

	return shaderAndHash.shader.get();
}

void Shader::NetworkBuilder::parameterValueWalk( const Shader *shaderNode, const Gaffer::Plug *parameterPlug, const IECore::InternedString &parameterName, IECore::CompoundDataMap &values )
{
	for( InputPlugIterator it( parameterPlug ); !it.done(); ++it )
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

		if( !isLeafParameter( it->get() ) )
		{
			parameterValueWalk( shaderNode, it->get(), childParameterName, values );
		}
		else
		{
			if( IECore::DataPtr value = shaderNode->parameterValue( it->get(), *this ) )
			{
				values[childParameterName] = value;
			}
		}
	}
}

bool Shader::NetworkBuilder::isLeafParameter( const Gaffer::Plug *parameterPlug ) const
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

const std::string &Shader::NetworkBuilder::shaderHandle( const Shader *shaderNode )
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

const Shader *Shader::NetworkBuilder::effectiveNode( const Shader *shaderNode ) const
{
	while( shaderNode )
	{
		if( shaderNode->enabledPlug()->getValue() )
		{
			return shaderNode;
		}

		const Plug *correspondingInput = shaderNode->correspondingInput( shaderNode->outPlug() );
		if( !correspondingInput )
		{
			return NULL;
		}

		const Plug *source = correspondingInput->source<Plug>();
		if( source == correspondingInput )
		{
			return NULL;
		}

		shaderNode = source->ancestor<Shader>();
	}
	return NULL;
}
