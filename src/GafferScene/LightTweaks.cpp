//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "IECore/Shader.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/SplineData.h"

#include "Gaffer/StringAlgo.h"
#include "Gaffer/CompoundDataPlug.h"
#include "Gaffer/SplinePlug.h"

#include "GafferScene/LightTweaks.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// TweakPlug
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( LightTweaks::TweakPlug );

LightTweaks::TweakPlug::TweakPlug( const std::string &tweakName, Gaffer::ValuePlugPtr valuePlug, bool enabled )
	:	Plug( "tweak", In, Default | Dynamic )
{
	construct( tweakName, valuePlug, enabled );
}

LightTweaks::TweakPlug::TweakPlug( const std::string &tweakName, const IECore::Data *value, bool enabled )
	:	Plug( "tweak", In, Default | Dynamic )
{
	construct( tweakName, CompoundDataPlug::createPlugFromData( "value", In, Default | Dynamic, value ), enabled );
}

LightTweaks::TweakPlug::TweakPlug( const std::string &name, Direction direction, unsigned flags )
	:	Plug( name, direction, flags )
{
}

void LightTweaks::TweakPlug::construct( const std::string &tweakName, Gaffer::ValuePlugPtr valuePlug, bool enabled )
{
	addChild( new StringPlug( "name" ) );
	addChild( new BoolPlug( "enabled", Plug::In, true ) );
	addChild( new IntPlug( "mode", Plug::In, Replace, Replace, Multiply ) );
	valuePlug->setName( "value" );
	valuePlug->setFlags( Dynamic, true );
	addChild( valuePlug );

	namePlug()->setValue( tweakName );
	enabledPlug()->setValue( enabled );
}

Gaffer::StringPlug *LightTweaks::TweakPlug::namePlug()
{
	return getChild<StringPlug>( 0 );
}

const Gaffer::StringPlug *LightTweaks::TweakPlug::namePlug() const
{
	return getChild<StringPlug>( 0 );
}

Gaffer::BoolPlug *LightTweaks::TweakPlug::enabledPlug()
{
	return getChild<BoolPlug>( 1 );
}

const Gaffer::BoolPlug *LightTweaks::TweakPlug::enabledPlug() const
{
	return getChild<BoolPlug>( 1 );
}

Gaffer::IntPlug *LightTweaks::TweakPlug::modePlug()
{
	return getChild<IntPlug>( 2 );
}

const Gaffer::IntPlug *LightTweaks::TweakPlug::modePlug() const
{
	return getChild<IntPlug>( 2 );
}

template<typename T>
T *LightTweaks::TweakPlug::valuePlug()
{
	return getChild<T>( 3 );
}

template<typename T>
const T *LightTweaks::TweakPlug::valuePlug() const
{
	return getChild<T>( 3 );
}

bool LightTweaks::TweakPlug::acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
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

Gaffer::PlugPtr LightTweaks::TweakPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	PlugPtr result = new TweakPlug( name, direction, getFlags() );
	for( PlugIterator it( this ); !it.done(); ++it )
	{
		result->addChild( (*it)->createCounterpart( (*it)->getName(), direction ) );
	}
	return result;
}

//////////////////////////////////////////////////////////////////////////
// LightTweaks
//////////////////////////////////////////////////////////////////////////

namespace
{

const char *modeToString( LightTweaks::TweakPlug::Mode mode )
{
	switch( mode )
	{
		case LightTweaks::TweakPlug::Replace :
			return "Replace";
		case LightTweaks::TweakPlug::Add :
			return "Add";
		case LightTweaks::TweakPlug::Subtract :
			return "Subtract";
		case LightTweaks::TweakPlug::Multiply :
			return "Multiply";
		default :
			return "Invalid";
	}
}

template<typename PlugType>
void basicTweak( Data *data, PlugType *plug, LightTweaks::TweakPlug::Mode mode )
{
	if( mode != LightTweaks::TweakPlug::Replace )
	{
		throw IECore::Exception( boost::str( boost::format(
			"%s mode not supported for \"%s\""
		) % modeToString( mode ) % data->typeName() ) );
	}

	typedef TypedData<typename PlugType::ValueType> DataType;
	DataType *typedData = runTimeCast<DataType>( data );
	if( !typedData )
	{
		throw IECore::Exception( boost::str( boost::format(
			"Plug type \"%s\" does not match parameter type \"%s\""
		) % plug->typeName() % data->typeName() ) );
	}

	typedData->writable() = plug->getValue();
}

template<typename PlugType>
void numericTweak( Data *data, PlugType *plug, LightTweaks::TweakPlug::Mode mode )
{
	typedef TypedData<typename PlugType::ValueType> DataType;
	DataType *typedData = runTimeCast<DataType>( data );
	if( !typedData )
	{
		throw IECore::Exception( boost::str( boost::format(
			"Plug type \"%s\" does not match parameter type \"%s\""
		) % plug->typeName() % data->typeName() ) );
	}

	const typename PlugType::ValueType value = plug->getValue();
	switch( mode )
	{
		case LightTweaks::TweakPlug::Replace :
			typedData->writable() = value;
			break;
		case LightTweaks::TweakPlug::Add :
			typedData->writable() += value;
			break;
		case LightTweaks::TweakPlug::Subtract :
			typedData->writable() -= value;
			break;
		case LightTweaks::TweakPlug::Multiply :
			typedData->writable() *= value;
			break;
	}
}

void tweak( Data *data, Plug *plug, LightTweaks::TweakPlug::Mode mode )
{
	switch( static_cast<Gaffer::TypeId>( plug->typeId() ) )
	{
		case FloatPlugTypeId :
			numericTweak( data, static_cast<const FloatPlug *>( plug ), mode );
			break;
		case IntPlugTypeId :
			numericTweak( data, static_cast<const IntPlug *>( plug ), mode );
			break;
		case StringPlugTypeId :
			basicTweak( data, static_cast<const StringPlug *>( plug ), mode );
			break;
		case BoolPlugTypeId :
			basicTweak( data, static_cast<const BoolPlug *>( plug ), mode );
			break;
		case V2iPlugTypeId :
			numericTweak( data, static_cast<const V2iPlug *>( plug ), mode );
			break;
		case V3iPlugTypeId :
			numericTweak( data, static_cast<const V3iPlug *>( plug ), mode );
			break;
		case V2fPlugTypeId :
			numericTweak( data, static_cast<const V2fPlug *>( plug ), mode );
			break;
		case V3fPlugTypeId :
			numericTweak( data, static_cast<const V3fPlug *>( plug ), mode );
			break;
		case Color3fPlugTypeId :
			numericTweak( data, static_cast<const Color3fPlug *>( plug ), mode );
			break;
		case Color4fPlugTypeId :
			numericTweak( data, static_cast<const Color4fPlug *>( plug ), mode );
			break;
		case Box2fPlugTypeId :
			basicTweak( data, static_cast<const Box2fPlug *>( plug ), mode );
			break;
		case Box2iPlugTypeId :
			basicTweak( data, static_cast<const Box2iPlug *>( plug ), mode );
			break;
		case Box3fPlugTypeId :
			basicTweak( data, static_cast<const Box3fPlug *>( plug ), mode );
			break;
		case Box3iPlugTypeId :
			basicTweak( data, static_cast<const Box3iPlug *>( plug ), mode );
			break;
		case SplineffPlugTypeId :
			basicTweak( data, static_cast<const SplineffPlug *>( plug ), mode );
			break;
		case SplinefColor3fPlugTypeId :
			basicTweak( data, static_cast<const SplinefColor3fPlug *>( plug ), mode );
			break;
		case M44fPlugTypeId :
			basicTweak( data, static_cast<const M44fPlug *>( plug ), mode );
			break;
		default :
			throw IECore::Exception(
				boost::str( boost::format( "Plug \"%s\" has unsupported type \"%s\"" ) % plug->getName().string() % plug->typeName() )
			);
	}
}

} // namespace

IE_CORE_DEFINERUNTIMETYPED( LightTweaks );

size_t LightTweaks::g_firstPlugIndex = 0;

LightTweaks::LightTweaks( const std::string &name )
	:	SceneElementProcessor( name, Filter::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "type", Plug::In, "light *:light" ) );
	addChild( new Plug( "tweaks" ) );

	// Fast pass-throughs for the things we don't alter.
	outPlug()->objectPlug()->setInput( inPlug()->objectPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
}

LightTweaks::~LightTweaks()
{
}

Gaffer::StringPlug *LightTweaks::typePlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *LightTweaks::typePlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

Gaffer::Plug *LightTweaks::tweaksPlug()
{
	return getChild<Gaffer::Plug>( g_firstPlugIndex + 1 );
}

const Gaffer::Plug *LightTweaks::tweaksPlug() const
{
	return getChild<Gaffer::Plug>( g_firstPlugIndex + 1 );
}

void LightTweaks::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( tweaksPlug()->isAncestorOf( input ) || input == typePlug() )
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}
}

bool LightTweaks::processesAttributes() const
{
	// Although the base class says that we should return a constant, it should
	// be OK to return this because it's constant across the hierarchy.
	return !tweaksPlug()->children().empty();
}

void LightTweaks::hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	typePlug()->hash( h );
	for( TweakPlugIterator tIt( tweaksPlug() ); !tIt.done(); ++tIt )
	{
		for( ValuePlugIterator vIt( tIt->get() ); !vIt.done(); ++vIt )
		{
			(*vIt)->hash( h );
		}
	}
}

IECore::ConstCompoundObjectPtr LightTweaks::computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputAttributes ) const
{
	const string type = typePlug()->getValue();
	if( type.empty() )
	{
		return inputAttributes;
	}

	const Plug *tweaksPlug = this->tweaksPlug();
	if( tweaksPlug->children().empty() )
	{
		return inputAttributes;
	}


	CompoundObjectPtr result = new CompoundObject;
	const CompoundObject::ObjectMap &in = inputAttributes->members();
	CompoundObject::ObjectMap &out = result->members();
	for( CompoundObject::ObjectMap::const_iterator it = in.begin(), eIt = in.end(); it != eIt; ++it )
	{
		if( !StringAlgo::matchMultiple( it->first, type ) )
		{
			out.insert( *it );
			continue;
		}
		const ObjectVector *network = runTimeCast<const ObjectVector>( it->second.get() );
		if( !network || network->members().empty() )
		{
			out.insert( *it );
			continue;
		}

		const Shader *lightShader = runTimeCast<const Shader>( network->members().back().get() );
		if( !lightShader )
		{
			out.insert( *it );
			continue;
		}

		ObjectVectorPtr tweakedNetwork = new ObjectVector;
		tweakedNetwork->members() = network->members();
		ShaderPtr tweakedShader = lightShader->copy();
		tweakedNetwork->members().back() = tweakedShader;

		for( TweakPlugIterator tIt( tweaksPlug ); !tIt.done(); ++tIt )
		{
			if( !(*tIt)->enabledPlug()->getValue() )
			{
				continue;
			}
			const std::string name = (*tIt)->namePlug()->getValue();
			if( name.empty() )
			{
				continue;
			}

			Data *parameterValue = tweakedShader->parametersData()->member<Data>( name );
			if( !parameterValue )
			{
				throw IECore::Exception( boost::str( boost::format( "Parameter \"%s\" does not exist" ) % name ) );
			}

			tweak(
				parameterValue,
				(*tIt)->valuePlug<Plug>(),
				static_cast<TweakPlug::Mode>( (*tIt)->modePlug()->getValue() )
			);
		}

		out[it->first] = tweakedNetwork;
	}

	return result;
}
