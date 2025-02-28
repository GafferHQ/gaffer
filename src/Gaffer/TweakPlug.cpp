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

#include "Gaffer/TweakPlug.h"

#include "Gaffer/PlugAlgo.h"
#include "Gaffer/ScriptNode.h"

#include "IECore/DataAlgo.h"
#include "IECore/PathMatcherData.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/StringAlgo.h"
#include "IECore/TypeTraits.h"

#include "fmt/format.h"

#include "boost/algorithm/string/join.hpp"
#include "boost/algorithm/string/replace.hpp"

#include <unordered_map>
#include <unordered_set>

using namespace std;
using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////
namespace
{

template<typename T>
T vectorAwareMin( const T &v1, const T &v2 )
{
	if constexpr( IECore::TypeTraits::IsVec<T>::value || IECore::TypeTraits::IsColor<T>::value )
	{
		T result;
		for( size_t i = 0; i < T::dimensions(); ++i )
		{
			result[i] = std::min( v1[i], v2[i] );
		}
		return result;
	}
	else
	{
		return std::min( v1, v2 );
	}
}

template<typename T>
T vectorAwareMax( const T &v1, const T &v2 )
{
	if constexpr( IECore::TypeTraits::IsVec<T>::value || IECore::TypeTraits::IsColor<T>::value )
	{
		T result;
		for( size_t i = 0; i < T::dimensions(); ++i )
		{
			result[i] = std::max( v1[i], v2[i] );
		}
		return result;
	}
	else
	{
		return std::max( v1, v2 );
	}
}

template< typename T >
T applyNumericTweak(
	const T &source,
	const T &tweak,
	TweakPlug::Mode mode,
	const std::string &tweakName
)
{
	if constexpr(
		( std::is_arithmetic_v<T> && !std::is_same_v< T, bool > ) ||
		IECore::TypeTraits::IsVec<T>::value ||
		IECore::TypeTraits::IsColor<T>::value
	)
	{
		switch( mode )
		{
			case TweakPlug::Add :
				return source + tweak;
			case TweakPlug::Subtract :
				return source - tweak;
			case TweakPlug::Multiply :
				return source * tweak;
			case TweakPlug::Min :
				return vectorAwareMin( source, tweak );
			case TweakPlug::Max :
				return vectorAwareMax( source, tweak );
			case TweakPlug::ListAppend :
			case TweakPlug::ListPrepend :
			case TweakPlug::ListRemove :
			case TweakPlug::Replace :
			case TweakPlug::Remove :
			case TweakPlug::Create :
			case TweakPlug::CreateIfMissing :
				throw IECore::Exception(
					fmt::format(
						"Cannot apply tweak with mode {} using applyNumericTweak.",
						TweakPlug::modeToString( mode )
					)
				);
			default:
				throw IECore::Exception( fmt::format( "Not a valid tweak mode: {}.", mode ) );
		}
	}
	else
	{
		// NOTE: If we are operating on variables that aren't actually stored in a Data, then the
		// data type reported here may not be technically correct - for example, we might want to
		// call this on elements of a StringVectorData, in which case this would report a type of
		// "StringData", but there is nothing of actual type "StringData". This message still
		// communicates the actual problem though ( we don't support arithmetic on strings ).

		throw IECore::Exception(
			fmt::format(
				"Cannot apply tweak with mode {} to \"{}\" : Data type {} not supported.",
				TweakPlug::modeToString( mode ), tweakName, IECore::TypedData<T>::staticTypeName()
			)
		);
	}
}

template<typename T>
std::vector<T> tweakedList( const std::vector<T> &source, const std::vector<T> &tweak, TweakPlug::Mode mode )
{
	std::vector<T> result = source;

	struct HashFunc
	{
		size_t operator()(const T& x) const
		{
			IECore::MurmurHash h;
			h.append( x );
			return h.h1();
		}
	};

	std::unordered_set<T, HashFunc> tweakSet( tweak.begin(), tweak.end() );

	result.erase(
		std::remove_if(
			result.begin(),
			result.end(),
			[&tweakSet]( const auto &elem )
			{
				return tweakSet.count( elem );
			}
		),
		result.end()
	);

	if( mode == TweakPlug::ListAppend )
	{
		result.insert( result.end(), tweak.begin(), tweak.end() );
	}
	else if( mode == TweakPlug::ListPrepend )
	{
		result.insert( result.begin(), tweak.begin(), tweak.end() );
	}

	return result;
}

template<typename T>
T applyListTweak(
	const T &source,
	const T &tweak,
	TweakPlug::Mode mode,
	const std::string &tweakName
)
{
	// \todo - would look cleaner if we had an IsVector in TypeTraits rather than needed to wrap
	// this is a Data just to check if it's an std::vector
	if constexpr( IECore::TypeTraits::IsVectorTypedData< IECore::TypedData<T> >::value )
	{
		return tweakedList( source, tweak, mode );
	}
	else if constexpr( std::is_same_v<T, IECore::PathMatcher> )
	{
		IECore::PathMatcher result = source;
		if( mode == TweakPlug::ListRemove )
		{
			result.removePaths( tweak );
		}
		else
		{
			result.addPaths( tweak );
		}
		return result;
	}
	else if constexpr( std::is_same_v<T, std::string> )
	{
		std::vector<std::string> sourceVector;
		IECore::StringAlgo::tokenize( source, ' ', sourceVector );
		std::vector<std::string> tweakVector;
		IECore::StringAlgo::tokenize( tweak, ' ', tweakVector );
		return boost::algorithm::join( tweakedList( sourceVector, tweakVector, mode ), " " );
	}
	else
	{
		throw IECore::Exception(
			fmt::format(
				"Cannot apply tweak with mode {} to \"{}\" : Data type {} not supported.",
				TweakPlug::modeToString( mode ), tweakName, IECore::TypedData<T>::staticTypeName()
			)
		);
	}
}

template< typename T >
T applyReplaceTweak(
	const T &source,
	const T &tweak
)
{
	if constexpr( std::is_same_v< T, std::string > )
	{
		return boost::replace_all_copy( tweak, "{source}", source );
	}
	else if constexpr ( std::is_same_v< T, IECore::InternedString > )
	{
		return IECore::InternedString( boost::replace_all_copy( tweak.string(), "{source}", source.string() ) );
	}
	else
	{
		return tweak;
	}
}

template< typename T >
T applyValueTweak(
	const T &source,
	const T &tweak,
	TweakPlug::Mode mode,
	const std::string &tweakName
)
{
	if(
		mode == Gaffer::TweakPlug::Add ||
		mode == Gaffer::TweakPlug::Subtract ||
		mode == Gaffer::TweakPlug::Multiply ||
		mode == Gaffer::TweakPlug::Min ||
		mode == Gaffer::TweakPlug::Max
	)
	{
		return applyNumericTweak( source, tweak, mode, tweakName );
	}
	else if(
		mode == TweakPlug::ListAppend ||
		mode == TweakPlug::ListPrepend ||
		mode == TweakPlug::ListRemove
	)
	{
		return applyListTweak( source, tweak, mode, tweakName );
	}
	else if( mode == TweakPlug::Replace )
	{
		return applyReplaceTweak( source, tweak );
	}
	else
	{
		throw IECore::Exception(
			fmt::format(
				"Cannot apply tweak with mode {} using applyValueTweak.",
				TweakPlug::modeToString( mode )
			)
		);
	}
}


template <typename T>
void removeUnusedElements( std::vector<int> &indices, std::vector<T> &data )
{
	std::vector<int> used( data.size(), -1 );

	for( const int &i : indices )
	{
		used[i] = 1;
	}

	int accum = 0;
	for( int &i : used )
	{
		if( i != -1 )
		{
			i = accum;
			accum += 1;
		}
	}

	if( accum == (int)data.size() )
	{
		// All elements were used
		return;
	}

	std::vector<T> result;
	result.reserve( accum );
	for( size_t j = 0; j < data.size(); j++ )
	{
		if( used[j] != -1 )
		{
			result.push_back( data[j] );
		}
	}

	for( int &i : indices )
	{
		i = used[i];
	}

	data.swap( result );
}

template< typename T>
bool constexpr hasZeroConstructor()
{
	// Some types, like V3f and Color3f, won't default initialize unless we explicitly
	// pass 0 to the constructor. Other types don't have a constructor that accepts 0,
	// so we need to distinguish the two somehow. Currently, I'm using a blacklist of
	// types that don't need to be initialized to zero ... my rationale is that if a new
	// type is added, I would rather get a compile error than get uninitialized memory.
	return !(
		IECore::TypeTraits::IsBox< T >::value ||
		IECore::TypeTraits::IsMatrix< T >::value ||
		IECore::TypeTraits::IsQuat< T >::value ||
		std::is_same_v< T, IECore::InternedString > ||
		std::is_same_v< T, std::string >
	);
}

// There are a lot of different ways data could be convertible - this should probably be
// expanded. But just handling simple numeric types makes things easier when we need to
// use this in PromoteInstances.

template< typename A, typename B >
constexpr bool valueTypesAreConvertible()
{
	return std::is_arithmetic_v< A > && std::is_arithmetic_v< B >;
}

template< typename A, typename B >
constexpr A convertValueType( const B &b )
{
	return b;
}

template< typename DestDataType, typename SrcDataType >
typename DestDataType::Ptr convertData( const SrcDataType *srcData )
{
	if constexpr( TypeTraits::IsTypedData<SrcDataType>::value )
	{
		if constexpr( valueTypesAreConvertible< typename SrcDataType::ValueType, typename DestDataType::ValueType >() )
		{
			typename DestDataType::Ptr resultData = new DestDataType();
			resultData->writable() = convertValueType< typename DestDataType::ValueType >( srcData->readable() );
			return resultData;
		}
		else if constexpr( TypeTraits::IsVectorTypedData< SrcDataType >::value && TypeTraits::IsVectorTypedData< DestDataType >::value )
		{
			if constexpr( valueTypesAreConvertible< typename SrcDataType::ValueType::value_type, typename DestDataType::ValueType::value_type >() )
			{
				typename DestDataType::Ptr resultData = new DestDataType();
				auto &result = resultData->writable();
				result.reserve( srcData->readable().size() );
				for( const auto &i : srcData->readable() )
				{
					result.push_back( convertValueType< typename DestDataType::ValueType::value_type >( i ) );
				}
				return resultData;
			}
		}
	}
	return nullptr;
}

} // namespace

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
	addChild( new IntPlug( "mode", direction, Replace, First, Last ) );

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

bool TweakPlug::applyTweak( IECore::CompoundData *parameters, MissingMode missingMode ) const
{
	return applyTweak(
		[&parameters]( const std::string &valueName, const bool withFallback ) { return parameters->member( valueName ); },
		[&parameters]( const std::string &valueName, DataPtr newData )
		{
			if( newData == nullptr )
			{
				return parameters->writable().erase( valueName ) > 0;
			}
			parameters->writable()[valueName] = newData;
			return true;
		},
		missingMode
	);
}

const char *TweakPlug::modeToString( Gaffer::TweakPlug::Mode mode )
{
	switch( mode )
	{
		case Gaffer::TweakPlug::Replace :
			return "Replace";
		case Gaffer::TweakPlug::Add :
			return "Add";
		case Gaffer::TweakPlug::Subtract :
			return "Subtract";
		case Gaffer::TweakPlug::Multiply :
			return "Multiply";
		case Gaffer::TweakPlug::Remove :
			return "Remove";
		case Gaffer::TweakPlug::Create :
			return  "Create";
		case Gaffer::TweakPlug::Min :
			return "Min";
		case Gaffer::TweakPlug::Max :
			return "Max";
		case Gaffer::TweakPlug::ListAppend :
			return "ListAppend";
		case Gaffer::TweakPlug::ListPrepend :
			return "ListPrepend";
		case Gaffer::TweakPlug::ListRemove :
			return "ListRemove";
		case Gaffer::TweakPlug::CreateIfMissing :
			return "CreateIfMissing";
	}
	return  "Invalid";
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
	for( const auto &tweakPlug : TweakPlug::Range( *this ) )
	{
		result->addChild( tweakPlug->createCounterpart( tweakPlug->getName(), direction ) );
	}
	return result;
}

bool TweaksPlug::applyTweaks( IECore::CompoundData *parameters, TweakPlug::MissingMode missingMode ) const
{
	bool applied = false;
	for( const auto &tweak : TweakPlug::Range( *this ) )
	{
		if( tweak->applyTweak( parameters, missingMode ) )
		{
			applied = true;
		}
	}
	return applied;
}


void TweakPlug::applyTweakInternal( IECore::Data *data, const IECore::Data *tweakData, TweakPlug::Mode mode, const std::string &name )
{
	IECore::dispatch(
		data,
		[&tweakData, &mode, &name] ( auto dataTyped )
		{
			using DataType = typename std::remove_const_t<std::remove_pointer_t<decltype( dataTyped )> >;
			if constexpr( IECore::TypeTraits::IsTypedData< DataType >::value )
			{
				const DataType *tweakDataMatchingTyped = IECore::runTimeCast< const DataType >( tweakData );
				typename DataType::Ptr tweakDataConverted;

				if( !tweakDataMatchingTyped )
				{
					tweakDataConverted = IECore::dispatch( tweakData,
						[]( const auto *tweakDataTyped )
						{
							return convertData<DataType>( tweakDataTyped );
						}
					);
					tweakDataMatchingTyped = tweakDataConverted.get();
				}

				if( !tweakDataMatchingTyped )
				{
					throw IECore::Exception(
						fmt::format( "Cannot apply tweak to \"{}\" : Value of type \"{}\" does not match parameter of type \"{}\"", name, dataTyped->typeName(), tweakData->typeName() )
					);
				}

				auto &value = dataTyped->writable();
				value = applyValueTweak( value, tweakDataMatchingTyped->readable(), mode, name );
			}
			else
			{
				throw IECore::Exception( fmt::format( "Cannot apply tweak to \"{}\" of type \"{}\"", name, dataTyped->typeName() ) );
			}
		}
	);
}

IECore::DataPtr TweakPlug::createVectorDataFromElement( const IECore::Data *elementData, size_t size, bool useElementValueAsDefault, const std::string &name )
{
	return IECore::dispatch(
		elementData,
		[&size, &useElementValueAsDefault, &name] ( auto elementDataTyped ) -> IECore::DataPtr
		{
			using DataType = typename std::remove_const_t<std::remove_pointer_t<decltype( elementDataTyped )> >;
			using ValueType = typename DataType::ValueType;

			if constexpr(
				IECore::TypeTraits::IsTypedData< DataType >::value &&
				!IECore::TypeTraits::IsVectorTypedData< DataType >::value &&

				// A bunch of things we're not allowed to make vectors of
				!IECore::TypeTraits::IsTransformationMatrix< ValueType >::value &&
				!IECore::TypeTraits::IsSpline< ValueType >::value &&
				!std::is_same_v< ValueType, IECore::PathMatcher > &&
				!std::is_same_v< ValueType, boost::posix_time::ptime >
			)
			{
				constexpr bool isGeometric = IECore::TypeTraits::IsGeometricTypedData< DataType >::value;
				using VectorDataType = std::conditional_t<
					isGeometric,
					IECore::GeometricTypedData< std::vector< ValueType > >,
					IECore::TypedData< std::vector< ValueType > >
				>;

				typename VectorDataType::Ptr vectorData = new VectorDataType();

				if( useElementValueAsDefault )
				{
					vectorData->writable().resize( size, elementDataTyped->readable() );
				}
				else
				{
					// Some types, like V3f and Color3f, won't default initialize unless we explicitly
					// pass 0 to the constructor. Other types don't have a constructor that accepts 0,
					// so we need to distinguish the two somehow. Currently, I'm using a blacklist of
					// types that don't need to be initialized to zero ... my rationale is that if a new
					// type is added, I would rather get a compile error than get uninitialized memory.
					if constexpr( !hasZeroConstructor< ValueType >() )
					{
						vectorData->writable().resize( size, ValueType() );
					}
					else
					{
						vectorData->writable().resize( size, ValueType( 0 ) );
					}
				}

				if constexpr( isGeometric )
				{
					vectorData->setInterpretation( elementDataTyped->getInterpretation() );
				}

				return vectorData;
			}
			else
			{
				throw IECore::Exception( fmt::format(
					"Invalid type \"{}\" for non-constant element-wise tweak \"{}\".",
					elementDataTyped->typeName(), name
				) );
			}
		}
	);
}

void TweakPlug::applyVectorElementTweak( IECore::Data *vectorData, const IECore::Data *tweakData, IECore::IntVectorData *indicesData, TweakPlug::Mode mode, const std::string &name, const boost::dynamic_bitset<> *mask )
{
	IECore::dispatch( vectorData,
		[&tweakData, &indicesData, &mode, &name, &mask]( auto *vectorDataTyped )
		{
			using SourceType = typename std::remove_pointer_t<decltype( vectorDataTyped )>;
			if constexpr( IECore::TypeTraits::IsVectorTypedData< SourceType >::value )
			{
				auto &result = vectorDataTyped->writable();
				using ElementType = typename SourceType::ValueType::value_type;
				using ElementDataType = IECore::TypedData< ElementType >;

				const ElementDataType* tweakDataMatchingTyped = IECore::runTimeCast< const ElementDataType >( tweakData );
				typename ElementDataType::Ptr tweakDataConverted;

				if( !tweakDataMatchingTyped )
				{
					tweakDataConverted = IECore::dispatch( tweakData,
						[]( auto *tweakDataTyped )
						{
							return convertData<ElementDataType>( tweakDataTyped );
						}
					);
					tweakDataMatchingTyped = tweakDataConverted.get();
				}

				if( !tweakDataMatchingTyped )
				{
					throw IECore::Exception(
						fmt::format(
							"Cannot apply tweak to \"{}\" : Parameter should be of type \"{}\" in order to apply "
							"to an element of \"{}\", but got \"{}\" instead.",
							name, ElementDataType::staticTypeName(), vectorDataTyped->typeName(), tweakData->typeName()
						)
					);
				}

				auto &tweak = tweakDataMatchingTyped->readable();

				if( mask && indicesData )
				{
					// OK, this is a somewhat complex special case - we are only tweaking some data, based
					// on indices, but some indices currently refer to the same data. If we end up tweaking
					// only some of the indices that currently refer to the same data, then we're splitting
					// it into two different values, and need to add a new piece of data to hold the new
					// value.

					result.reserve( result.size() + mask->count() );


					std::vector<int> &indices = indicesData->writable();
					std::unordered_map< int, int > tweakedIndices;

					if( mask->size() != indices.size() )
					{
						throw IECore::Exception(
							fmt::format(
								"Invalid call to TweakPlug::applyElementwiseTweak. Mask size {} doesn't match indices size {}.",
								mask->size(), indices.size()
							)
						);
					}

					for( size_t i = 0 ; i < mask->size(); i++ )
					{
						if( mask->test(i) )
						{
							auto[ it, inserted ] = tweakedIndices.try_emplace( indices[i], result.size() );
							if( inserted )
							{
								result.push_back( applyValueTweak<ElementType>( result[indices[i]], tweak, mode, name ) );
							}
							indices[i] = it->second;
						}
					}


					// If we actually ended up tweaking all indices that used a piece of data, that data is now
					// abandoned, so we should now do a scan to remove unused data.
					removeUnusedElements( indices, result );

					result.shrink_to_fit();
				}
				else if( mask )
				{
					if( mask->size() != result.size() )
					{
						throw IECore::Exception(
							fmt::format(
								"Invalid call to TweakPlug::applyElementwiseTweak. Mask size {} doesn't match data size {}.",
								mask->size(), result.size()
							)
						);
					}

					// If there are no indices, then we just modify the data where the mask is true
					for( size_t i = 0 ; i < result.size(); i++ )
					{
						if( mask->test(i) )
						{
							result[i] = applyValueTweak<ElementType>( result[i], tweak, mode, name );
						}
					}
				}
				else
				{
					// If there is no mask given, we're just modifying all the data, and it doesn't matter
					// whether or not there are indices.

					// I probably should have paid more attention to what r-value references are in general,
					// but in this case it seems like a pretty safe way to force this to work with the
					// vector-of-bool weirdness
					for( auto &&i : result )
					{
						i = applyValueTweak<ElementType>( i, tweak, mode, name );
					}
				}
			}
			else
			{
				throw IECore::Exception( fmt::format(
					"Could not apply tweak to \"{}\" : Expected vector typed data, got \"{}\".",
					name, vectorDataTyped->typeName()
				) );
			}
		}
	);

}
