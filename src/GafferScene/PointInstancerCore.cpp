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

#include "GafferScene/PointInstancerCore.h"

#include "GafferScene/Private/ChildNamesMap.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/PointInstancer.h"

#include "IECore/DataAlgo.h"
#include "IECore/MessageHandler.h"
#include "IECore/NullObject.h"
#include "IECore/VectorTypedData.h"

#include "boost/iterator/function_output_iterator.hpp"
#include "boost/lexical_cast.hpp"

#include "fmt/format.h"

#include <regex>
#include <unordered_map>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

// We want prototype names to be valid identifiers for USD prims, which
// means that '.' and '-' are off limits. So we define `safeFormat()`
// and specialise it for floats. We don't specialise for `string`, even
// though the values may not be USD-safe, because the user is in direct
// control of string values and can fix themselves.
template<typename T>
string safeFormat( const T &t )
{
	return fmt::format( "{}", t );
}

// Note : It's important that this is a one-to-one mapping, so that each
// unique float value produces a unique prototype name.
template<>
string safeFormat( const float &t )
{
	string result;
	auto safePushBack = [&result]( char c ) {
		switch( c )
		{
			case '-' :
				result.push_back( 'n' );
				break;
			case '.' :
				result.push_back( '_' );
				break;
			default :
				result.push_back( c );
				break;
		}
	};
	fmt::format_to(
		boost::make_function_output_iterator( std::ref( safePushBack ) ),
		"{}", t
	);
	return result;
}

struct ContextVariableCreator
{

	virtual ~ContextVariableCreator() {}
	virtual void create( size_t pointIndex, CompoundDataMap &variables ) const = 0;
	virtual void hash( size_t pointIndex, IECore::MurmurHash &h ) const = 0;
	virtual string format( size_t pointIndex ) const = 0;

};

template<typename T>
struct TypedContextVariableCreator : public ContextVariableCreator
{

	TypedContextVariableCreator( const string &name, const PrimitiveVariable &primitiveVariable )
		:	m_name( name ), m_indexedView( primitiveVariable )
	{
	}

	void create( size_t pointIndex, CompoundDataMap &variables ) const override
	{
		variables[m_name] = new TypedData<T>( m_indexedView[pointIndex ] );
	}

	void hash( size_t pointIndex, IECore::MurmurHash &h ) const override
	{
		// `static_cast` needed to avoid the `vector<bool>` fiasco.
		h.append( static_cast<T>( m_indexedView[pointIndex] ) );
	}

	string format( size_t pointIndex ) const override
	{
		return safeFormat( m_indexedView[pointIndex] );
	}

	private :

		InternedString m_name;
		PrimitiveVariable::IndexedView<T> m_indexedView;

};

std::unique_ptr<ContextVariableCreator> makeContextVariableCreator( const std::string &name, const IECoreScene::PrimitiveVariable &primitiveVariable )
{
	return dispatch(

		primitiveVariable.data.get(),

		[&] ( const auto *data ) -> unique_ptr<ContextVariableCreator> {

			using DataType = remove_const_t<remove_pointer_t<decltype( data )>>;

			if constexpr(
				std::is_same_v<DataType, BoolVectorData> ||
				std::is_same_v<DataType, IntVectorData> ||
				std::is_same_v<DataType, FloatVectorData> ||
				std::is_same_v<DataType, StringVectorData>
			)
			{

				using ElementType = typename DataType::ValueType::value_type;
				return make_unique<TypedContextVariableCreator<ElementType>>( name, primitiveVariable );
			}
			else
			{
				IECore::msg( IECore::Msg::Warning, "PointInstancerCore", "PrimitiveVariable \"{}\" has unsupported type \"{}\"", name, data->typeName() );
				return nullptr;
			}
		}

	);

}

using ContextVariableCreators = boost::container::flat_map<string, unique_ptr<ContextVariableCreator>>;

// Magic for using lambdas with `std::visit()`.
template<class... Ts> struct overload : Ts... { using Ts::operator()...; };
template<class... Ts> overload( Ts... ) -> overload<Ts...>;

struct NameFormatter
{

	NameFormatter(
		const std::string &format, const ContextVariableCreators &contextVariables,
		const optional<PrimitiveVariable::IndexedView<float>> &timeOffsets
	)
		:	m_timeOffsets( timeOffsets )
	{
		if( format == "" )
		{
			// Construct default formatter.
			m_parts.push_back( SpecialPart::Name );
			for( const auto &[name, creator] : contextVariables )
			{
				m_parts.push_back( fmt::format( "_{}_", name ) );
				m_parts.push_back( creator.get() );
			}
			if( timeOffsets )
			{
				m_parts.push_back( "_" );
				m_parts.push_back( SpecialPart::TimeOffset );
			}

			return;
		}

		// Parse custom formatter into `m_parts`.

		unordered_set<string> usedContextVariables;
		bool usedName = false;
		bool usedTimeOffset = false;
		bool usedHash = false;

		const regex r( "\\{[^}]*\\}" );

		sregex_iterator matchIt( format.begin(), format.end(), r );
		sregex_iterator matchEnd;

		ssub_match suffix;
		std::string result;
		for( ; matchIt != matchEnd; ++matchIt )
		{
			if( matchIt->prefix().length() )
			{
				m_parts.push_back( matchIt->prefix().str() );
			}

			string token = matchIt->str();
			token = token.substr( 1, token.size() - 2 );
			if( token == "name" )
			{
				m_parts.push_back( SpecialPart::Name );
				usedName = true;
			}
			else if( token == "timeOffset" )
			{
				m_parts.push_back( SpecialPart::TimeOffset );
				usedTimeOffset = true;
			}
			else if( token == "hash" )
			{
				m_parts.push_back( SpecialPart::Hash );
				usedHash = true;
			}
			else
			{
				auto it = contextVariables.find( token );
				if( it != contextVariables.end() )
				{
					m_parts.push_back( it->second.get() );
					usedContextVariables.insert( token );
				}
			}
			suffix = matchIt->suffix();
		}

		// The suffix for one match is the same as the prefix for the next
		// match. So we only need to add the suffix from the last match.
		if( suffix.length() )
		{
			m_parts.push_back( suffix.str() );
		}

		// If we're not using all the available variables, then append the
		// hash to keep the name unique.
		if(
			!usedName ||
			( usedContextVariables.size() < contextVariables.size() ) ||
			( timeOffsets && !usedTimeOffset )
		)
		{
			if( !usedHash )
			{
				m_parts.push_back( "_" );
				m_parts.push_back( SpecialPart::Hash );
			}
		}
	}

	string name( const string &baseName, size_t pointIndex, const IECore::MurmurHash &hash )
	{
		string result;
		for( const auto &part : m_parts )
		{
			std::visit(
				overload {
					[&] ( SpecialPart s )
					{
						switch( s )
						{
							case SpecialPart::Name :
								result += baseName;
								break;
							case SpecialPart::TimeOffset :
								result += safeFormat( m_timeOffsets ? (*m_timeOffsets)[pointIndex] : 0.0f );
								break;
							case SpecialPart::Hash :
								result += hash.toString();
								break;
						}
					},
					[&] ( const ContextVariableCreator *c )
					{
						result += c->format( pointIndex );
					},
					[&] ( string s )
					{
						result += s;
					}

				},
				part
			);
		}

		return result;
	}

	private :

		const optional<PrimitiveVariable::IndexedView<float>> &m_timeOffsets;

		enum class SpecialPart
		{
			Name,
			TimeOffset,
			Hash
		};

		using Part = variant<string, const ContextVariableCreator *, SpecialPart>;
		vector<Part> m_parts;

};

struct PrototypeMap : public IECore::Data
{

	struct Prototype
	{
		string location;
		float timeOffset = 0.0f;
		CompoundDataPtr contextVariables = nullptr;
	};

	using Map = unordered_map<string, Prototype>;
	Map map;

	StringVectorDataPtr orderedNames;
	IntVectorDataPtr updatedPrototypeIndex;

};

IE_CORE_DECLAREPTR( PrototypeMap )

} // namespace

//////////////////////////////////////////////////////////////////////////
// PointInstancerCore
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( PointInstancerCore );

size_t PointInstancerCore::g_firstPlugIndex = 0;

PointInstancerCore::PointInstancerCore( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ObjectPlug( "inPoints", Plug::In, NullObject::defaultNullObject() ) );

	addChild( new StringPlug( "timeOffset" ) );
	addChild( new StringPlug( "contextVariables" ) );
	addChild( new StringPlug( "prototypeFormat" ) );

	addChild( new ObjectPlug( "outPoints", Plug::Out, NullObject::defaultNullObject() ) );

	addChild( new StringVectorDataPlug( "prototypeNames", Plug::Out ) );

	addChild( new StringPlug( "prototypeSelector" ) );

	addChild( new StringPlug( "prototype", Plug::Out ) );
	addChild( new FloatPlug( "prototypeTimeOffset", Plug::Out ) );
	addChild( new AtomicCompoundDataPlug( "prototypeContext", Plug::Out ) );

	addChild( new ObjectPlug( "__prototypeMap", Plug::Out, NullObject::defaultNullObject() ) );

}

PointInstancerCore::~PointInstancerCore()
{
}

Gaffer::ObjectPlug *PointInstancerCore::inPointsPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex );
}

const Gaffer::ObjectPlug *PointInstancerCore::inPointsPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *PointInstancerCore::timeOffsetPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *PointInstancerCore::timeOffsetPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *PointInstancerCore::contextVariablesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *PointInstancerCore::contextVariablesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *PointInstancerCore::prototypeFormatPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *PointInstancerCore::prototypeFormatPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::ObjectPlug *PointInstancerCore::outPointsPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::ObjectPlug *PointInstancerCore::outPointsPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 4 );
}

Gaffer::StringVectorDataPlug *PointInstancerCore::prototypeNamesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::StringVectorDataPlug *PointInstancerCore::prototypeNamesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 5 );
}

Gaffer::StringPlug *PointInstancerCore::prototypeSelectorPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::StringPlug *PointInstancerCore::prototypeSelectorPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 6 );
}

Gaffer::StringPlug *PointInstancerCore::prototypePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::StringPlug *PointInstancerCore::prototypePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 7 );
}

Gaffer::FloatPlug *PointInstancerCore::prototypeTimeOffsetPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::FloatPlug *PointInstancerCore::prototypeTimeOffsetPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 8 );
}

Gaffer::AtomicCompoundDataPlug *PointInstancerCore::prototypeContextPlug()
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 9 );
}

const Gaffer::AtomicCompoundDataPlug *PointInstancerCore::prototypeContextPlug() const
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 9 );
}

Gaffer::ObjectPlug *PointInstancerCore::prototypeMapPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 10 );
}

const Gaffer::ObjectPlug *PointInstancerCore::prototypeMapPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 10 );
}

void PointInstancerCore::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( affectsPrototypeMap( input ) )
	{
		outputs.push_back( prototypeMapPlug() );
	}

	if( affectsOutPoints( input ) )
	{
		outputs.push_back( outPointsPlug() );
	}

	if( affectsPrototypeNames( input ) )
	{
		outputs.push_back( prototypeNamesPlug() );
	}

	if( affectsPrototype( input ) )
	{
		outputs.push_back( prototypePlug() );
	}

	if( affectsPrototypeTimeOffset( input ) )
	{
		outputs.push_back( prototypeTimeOffsetPlug() );
	}

	if( affectsPrototypeContext( input ) )
	{
		outputs.push_back( prototypeContextPlug() );
	}
}

void PointInstancerCore::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == prototypeMapPlug() )
	{
		hashPrototypeMap( context, h );
	}
	else if( output == outPointsPlug() )
	{
		hashOutPoints( context, h );
	}
	else if( output == prototypeNamesPlug() )
	{
		hashPrototypeNames( context, h );
	}
	else if( output == prototypePlug() )
	{
		hashPrototype( context, h );
	}
	else if( output == prototypeTimeOffsetPlug() )
	{
		hashPrototypeTimeOffset( context, h );
	}
	else if( output == prototypeContextPlug() )
	{
		hashPrototypeContext( context, h );
	}
	else
	{
		ComputeNode::hash( output, context, h );
	}
}

void PointInstancerCore::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == prototypeMapPlug() )
	{
		static_cast<ObjectPlug *>( output )->setValue( computePrototypeMap() );
	}
	else if( output == outPointsPlug() )
	{
		static_cast<ObjectPlug *>( output )->setValue( computeOutPoints() );
	}
	else if( output == prototypeNamesPlug() )
	{
		static_cast<StringVectorDataPlug *>( output )->setValue( computePrototypeNames() );
	}
	else if( output == prototypePlug() )
	{
		static_cast<StringPlug *>( output )->setValue( computePrototype() );
	}
	else if( output == prototypeTimeOffsetPlug() )
	{
		static_cast<FloatPlug *>( output )->setValue( computePrototypeTimeOffset() );
	}
	else if( output == prototypeContextPlug() )
	{
		static_cast<AtomicCompoundDataPlug *>( output )->setValue( computePrototypeContext() );
	}
	else
	{
		ComputeNode::compute( output, context );
	}
}

bool PointInstancerCore::affectsPrototypeMap( const Gaffer::Plug *input ) const
{
	return
		input == inPointsPlug() ||
		input == timeOffsetPlug() ||
		input == contextVariablesPlug() ||
		input == prototypeFormatPlug()
	;
}

void PointInstancerCore::hashPrototypeMap( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( prototypeMapPlug(), context, h );
	inPointsPlug()->hash( h );
	timeOffsetPlug()->hash( h );
	contextVariablesPlug()->hash( h );
	prototypeFormatPlug()->hash( h );
}

IECore::ConstObjectPtr PointInstancerCore::computePrototypeMap() const
{
	PrototypeMapPtr result = new PrototypeMap;
	result->orderedNames = new StringVectorData();

	ConstObjectPtr inputObject = inPointsPlug()->getValue();
	const auto primitive = runTimeCast<const IECoreScene::Primitive>( inputObject.get() );
	if( !primitive )
	{
		return result;
	}

	auto prototypes = primitive->variableIndexedView<StringVectorData>( "prototypeRoots" );
	if( !prototypes || !prototypes->size() )
	{
		return result;
	}

	auto prototypeIndex = primitive->variableIndexedView<IntVectorData>( "prototypeIndex" );
	auto timeOffset = primitive->variableIndexedView<FloatVectorData>( timeOffsetPlug()->getValue() );

	// We might be collecting prototypes that happen to have the same name,
	// for example `/path/to/sphere` and `/path/to/another/sphere`. Start
	// by making sure we have a unique base time for each prototype - in this
	// case `{ "sphere", "sphere1" }`.

	vector<string> prototypeBaseNames;
	{
		unordered_set<InternedString> usedNames;
		prototypeBaseNames.reserve( prototypes->size() );
		for( const auto &location : *prototypes )
		{
			auto locationPath = ScenePlug::stringToPath( location );
			InternedString baseName = locationPath.size() ? locationPath.back() : "prototype";
			baseName = Private::ChildNamesMap::uniqueName( baseName, usedNames );
			usedNames.insert( baseName );
			prototypeBaseNames.push_back( baseName );
		}
	}

	// Get functions to generate context variables for each of the
	// primitive variables we've been asked to use.

	const size_t numPoints = primitive->variableSize( IECoreScene::PrimitiveVariable::Vertex );
	boost::container::flat_map<string, unique_ptr<ContextVariableCreator>> contextVariableCreators;

	const string contextVariables = contextVariablesPlug()->getValue();
	for( const auto &[name, primitiveVariable] : primitive->variables )
	{
		if( !IECore::StringAlgo::matchMultiple( name, contextVariables ) )
		{
			continue;
		}
		if( primitive->variableSize( primitiveVariable.interpolation ) != numPoints )
		{
			IECore::msg( IECore::Msg::Warning, "PrimitiveVariable \"{}\" has the wrong size", name );
			continue;
		}
		unique_ptr<ContextVariableCreator> creator = makeContextVariableCreator( name, primitiveVariable );
		if( creator )
		{
			contextVariableCreators[name] = std::move( creator );
		}
	}

	// Now fill our map, so we can quickly access each prototype
	// by the names we publish via the `prototypeNames` plug.

	vector<string> &orderedNames = result->orderedNames->writable();

	if( !timeOffset && contextVariableCreators.empty() )
	{
		// If we're not generating prototype variations, then
		// we just use the base names directly.
		for( size_t i = 0; i < prototypes->size(); ++i )
		{
			result->map[prototypeBaseNames[i]] = { (*prototypes)[i] };
		}
		orderedNames.swap( prototypeBaseNames );
	}
	else
	{
		// Generating prototype variations. Need to visit each point.
		unordered_map<MurmurHash, int> hashToPrototypeIndex;
		vector<int> newPrototypeIndex; newPrototypeIndex.reserve( numPoints );

		NameFormatter formatter( prototypeFormatPlug()->getValue(), contextVariableCreators, timeOffset );

		for( size_t pointIndex = 0; pointIndex < numPoints; ++pointIndex )
		{
			MurmurHash h;
			const int inPrototypeIndex = prototypeIndex ? (*prototypeIndex)[pointIndex] : 0;
			if( inPrototypeIndex < 0 || (size_t)inPrototypeIndex >= prototypes->size() )
			{
				throw IECore::Exception( fmt::format(
					"Prototype index {} out of range (on point {})",
					inPrototypeIndex, pointIndex
				) );
			}

			h.append( inPrototypeIndex );
			if( timeOffset )
			{
				h.append( (*timeOffset)[pointIndex] );
			}
			for( const auto &[name, creator] : contextVariableCreators )
			{
				creator->hash( pointIndex, h );
			}

			auto [hashIt, hashInserted] = hashToPrototypeIndex.insert( { h, orderedNames.size() } );
			if( hashInserted )
			{
				// First time we've encounted this prototype variant.
				// Generate a unique name and add it to the PrototypeMap.

				const string prototypeName = formatter.name( prototypeBaseNames[inPrototypeIndex], pointIndex, h );
				PrototypeMap::Prototype &prototype = result->map[prototypeName];
				assert( prototype.location.empty() ); // Should not have created this already.
				prototype.location = (*prototypes)[inPrototypeIndex];
				prototype.timeOffset = timeOffset ? (*timeOffset)[pointIndex] : 0.0f;
				if( contextVariableCreators.size() )
				{
					prototype.contextVariables = new CompoundData;
					for( const auto &[name, creator] : contextVariableCreators )
					{
						creator->create( pointIndex, prototype.contextVariables->writable() );
					}
				}

				orderedNames.push_back( prototypeName );
			}
			newPrototypeIndex.push_back( hashIt->second );
		}
		result->updatedPrototypeIndex = new IntVectorData( std::move( newPrototypeIndex ) );
	}

	result->orderedNames = new StringVectorData( std::move( orderedNames ) );

	return result;
}

bool PointInstancerCore::affectsOutPoints( const Gaffer::Plug *input ) const
{
	return input == inPointsPlug() || input == prototypeMapPlug();
}

void PointInstancerCore::hashOutPoints( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( outPointsPlug(), context, h );
	inPointsPlug()->hash( h );
	prototypeMapPlug()->hash( h );
}

IECore::ConstObjectPtr PointInstancerCore::computeOutPoints() const
{
	ConstObjectPtr inputObject = inPointsPlug()->getValue();
	const auto primitive = runTimeCast<const IECoreScene::Primitive>( inputObject.get() );
	if( !primitive )
	{
		return inputObject;
	}

	// Create PointInstancer and transfer PrimitiveVariables.

	IECoreScene::PointInstancerPtr result = new IECoreScene::PointInstancer(
		primitive->variableSize( IECoreScene::PrimitiveVariable::Vertex )
	);

	for( const auto &[name, primitiveVariable ] : primitive->variables )
	{
		if( primitiveVariable.interpolation == IECoreScene::PrimitiveVariable::Constant )
		{
			result->variables[name] = primitiveVariable;
		}
		else if( primitive->variableSize( primitiveVariable.interpolation ) == result->getNumPoints() )
		{
			result->variables[name] = IECoreScene::PrimitiveVariable(
				IECoreScene::PrimitiveVariable::Vertex, primitiveVariable.data, primitiveVariable.indices
			);
		}
	}

	// Set prototypes.

	ConstPrototypeMapPtr map = boost::static_pointer_cast<const PrototypeMap>( prototypeMapPlug()->getValue() );
	vector<string> prototypes;
	prototypes.reserve( map->orderedNames->readable().size() );
	for( const auto &name : map->orderedNames->readable() )
	{
		prototypes.push_back( fmt::format( "prototypes/{}", name ) );
	}
	result->setPrototypes( new StringVectorData( std::move( prototypes ) ) );

	if( map->updatedPrototypeIndex )
	{
		result->setPrototypeIndex( map->updatedPrototypeIndex );
	}

	return result;
}

bool PointInstancerCore::affectsPrototypeNames( const Gaffer::Plug *input ) const
{
	return input == prototypeMapPlug();
}

void PointInstancerCore::hashPrototypeNames( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( prototypeNamesPlug(), context, h );
	prototypeMapPlug()->hash( h );
}

IECore::ConstStringVectorDataPtr PointInstancerCore::computePrototypeNames() const
{
	ConstPrototypeMapPtr map = boost::static_pointer_cast<const PrototypeMap>( prototypeMapPlug()->getValue() );
	return map->orderedNames;
}

bool PointInstancerCore::affectsPrototype( const Gaffer::Plug *input ) const
{
	return
		input == prototypeSelectorPlug() ||
		input == prototypeMapPlug()
	;
}

void PointInstancerCore::hashPrototype( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( prototypePlug(), context, h );
	prototypeMapPlug()->hash( h );
	prototypeSelectorPlug()->hash( h );
}

std::string PointInstancerCore::computePrototype() const
{
	ConstPrototypeMapPtr map = boost::static_pointer_cast<const PrototypeMap>( prototypeMapPlug()->getValue() );
	const auto it = map->map.find( prototypeSelectorPlug()->getValue() );
	return it != map->map.end() ? it->second.location : "";
}

bool PointInstancerCore::affectsPrototypeTimeOffset( const Gaffer::Plug *input ) const
{
	return
		input == prototypeSelectorPlug() ||
		input == prototypeMapPlug()
	;
}

void PointInstancerCore::hashPrototypeTimeOffset( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( prototypeTimeOffsetPlug(), context, h );
	prototypeMapPlug()->hash( h );
	prototypeSelectorPlug()->hash( h );
}

float PointInstancerCore::computePrototypeTimeOffset() const
{
	ConstPrototypeMapPtr map = boost::static_pointer_cast<const PrototypeMap>( prototypeMapPlug()->getValue() );
	const auto it = map->map.find( prototypeSelectorPlug()->getValue() );
	return it != map->map.end() ? it->second.timeOffset : 0.0f;
}

bool PointInstancerCore::affectsPrototypeContext( const Gaffer::Plug *input ) const
{
	return
		input == prototypeSelectorPlug() ||
		input == prototypeMapPlug()
	;
}

void PointInstancerCore::hashPrototypeContext( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( prototypeContextPlug(), context, h );
	prototypeMapPlug()->hash( h );
	prototypeSelectorPlug()->hash( h );
}

IECore::ConstCompoundDataPtr PointInstancerCore::computePrototypeContext() const
{
	ConstPrototypeMapPtr map = boost::static_pointer_cast<const PrototypeMap>( prototypeMapPlug()->getValue() );
	const auto it = map->map.find( prototypeSelectorPlug()->getValue() );
	if( it != map->map.end() && it->second.contextVariables )
	{
		return it->second.contextVariables;
	}
	return prototypeContextPlug()->defaultValue();
}
