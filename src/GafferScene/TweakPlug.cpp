//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/TweakPlug.h"

#include "GafferScene/Shader.h"

#include "Gaffer/PlugAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/SplinePlug.h"

#include "IECoreScene/ShaderNetwork.h"
#include "IECoreScene/ShaderNetworkAlgo.h"

#include "IECore/DataAlgo.h"
#include "IECore/TypeTraits.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/SplineData.h"
#include "IECore/StringAlgo.h"

#include <unordered_map>

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// TweakPlug
//////////////////////////////////////////////////////////////////////////

GAFFER_PLUG_DEFINE_TYPE( TweakPlug );

TweakPlug::TweakPlug( const std::string &tweakName, Gaffer::ValuePlugPtr valuePlug, Mode mode, bool enabled )
	:	TweakPlug( valuePlug, "tweak", In, Default | Dynamic )
{
	namePlug()->setValue( tweakName );
	modePlug()->setValue( mode );
	enabledPlug()->setValue( enabled );
}

TweakPlug::TweakPlug( const std::string &tweakName, const IECore::Data *value, Mode mode, bool enabled )
	:	TweakPlug( tweakName, PlugAlgo::createPlugFromData( "value", In, Default | Dynamic, value ), mode, enabled )
{
}

TweakPlug::TweakPlug( Gaffer::ValuePlugPtr valuePlug, const std::string &name, Direction direction, unsigned flags )
	:	ValuePlug( name, direction, flags )
{
	addChild( new StringPlug( "name", direction ) );
	addChild( new BoolPlug( "enabled", direction, true ) );
	addChild( new IntPlug( "mode", direction, Replace, Replace, Remove ) );

	if( valuePlug )
	{
		valuePlug->setName( "value" );
		addChild( valuePlug );
	}
}

Gaffer::StringPlug *TweakPlug::namePlug()
{
	return getChild<StringPlug>( 0 );
}

const Gaffer::StringPlug *TweakPlug::namePlug() const
{
	return getChild<StringPlug>( 0 );
}

Gaffer::BoolPlug *TweakPlug::enabledPlug()
{
	return getChild<BoolPlug>( 1 );
}

const Gaffer::BoolPlug *TweakPlug::enabledPlug() const
{
	return getChild<BoolPlug>( 1 );
}

Gaffer::IntPlug *TweakPlug::modePlug()
{
	return getChild<IntPlug>( 2 );
}

const Gaffer::IntPlug *TweakPlug::modePlug() const
{
	return getChild<IntPlug>( 2 );
}

Gaffer::ValuePlug *TweakPlug::valuePlugInternal()
{
	if( children().size() <= 3 )
	{
		return nullptr;
	}

	return getChild<ValuePlug>( 3 );
}

const Gaffer::ValuePlug *TweakPlug::valuePlugInternal() const
{
	if( children().size() <= 3 )
	{
		return nullptr;
	}

	return getChild<ValuePlug>( 3 );
}

bool TweakPlug::acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
{
	if( !Plug::acceptsChild( potentialChild ) )
	{
		return false;
	}

	if(
		potentialChild->isInstanceOf( StringPlug::staticTypeId() ) &&
		potentialChild->getName() == "name" &&
		!getChild<Plug>( "name" )
	)
	{
		return true;
	}
	else if(
		potentialChild->isInstanceOf( BoolPlug::staticTypeId() ) &&
		potentialChild->getName() == "enabled" &&
		!getChild<Plug>( "enabled" )
	)
	{
		return true;
	}
	else if(
		potentialChild->isInstanceOf( IntPlug::staticTypeId() ) &&
		potentialChild->getName() == "mode" &&
		!getChild<Plug>( "mode" )
	)
	{
		return true;
	}
	else if(
		potentialChild->isInstanceOf( ValuePlug::staticTypeId() ) &&
		potentialChild->getName() == "value" &&
		!getChild<Plug>( "value" )
	)
	{
		return true;
	}

	return false;
}

Gaffer::PlugPtr TweakPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	const Plug *p = valuePlug();
	PlugPtr plugCounterpart = p->createCounterpart( p->getName(), direction );

	return new TweakPlug( runTimeCast<ValuePlug>( plugCounterpart.get() ), name, direction, getFlags() );
}

IECore::MurmurHash TweakPlug::hash() const
{
	MurmurHash result = ValuePlug::hash();

	const auto shaderOutput = this->shaderOutput();
	if( shaderOutput.first )
	{
		shaderOutput.first->attributesHash( shaderOutput.second, result );
	}

	return result;
}

// Utility methods need by applyTweak
namespace
{

const char *modeToString( TweakPlug::Mode mode )
{
	switch( mode )
	{
		case TweakPlug::Replace :
			return "Replace";
		case TweakPlug::Add :
			return "Add";
		case TweakPlug::Subtract :
			return "Subtract";
		case TweakPlug::Multiply :
			return "Multiply";
		case TweakPlug::Remove :
			return "Remove";
		default :
			return "Invalid";
	}
}

// TODO - if these make sense, I guess they should be pushed back to cortex

// IsColorTypedData
template< typename T > struct IsColorTypedData : boost::mpl::and_< TypeTraits::IsTypedData<T>, TypeTraits::IsColor< typename TypeTraits::ValueType<T>::type > > {};

// SupportsArithmeticData
template< typename T > struct SupportsArithData : boost::mpl::or_<  TypeTraits::IsNumericSimpleTypedData<T>, TypeTraits::IsVecTypedData<T>, IsColorTypedData<T>> {};

class NumericTweak
{
public:
	NumericTweak( IECore::Data *sourceData, TweakPlug::Mode mode, const std::string &tweakName )
		: m_sourceData( sourceData ), m_mode( mode ), m_tweakName( tweakName )
	{
	}

	template<typename T>
	void operator()( T * data, typename std::enable_if<SupportsArithData<T>::value>::type *enabler = nullptr ) const
	{
		T *sourceDataCast = runTimeCast<T>( m_sourceData );
		switch( m_mode )
		{
			case TweakPlug::Add :
				data->writable() += sourceDataCast->readable();
				break;
			case TweakPlug::Subtract :
				data->writable() -= sourceDataCast->readable();
				break;
			case TweakPlug::Multiply :
				data->writable() *= sourceDataCast->readable();
				break;
			case TweakPlug::Replace :
			case TweakPlug::Remove :
				// These cases are unused - we handle replace and remove mode outside of numericTweak.
				// But the compiler gets unhappy if we don't handle some cases
				break;
		}
	}

	void operator()( Data * data ) const
	{
		throw IECore::Exception( boost::str( boost::format( "Cannot apply tweak with mode %s to \"%s\" : Data type %s not supported." ) % modeToString( m_mode ) % m_tweakName % m_sourceData->typeName() ) );
	}

private:

	IECore::Data *m_sourceData;
	TweakPlug::Mode m_mode;
	const std::string &m_tweakName;
};

bool applyTweakInternal( TweakPlug::Mode mode, const ValuePlug *valuePlug, const std::string &tweakName, const InternedString &parameterName, IECore::CompoundData *parameters, TweakPlug::MissingMode missingMode )
{
	if( mode == TweakPlug::Remove )
	{
		return parameters->writable().erase( parameterName );
	}

	Data *parameterValue = parameters->member<Data>( parameterName );
	DataPtr newData = PlugAlgo::getValueAsData( valuePlug );
	if( !newData )
	{
		throw IECore::Exception(
			boost::str( boost::format( "Cannot apply tweak to \"%s\" : Value plug has unsupported type \"%s\"" ) % tweakName % valuePlug->typeName() )
		);
	}
	if( parameterValue && parameterValue->typeId() != newData->typeId() )
	{
		throw IECore::Exception( boost::str( boost::format( "Cannot apply tweak to \"%s\" : Value of type \"%s\" does not match parameter of type \"%s\"" ) % tweakName % parameterValue->typeName() % newData->typeName() ) );
	}

	if( !parameterValue )
	{
		if( missingMode == TweakPlug::MissingMode::Ignore )
		{
			return false;
		}
		else if( !( mode == TweakPlug::Replace && missingMode == TweakPlug::MissingMode::IgnoreOrReplace ) )
		{
			throw IECore::Exception( boost::str( boost::format( "Cannot apply tweak with mode %s to \"%s\" : This parameter does not exist" ) % modeToString( mode ) % tweakName ) );
		}
	}

	if( mode == TweakPlug::Replace )
	{
		parameters->writable()[parameterName] = newData;
		return true;
	}

	NumericTweak t( newData.get(), mode, tweakName );
	dispatch( parameterValue, t );
	return true;
}

} // namespace

bool TweakPlug::applyTweak( IECore::CompoundData *parameters, MissingMode missingMode ) const
{
	if( !enabledPlug()->getValue() )
	{
		return false;
	}

	const std::string name = namePlug()->getValue();
	if( name.empty() )
	{
		return false;
	}

	const Mode mode = static_cast<Mode>( modePlug()->getValue() );
	return applyTweakInternal( mode, this->valuePlug(), name, name, parameters, missingMode );
}

bool TweakPlug::applyTweaks( const Plug *tweaksPlug, IECoreScene::ShaderNetwork *shaderNetwork, TweakPlug::MissingMode missingMode )
{
	unordered_map<InternedString, IECoreScene::ShaderPtr> modifiedShaders;

	bool appliedTweaks = false;
	bool removedConnections = false;
	for( TweakPlug::Iterator tIt( tweaksPlug ); !tIt.done(); ++tIt )
	{
		const TweakPlug *tweakPlug = tIt->get();
		const std::string name = tweakPlug->namePlug()->getValue();
		if( name.empty() )
		{
			continue;
		}

		if( !tweakPlug->enabledPlug()->getValue() )
		{
			continue;
		}

		ShaderNetwork::Parameter parameter;
		size_t dotPos = name.find_last_of( '.' );
		if( dotPos == string::npos )
		{
			parameter.shader = shaderNetwork->getOutput().shader;
			parameter.name = name;
		}
		else
		{
			parameter.shader = InternedString( name.c_str(), dotPos );
			parameter.name = InternedString( name.c_str() + dotPos + 1 );
		}

		const IECoreScene::Shader *shader = shaderNetwork->getShader( parameter.shader );
		if( !shader )
		{
			if( missingMode != TweakPlug::MissingMode::Ignore )
			{
				throw IECore::Exception( boost::str(
					boost::format( "Cannot apply tweak \"%1%\" because shader \"%2%\" does not exist" ) % name % parameter.shader
				) );
			}
			else
			{
				continue;
			}
		}

		const Mode mode = static_cast<Mode>( tweakPlug->modePlug()->getValue() );

		if( auto input = shaderNetwork->input( parameter )  )
		{
			if( mode != Mode::Replace )
			{
				throw IECore::Exception( boost::str( boost::format( "Cannot apply tweak to \"%s\" : Mode must be \"Replace\" when a previous connection exists" ) % name ) );
			}
			shaderNetwork->removeConnection( { input, parameter } );
			removedConnections = true;
		}

		const auto shaderOutput = tweakPlug->shaderOutput();
		if( shaderOutput.first )
		{
			// New connection
			ConstCompoundObjectPtr shaderAttributes = shaderOutput.first->attributes( shaderOutput.second );
			const ShaderNetwork *inputNetwork = nullptr;
			for( const auto &a : shaderAttributes->members() )
			{
				if( ( inputNetwork = runTimeCast<const ShaderNetwork>( a.second.get() ) ) )
				{
					break;
				}
			}

			if( inputNetwork && inputNetwork->getOutput() )
			{
				if( mode != Mode::Replace )
				{
					throw IECore::Exception( boost::str( boost::format( "Cannot apply tweak to \"%s\" : Mode must be \"Replace\" when inserting a connection" ) % name ) );
				}
				const auto inputParameter = ShaderNetworkAlgo::addShaders( shaderNetwork, inputNetwork );
				shaderNetwork->addConnection( { inputParameter, parameter } );
				appliedTweaks = true;
			}
		}
		else
		{
			// Regular tweak
			auto modifiedShader = modifiedShaders.insert( { parameter.shader, nullptr } );
			if( modifiedShader.second )
			{
				modifiedShader.first->second = shader->copy();
			}

			if( applyTweakInternal( mode, tweakPlug->valuePlug(), name, parameter.name, modifiedShader.first->second->parametersData(), missingMode ) )
			{
				appliedTweaks = true;
			}
		}
	}

	for( auto &x : modifiedShaders )
	{
		shaderNetwork->setShader( x.first, std::move( x.second ) );
	}

	if( removedConnections )
	{
		ShaderNetworkAlgo::removeUnusedShaders( shaderNetwork );
	}

	return appliedTweaks || removedConnections;
}

std::pair<const GafferScene::Shader *, const Gaffer::Plug *> TweakPlug::shaderOutput() const
{
	const Plug *source = valuePlug()->source();
	if( source != valuePlug() )
	{
		if( auto shader = runTimeCast<const GafferScene::Shader>( source->node() ) )
		{
			if( source == shader->outPlug() || shader->outPlug()->isAncestorOf( source ) )
			{
				return { shader, source };
			}
		}
	}
	return { nullptr, nullptr };
}

//////////////////////////////////////////////////////////////////////////
// TweaksPlug
//////////////////////////////////////////////////////////////////////////

GAFFER_PLUG_DEFINE_TYPE( TweaksPlug );

TweaksPlug::TweaksPlug( const std::string &name, Direction direction, unsigned flags )
	:	ValuePlug( name, direction, flags )
{
}

bool TweaksPlug::acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
{
	if( !ValuePlug::acceptsChild( potentialChild ) )
	{
		return false;
	}

	return runTimeCast<const TweakPlug>( potentialChild );
}

bool TweaksPlug::acceptsInput( const Plug *input ) const
{
	if( !ValuePlug::acceptsChild( input ) )
	{
		return false;
	}

	if( !input )
	{
		return true;
	}

	if( const ScriptNode *s = ancestor<ScriptNode>() )
	{
		if( s->isExecuting() )
		{
			// Before TweaksPlug existed, regular Plugs were
			// used in its place. If such plugs were ever
			// promoted or passed through dots, they will have
			// been serialised with just a regular plug type,
			// and we need to tolerate connections to them
			// on loading.
			return true;
		}
	}

	return runTimeCast<const TweaksPlug>( input );
}

Gaffer::PlugPtr TweaksPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	PlugPtr result = new TweaksPlug( name, direction, getFlags() );
	for( Plug::Iterator it( this ); !it.done(); ++it )
	{
		result->addChild( (*it)->createCounterpart( (*it)->getName(), direction ) );
	}
	return result;
}

bool TweaksPlug::applyTweaks( IECore::CompoundData *parameters, TweakPlug::MissingMode missingMode ) const
{
	bool applied = false;
	for( TweakPlug::Iterator it( this ); !it.done(); ++it )
	{
		if( (*it)->applyTweak( parameters, missingMode ) )
		{
			applied = true;
		}
	}
	return applied;
}

bool TweaksPlug::applyTweaks( IECoreScene::ShaderNetwork *shaderNetwork, TweakPlug::MissingMode missingMode ) const
{
	return TweakPlug::applyTweaks( this, shaderNetwork, missingMode );
}
