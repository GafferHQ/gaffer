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
#include "Gaffer/OptionalValuePlug.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/SplinePlug.h"
#include "Gaffer/Switch.h"
#include "Gaffer/TypedPlug.h"

#include "IECoreScene/ShaderNetwork.h"

#include "IECore/VectorTypedData.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind/bind.hpp"
#include "boost/lexical_cast.hpp"

#include "fmt/compile.h"
#include "fmt/format.h"

using namespace std;
using namespace boost::placeholders;
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

using ShaderSet = boost::unordered_set<const Shader *>;

struct CycleDetector
{

	CycleDetector( ShaderSet &downstreamShaders, const Shader *shader )
		:	m_downstreamShaders( downstreamShaders ), m_shader( shader )
	{
		if( !m_downstreamShaders.insert( m_shader ).second )
		{
			throw IECore::Exception(
				fmt::format(
					"Shader \"{}\" is involved in a dependency cycle.",
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
					IECore::MurmurHash result;
					parameterHashForPlug( p, result );
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
						m_network->setOutput( outputParameterForPlug( p ) );
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

		IECoreScene::ShaderNetwork::Parameter outputParameterForPlug( const Plug *parameter )
		{
			assert( isOutputParameter( parameter ) );

			const Shader *shader = static_cast<const Shader *>( parameter->node() );
			IECore::InternedString outputName;
			// Set up an output name if we are a descendant of the output plug.
			// The alternative is a special case ( which should perhaps be removed
			// in the future ), which is that for nodes with one output, parameter
			// is the outPlug instead of being a descendant ( and then we use an
			// empty name ).
			if( shader->outPlug()->isAncestorOf( parameter ) )
			{
				outputName = parameter->relativeName( shader->outPlug() );
			}

			return { this->handle( shader ), outputName };
		}

		void parameterHashForPlug( const Plug *parameter, IECore::MurmurHash &h )
		{
			const Shader *shader = static_cast<const Shader *>( parameter->node() );
			h.append( shaderHash( shader ) );
			if( shader->outPlug()->isAncestorOf( parameter ) )
			{
				h.append( parameter->relativeName( shader->outPlug() ) );
			}
		}

		void checkNoShaderInput( const Gaffer::Plug *parameterPlug )
		{
			const Gaffer::Plug *effectiveParameter = this->effectiveParameter( parameterPlug );
			if( effectiveParameter && isOutputParameter( effectiveParameter ) )
			{
				throw IECore::Exception( fmt::format( "Shader connections to {} are not supported.", parameterPlug->fullName() ) );
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
			shader->blindData()->writable()["label"] = new IECore::StringData( nodeName );
			// \todo: deprecated, stop storing gaffer:nodeName after a grace period
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
				for( Plug::InputIterator it( parameter ); !it.done(); ++it )
				{
					hashParameterWalk( it->get(), h );
				}
			}
			else if( const Gaffer::ArrayPlug *arrayParameter = IECore::runTimeCast<const Gaffer::ArrayPlug>( parameter ) )
			{
				// Array parameter
				for( Plug::InputIterator it( arrayParameter ); !it.done(); ++it )
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
				for( Plug::InputIterator it( parameter ); !it.done(); ++it )
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
				for( Plug::InputIterator it( array ); !it.done(); ++it, ++i )
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
				static_cast<const Shader *>( parameter->node() )->parameterHash( parameter, h );
				assert( isOutputParameter( effectiveParameter ) );
				parameterHashForPlug( effectiveParameter, h );
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
				// We aren't driven by a live connection to a shader node, but we could be picking up an input
				// from a different node, due to the passthrough for disabled nodes.  Note that the input we are
				// finding here could be of a different type than the parameter we are writing a value for, which
				// may cause problems.
				//
				// The best solution I can think of is:
				// * always use ( parameter->node() )->parameterValue( parameter ) regardless of the inputs
				// * modify the shader compute to pass through the input value when the shader is disabled
				//   ( matching the behaviour of correspondingInput )
				// * replace effectiveParameter with drivingParameter, which only returns outputs representing
				//   actual shader connections, and otherwise null, simplifying logic in this class
				//
				// I'm now feeling like this is a pretty good solution, but it's more of a change, so we're
				// not worrying about it for now.
				if( IECore::DataPtr value = effectiveShader->parameterValue( effectiveParameter ) )
				{
					shader->parameters()[parameterName] = value;
				}

				// The children may be driven by actual connections
				addParameterComponentConnections( parameter, parameterName, connections );
			}
			else
			{
				// Store the local value of the parameter even if we have a connection.
				// The value will not be used, but it still lets us track the type of the connection.
				if( IECore::DataPtr value = static_cast<const Shader *>( parameter->node() )->parameterValue( parameter ) )
				{
					shader->parameters()[parameterName] = value;
				}

				connections.push_back( {
					outputParameterForPlug( effectiveParameter ),
					{ IECore::InternedString(), parameterName }
				} );
			}
		}

		void hashParameterComponentConnections( const Gaffer::Plug *parameter, IECore::MurmurHash &h )
		{
			if( isCompoundNumericPlug( parameter ) )
			{
				for( Plug::InputIterator it( parameter ); !it.done(); ++it )
				{
					const Gaffer::Plug *effectiveParameter = this->effectiveParameter( it->get() );
					if( effectiveParameter && isOutputParameter( effectiveParameter ) )
					{
						parameterHashForPlug( effectiveParameter, h );
						h.append( (*it)->getName() );
					}
				}
			}
			else if( (Gaffer::TypeId)parameter->typeId() == SplineffPlugTypeId )
			{
				hashSplineParameterComponentConnections< SplineffPlug >( (const SplineffPlug*)parameter, h );
			}
			else if( (Gaffer::TypeId)parameter->typeId() == SplinefColor3fPlugTypeId )
			{
				hashSplineParameterComponentConnections< SplinefColor3fPlug >( (const SplinefColor3fPlug*)parameter, h );
			}
			else if( (Gaffer::TypeId)parameter->typeId() == SplinefColor4fPlugTypeId )
			{
				hashSplineParameterComponentConnections< SplinefColor4fPlug >( (const SplinefColor4fPlug*)parameter, h );
			}
		}

		template< typename T >
		void hashSplineParameterComponentConnections( const T *parameter, IECore::MurmurHash &h )
		{
			checkNoShaderInput( parameter->interpolationPlug() );

			bool hasInput = false;
			for( unsigned int i = 0; i < parameter->numPoints(); i++ )
			{
				checkNoShaderInput( parameter->pointPlug( i ) );
				checkNoShaderInput( parameter->pointXPlug( i ) );

				const auto* yPlug = parameter->pointYPlug( i );
				const Gaffer::Plug *effectiveParameter = this->effectiveParameter( yPlug  );
				if( effectiveParameter && isOutputParameter( effectiveParameter ) )
				{
					hasInput = true;
					parameterHashForPlug( effectiveParameter, h );
					h.append( i );
				}
				else if( isCompoundNumericPlug( yPlug ) )
				{
					for( Plug::InputIterator it( yPlug ); !it.done(); ++it )
					{
						const Gaffer::Plug *effectiveCompParameter = this->effectiveParameter( it->get() );
						if( effectiveCompParameter && isOutputParameter( effectiveCompParameter ) )
						{
							hasInput = true;
							parameterHashForPlug( effectiveCompParameter, h );
							h.append( i );
							h.append( (*it)->getName() );
						}
					}
				}
			}

			if( hasInput )
			{
				for( unsigned int i = 0; i < parameter->numPoints(); i++ )
				{
					parameter->pointXPlug( i )->hash( h );
				}
			}
		}

		void addParameterComponentConnections( const Gaffer::Plug *parameter, const IECore::InternedString &parameterName, vector<IECoreScene::ShaderNetwork::Connection> &connections )
		{
			if( isCompoundNumericPlug( parameter ) )
			{
				for( Plug::InputIterator it( parameter ); !it.done(); ++it )
				{
					const Gaffer::Plug *effectiveParameter = this->effectiveParameter( it->get() );
					if( effectiveParameter && isOutputParameter( effectiveParameter ) )
					{
						IECore::InternedString inputName = parameterName.string() + "." + (*it)->getName().string();

						connections.push_back( {
							outputParameterForPlug( effectiveParameter ),
							{ IECore::InternedString(), inputName }
						} );
					}
				}
			}
			else if( (Gaffer::TypeId)parameter->typeId() == SplineffPlugTypeId )
			{
				addSplineParameterComponentConnections< SplineffPlug >( (const SplineffPlug*) parameter, parameterName, connections );
			}
			else if( (Gaffer::TypeId)parameter->typeId() == SplinefColor3fPlugTypeId )
			{
				addSplineParameterComponentConnections< SplinefColor3fPlug >( (const SplinefColor3fPlug*)parameter, parameterName, connections );
			}
			else if( (Gaffer::TypeId)parameter->typeId() == SplinefColor4fPlugTypeId )
			{
				addSplineParameterComponentConnections< SplinefColor4fPlug >( (const SplinefColor4fPlug*)parameter, parameterName, connections );
			}
		}

		template< typename T >
		void addSplineParameterComponentConnections( const T *parameter, const IECore::InternedString &parameterName, vector<IECoreScene::ShaderNetwork::Connection> &connections )
		{
			const int n = parameter->numPoints();
			std::vector< std::tuple< int, std::string, const Gaffer::Plug *> > inputs;

			for( int i = 0; i < n; i++ )
			{
				const auto* yPlug = parameter->pointYPlug( i );
				const Gaffer::Plug *effectiveParameter = this->effectiveParameter( yPlug  );
				if( effectiveParameter && isOutputParameter( effectiveParameter ) )
				{
					inputs.push_back( std::make_tuple( i, "", effectiveParameter ) );
				}
				else if( isCompoundNumericPlug( yPlug ) )
				{
					for( Plug::InputIterator it( yPlug ); !it.done(); ++it )
					{
						const Gaffer::Plug *effectiveCompParameter = this->effectiveParameter( it->get() );
						if( effectiveCompParameter && isOutputParameter( effectiveCompParameter ) )
						{
							inputs.push_back( std::make_tuple( i, "." + (*it)->getName().string(), effectiveCompParameter ) );
						}
					}
				}
			}

			if( !inputs.size() )
			{
				return;
			}

			std::vector< int > applySort( n );

			{
				std::vector< std::pair< float, unsigned int > > ordering;
				ordering.reserve( n );
				for( int i = 0; i < n; i++ )
				{
					ordering.push_back( std::make_pair( parameter->pointXPlug( i )->getValue(), i ) );
				}
				std::sort( ordering.begin(), ordering.end() );

				for( int i = 0; i < n; i++ )
				{
					applySort[ ordering[i].second ] = i;
				}
			}

			SplineDefinitionInterpolation interp = (SplineDefinitionInterpolation)parameter->interpolationPlug()->getValue();
			int endPointDupes = 0;
			// \todo : Need to duplicate the logic from SplineDefinition::endPointMultiplicity
			// John requested an explicit notice that we are displeased by this duplication.
			// Possible alternatives to this would be storing SplineDefinitionData instead of SplineData
			// in the ShaderNetwork, or moving the handling of endpoint multiplicity inside Splineff
			if( interp == SplineDefinitionInterpolationCatmullRom )
			{
				endPointDupes = 1;
			}
			else if( interp == SplineDefinitionInterpolationBSpline )
			{
				endPointDupes = 2;
			}
			else if( interp == SplineDefinitionInterpolationMonotoneCubic )
			{
				throw IECore::Exception(
					"Cannot support monotone cubic interpolation for splines with inputs, for plug " + parameter->fullName()
				);
			}


			for( const auto &[ origIndex, componentSuffix, sourcePlug ] : inputs )
			{
				IECoreScene::ShaderNetwork::Parameter sourceParameter = outputParameterForPlug( sourcePlug );

				int index = applySort[ origIndex ];
				int outIndexMin, outIndexMax;
				if( index == 0 )
				{
					outIndexMin = 0;
					outIndexMax = endPointDupes;
				}
				else if( index == n - 1 )
				{
					outIndexMin = endPointDupes + n - 1;
					outIndexMax = endPointDupes + n - 1 + endPointDupes;
				}
				else
				{
					outIndexMin = outIndexMax = index + endPointDupes;
				}

				for( int i = outIndexMin; i <= outIndexMax; i++ )
				{
					IECore::InternedString inputName = fmt::format(
						FMT_COMPILE( "{}[{}].y{}" ),
						parameterName.string(), i, componentSuffix
					);
					connections.push_back( {
						sourceParameter,
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

		using ShaderMap = std::map<const Shader *, HandleAndHash>;
		ShaderMap m_shaders;

		ShaderSet m_downstreamShaders; // Used for detecting cycles

};

//////////////////////////////////////////////////////////////////////////
// Shader implementation
//////////////////////////////////////////////////////////////////////////

static IECore::InternedString g_nodeColorMetadataName( "nodeGadget:color" );

GAFFER_NODE_DEFINE_TYPE( Shader );

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

	Metadata::nodeValueChangedSignal( this ).connect( boost::bind( &Shader::nodeMetadataChanged, this, ::_2 ) );
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

bool Shader::affectsAttributes( const Gaffer::Plug *input ) const
{
	return
		parametersPlug()->isAncestorOf( input ) ||
		input == enabledPlug() ||
		input == nodeNamePlug() ||
		input == namePlug() ||
		input == typePlug() ||
		input->parent<Plug>() == nodeColorPlug() ||
		input == attributeSuffixPlug()
	;
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

	if( affectsAttributes( input ) )
	{
		outputs.push_back( outAttributesPlug() );
	}

	if( input == outAttributesPlug() )
	{
		// Our `outPlug()` is the one that actually gets connected into
		// the ShaderPlug on ShaderAssignment etc. But `ShaderPlug::attributes()`
		// pulls on `outAttributesPlug()`, so when that is dirtied, we should
		// also dirty `outPlug()` to propagate dirtiness to ShaderAssignments.

		if( const Plug *out = outPlug() )
		{
			if( !out->children().empty() )
			{
				for( Plug::RecursiveIterator it( out ); !it.done(); it++ )
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

void Shader::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == outAttributesPlug() )
	{
		ComputeNode::hash( output, context, h );
		const Plug *outputParameter = outPlug();
		if( const std::string *name = context->getIfExists< std::string >( g_outputParameterContextName ) )
		{
			outputParameter = outputParameter->descendant<Plug>( *name );
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
		if( const std::string *name = context->getIfExists< std::string >( g_outputParameterContextName ) )
		{
			outputParameter = outputParameter->descendant<Plug>( *name );
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
	if( auto optionalValuePlug = IECore::runTimeCast<const OptionalValuePlug>( parameterPlug ) )
	{
		if( optionalValuePlug->enabledPlug()->getValue() )
		{
			optionalValuePlug->valuePlug()->hash( h );
		}
	}
	else if( auto valuePlug = IECore::runTimeCast<const ValuePlug>( parameterPlug ) )
	{
		valuePlug->hash( h );
	}
	else
	{
		h.append( parameterPlug->typeId() );
	}
}

IECore::DataPtr Shader::parameterValue( const Gaffer::Plug *parameterPlug ) const
{
	if( auto optionalValuePlug = IECore::runTimeCast<const OptionalValuePlug>( parameterPlug ) )
	{
		if( optionalValuePlug->enabledPlug()->getValue() )
		{
			return Gaffer::PlugAlgo::getValueAsData( optionalValuePlug->valuePlug() );
		}
		else
		{
			return nullptr;
		}
	}
	else if( auto valuePlug = IECore::runTimeCast<const Gaffer::ValuePlug>( parameterPlug ) )
	{
		return Gaffer::PlugAlgo::getValueAsData( valuePlug );
	}

	return nullptr;
}

void Shader::nameChanged( IECore::InternedString oldName )
{
	nodeNamePlug()->setValue( getName() );
}

void Shader::nodeMetadataChanged( IECore::InternedString key )
{
	if( key == g_nodeColorMetadataName )
	{
		IECore::ConstColor3fDataPtr d = Metadata::value<const IECore::Color3fData>( this, g_nodeColorMetadataName );
		nodeColorPlug()->setValue( d ? d->readable() : Color3f( 0.0f ) );
	}
}
