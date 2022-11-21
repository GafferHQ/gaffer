//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

#include "Gaffer/RandomChoice.h"

#include "Gaffer/Context.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/TypedPlug.h"

#include "IECore/TypeTraits.h"

#include "OpenEXR/ImathRandom.h"

#include <numeric>

using namespace std;
using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

// Types for the `choices.values` plug, templated on the value
// type of the `out` plug.

template<typename T>
using ValuesDataType = std::conditional_t<
	IECore::TypeTraits::IsVec<T>::value,
	IECore::GeometricTypedData<vector<T>>,
	IECore::TypedData<vector<T>>
>;

template<typename T>
using ValuesPlugType = Gaffer::TypedObjectPlug<ValuesDataType<T>>;

// If `plug` is a supported type, downcasts it to its true type and
// calls `functor( plug, args )`. Otherwise, does nothing.
template<typename F>
void dispatchPlugFunction( const ValuePlug *plug, F &&functor )
{
	const IECore::TypeId typeId = plug->typeId();

	switch( (int)typeId )
	{
		case BoolPlugTypeId :
			functor( static_cast<const BoolPlug *>( plug ) );
			break;
		case IntPlugTypeId :
			functor( static_cast<const IntPlug *>( plug ) );
			break;
		case FloatPlugTypeId :
			functor( static_cast<const FloatPlug *>( plug ) );
			break;
		case StringPlugTypeId :
			functor( static_cast<const StringPlug *>( plug ) );
			break;
		case V2iPlugTypeId :
			functor( static_cast<const V2iPlug *>( plug ) );
			break;
		case V3iPlugTypeId :
			functor( static_cast<const V3iPlug *>( plug ) );
			break;
		case V2fPlugTypeId :
			functor( static_cast<const V2fPlug *>( plug ) );
			break;
		case V3fPlugTypeId :
			functor( static_cast<const V3fPlug *>( plug ) );
			break;
		case Color3fPlugTypeId :
			functor( static_cast<const Color3fPlug *>( plug ) );
			break;
		default :
			break;
	}
}

// Utility for setting the value of an individual leaf plug, given the value for a main plug.
// This is needed because `ComputeNode::compute()` operates only on leaf plugs, but our implementation
// naturally ends up with a value for an entire CompoundNumericPlug.

template<typename PlugType>
void setValue( const PlugType *plug, const typename PlugType::ValueType &value, ValuePlug *leafPlug )
{
	assert( leafPlug == plug );
	static_cast<PlugType *>( leafPlug )->setValue( value );
}

template<typename T>
void setValue( const CompoundNumericPlug<T> *plug, const typename CompoundNumericPlug<T>::ValueType &value, ValuePlug *leafPlug )
{
	assert( leafPlug->parent() == plug );
	for( size_t i = 0, e = plug->children().size(); i < e; ++i )
	{
		if( leafPlug == plug->getChild( i ) )
		{
			static_cast<typename CompoundNumericPlug<T>::ChildType *>( leafPlug )->setValue( value[i] );
			return;
		}
	}
}

const InternedString g_outPlugName( "out" );

} // namespace

//////////////////////////////////////////////////////////////////////////
// RandomChoice
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( RandomChoice );

size_t RandomChoice::g_firstPlugIndex = 0;

RandomChoice::RandomChoice( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "seed", Plug::In, 0, 0 ) );
	addChild( new StringPlug( "seedVariable" ) );
	addChild( new ValuePlug( "choices" ) );
	choicesPlug()->addChild( new FloatVectorDataPlug( "weights", Plug::In, new FloatVectorData ) );
}

RandomChoice::~RandomChoice()
{
}

void RandomChoice::setup( const ValuePlug *plug )
{
	if( outPlug() || choicesValuesPlug() )
	{
		throw IECore::Exception( "Already set up" );
	}

	dispatchPlugFunction(
		plug,
		[this] ( const auto plug ) {
			using ValueType = typename remove_pointer_t<decltype( plug )>::ValueType;
			ValuePlugPtr valuesPlug = new ValuesPlugType<ValueType>( "values", Plug::In, new ValuesDataType<ValueType> );
			this->choicesPlug()->addChild( valuesPlug );
			this->addChild( plug->createCounterpart( g_outPlugName, Plug::Out ) );
		}
	);

	if( !outPlug() )
	{
		throw IECore::Exception( "Unsupported plug type" );
	}
}

bool RandomChoice::canSetup( const ValuePlug *plug )
{
	bool result = false;
	dispatchPlugFunction(
		plug,
		[&result] ( const auto plug ) {
			result = true;
		}
	);
	return result;
}

IntPlug *RandomChoice::seedPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const IntPlug *RandomChoice::seedPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

StringPlug *RandomChoice::seedVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const StringPlug *RandomChoice::seedVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

ValuePlug *RandomChoice::choicesPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 2 );
}

const ValuePlug *RandomChoice::choicesPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 2 );
}

FloatVectorDataPlug *RandomChoice::choicesWeightsPlug()
{
	return choicesPlug()->getChild<FloatVectorDataPlug>( 0 );
}

const FloatVectorDataPlug *RandomChoice::choicesWeightsPlug() const
{
	return choicesPlug()->getChild<FloatVectorDataPlug>( 0 );
}

ValuePlug *RandomChoice::outPlugInternal()
{
	return getChild<ValuePlug>( g_outPlugName );
}

const ValuePlug *RandomChoice::outPlugInternal() const
{
	return getChild<ValuePlug>( g_outPlugName );
}

void RandomChoice::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if(
		input == seedPlug() ||
		input == seedVariablePlug() ||
		input == choicesWeightsPlug() ||
		input == choicesValuesPlug()
	)
	{
		if( const Plug *p = outPlug() )
		{
			if( p->children().size() )
			{
				for( const auto &cp : Plug::Range( *p ) )
				{
					outputs.push_back( cp.get() );
				}
			}
			else
			{
				outputs.push_back( p );
			}
		}
	}
}

void RandomChoice::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( output == outPlug() || output->parent() == outPlug() )
	{
		seedPlug()->hash( h );
		const string seedVariable = seedVariablePlug()->getValue();
		if( !seedVariable.empty() )
		{
			h.append( context->variableHash( seedVariable ) );
		}
		choicesWeightsPlug()->hash( h );
		choicesValuesPlug()->hash( h );
		h.append( output->defaultHash() );
	}
}

void RandomChoice::compute( ValuePlug *output, const Context *context ) const
{
	if( output == outPlug() || output->parent() == outPlug() )
	{
		ConstFloatVectorDataPtr weightsData = choicesWeightsPlug()->getValue();
		const vector<float> &weights = weightsData->readable();

		size_t seed = seedPlug()->getValue();
		const string seedVariable = seedVariablePlug()->getValue();
		if( !seedVariable.empty() )
		{
			/// \todo See comments in `Random::computeSeed()`.
			IECore::DataPtr contextData = context->getAsData( seedVariable, nullptr );
			if( contextData )
			{
				const MurmurHash hash = contextData->Object::hash();
				seed += hash.h1();
			}
		}
		Imath::Rand48 random( seed );

		dispatchPlugFunction(
			outPlug(),
			[this, output, &weights, &random] ( auto plug ) {

				using PlugType = remove_const_t<remove_pointer_t<decltype( plug )>>;
				using ValueType = typename PlugType::ValueType;

				auto choicesData = this->choicesValuesPlug<ValuesPlugType<ValueType>>()->getValue();
				const auto &choices = choicesData->readable();
				if( !choices.size() )
				{
					output->setToDefault();
					return;
				}

				if( weights.size() != choices.size() )
				{
					throw IECore::Exception( boost::str(
						boost::format(
							"Length of `choices.weights` does not match length of `choices.values` "
							"(%1% but should be %2%)."
						) % weights.size() % choices.size()
					) );
				}

				const float weightsSum = accumulate(
					weights.begin(), weights.end(), 0.0f
				);
				if( weightsSum == 0.0f )
				{
					output->setToDefault();
					return;
				}

				const float r = random.nextf( 0, weightsSum );

				// We currently do a simple linear search until the summed
				// weight exceeds `r`. Theoretically this could be improved by
				// storing a vector of cumulative weights on an internal plug
				// and doing a binary search on that. But in practice, for the
				// sizes we expect to be dealing with (10s most commonly, perhaps
				// 1000s in the extreme), this appears not to be a win.
				float s = 0;
				for( size_t i = 0; i < choices.size(); ++i )
				{
					s += weights[i];
					if( s >= r )
					{
						setValue( plug, choices[i], output );
						return;
					}
				}

			}
		);
	}
	ComputeNode::compute( output, context );
}
