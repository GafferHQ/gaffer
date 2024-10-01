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

#include "Gaffer/Collect.h"

#include "Gaffer/NumericPlug.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/TypedObjectPlug.h"

#include "IECore/DataAlgo.h"
#include "IECore/TypeTraits.h"

#include "boost/bind.hpp"

#include "tbb/blocked_range.h"
#include "tbb/parallel_for.h"
#include "tbb/parallel_reduce.h"

#include "fmt/format.h"

using namespace std;
using namespace tbb;
using namespace IECore;
using namespace Gaffer;

namespace
{

// Miscellaneous utilities
// =======================

template<typename T>
void filterVector( vector<T> &v, const vector<unsigned char> &f )
{
	size_t newIndex = 0;
	for( size_t oldIndex = 0; oldIndex < v.size(); ++oldIndex )
	{
		if( f[oldIndex] )
		{
			if( newIndex != oldIndex )
			{
				v[newIndex] = std::move( v[oldIndex] );
			}
			++newIndex;
		}
	}
	v.resize( newIndex );
	v.shrink_to_fit();
}

void filterVectors( CompoundObject *compoundObject, const vector<unsigned char> &filter )
{
	for( auto &[name, value] : compoundObject->members() )
	{
		if( auto o = runTimeCast<ObjectVector>( value.get() ) )
		{
			filterVector( o->members(), filter );
		}
		else
		{
			if( auto d = runTimeCast<UCharVectorData>( value.get() ) )
			{
				// See `OutputTraits<BoolPlug>`.
				value = new BoolVectorData( vector<bool>( d->readable().begin(), d->readable().end() ) );
			}

			IECore::dispatch(
				static_cast<Data *>( value.get() ),
				[&] ( auto *data ) {
					using DataType = remove_pointer_t<decltype( data )>;
					if constexpr ( TypeTraits::IsVectorTypedData<DataType>::value )
					{
						filterVector( data->writable(), filter );
					}
				}
			);
		}
	}
}

using IntRange = blocked_range<int>;
const IECore::InternedString g_enabledOutputs( "__enabledOutputs__" );

// Type-based plug dispatch
// ========================
//
// We need to be able to deal with many types of input plug, which
// we do by calling generic lambdas after downcasting to the specific
// type we are dealing with.

// If `plug` is a supported type, downcasts it to its true type and
// calls `functor( plug, args )`. Otherwise, does nothing.
template<typename F>
void dispatchPlugFunction( const ValuePlug *plug, F &&functor )
{
	switch( (int)plug->typeId() )
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
		case Color4fPlugTypeId :
			functor( static_cast<const Color4fPlug *>( plug ) );
			break;
		case M33fPlugTypeId :
			functor( static_cast<const M33fPlug *>( plug ) );
			break;
		case M44fPlugTypeId :
			functor( static_cast<const M44fPlug *>( plug ) );
			break;
		case IntVectorDataPlugTypeId :
			functor( static_cast<const IntVectorDataPlug *>( plug ) );
			break;
		case StringVectorDataPlugTypeId :
			functor( static_cast<const StringVectorDataPlug *>( plug ) );
			break;
		case AtomicCompoundDataPlugTypeId :
			functor( static_cast<const AtomicCompoundDataPlug *>( plug ) );
			break;
		case CompoundObjectPlugTypeId :
			functor( static_cast<const CompoundObjectPlug *>( plug ) );
			break;
		case ObjectVectorPlugTypeId :
			functor( static_cast<const ObjectVectorPlug *>( plug ) );
			break;
		default :
			break;
	}
}

// OutputTraits
// ============
//
// Depending on the type of input plug we are collecting from, we will
// need a different type of output plug to store an array of the collected
// values. The OutputTraits template abstracts this away for us.

// By default we collect into an appropriate VectorTypedData object,
// with some careful handling to use GeometricTypedData where necessary.
template<typename InputPlugType>
struct OutputTraits
{
	using ContainerType = vector<typename InputPlugType::ValueType>;
	using ObjectType = std::conditional_t<
		IECore::TypeTraits::IsVec<typename ContainerType::value_type>::value,
		IECore::GeometricTypedData<ContainerType>,
		IECore::TypedData<ContainerType>
	>;
	using PlugType = TypedObjectPlug<ObjectType>;
	static ContainerType &container( ObjectType &object ) { return object.writable(); }
	static typename InputPlugType::ValueType collect( const InputPlugType *input ) { return input->getValue(); }
};

// CompoundData inputs are collected into an ObjectVector object.
template<typename T>
struct OutputTraits<TypedObjectPlug<T>>
{
	using ObjectType = ObjectVector;
	using ContainerType = ObjectVector::MemberContainer;
	using PlugType = ObjectVectorPlug;
	static ContainerType &container( ObjectType &object ) { return object.members(); }
	static ObjectPtr collect( const TypedObjectPlug<T> *input ) {
		// Cast is OK because we're storing into a container that becomes const
		// immediately after returning from compute. We never modify the value.
		return boost::const_pointer_cast<T>( input->getValue() );
	}
};

// BoolPlug inputs are subject to the `vector<bool>` fiasco. We can't write concurrently to
// individual elements of a `vector<bool>`, because they're proxies that mix multiple values
// into a single byte. So we write to a temporary UCharVectorData and then convert to
// BoolVectorData in `filterVectors()`.
template<>
struct OutputTraits<BoolPlug>
{
	using ObjectType = UCharVectorData;
	using ContainerType = UCharVectorData::ValueType;
	using PlugType = BoolVectorDataPlug;
	static ContainerType &container( ObjectType &object ) { return object.writable(); }
	static bool collect( const BoolPlug *input ) { return input->getValue(); }
};

} // namespace

GAFFER_NODE_DEFINE_TYPE( Collect );

size_t Collect::g_firstPlugIndex = 0;

Collect::Collect( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "contextVariable", Plug::In, "collect:value" ) );
	addChild( new StringPlug( "indexContextVariable", Plug::In, "collect:index" ) );
	addChild( new StringVectorDataPlug( "contextValues" ) );
	addChild( new BoolPlug( "enabled", Plug::In, true ) );
	addChild( new ValuePlug( "in", Plug::In, Plug::Flags::Default & ~Plug::Flags::AcceptsInputs ) );
	addChild( new ValuePlug( "out", Plug::Out ) );
	// Will currently always output StringVectorData, but we're using an ObjectPlug
	// for future compatibility with anticipated modes with non-string context variable
	// values (following the pattern established by the Wedge node).
	addChild( new ObjectPlug( "enabledValues", Plug::Out, new StringVectorData ) );
	addChild( new CompoundObjectPlug( "__collection", Plug::Out, new CompoundObject ) );

	inPlug()->childAddedSignal().connect( boost::bind( &Collect::inputAdded, this, ::_2 ) );
	inPlug()->childRemovedSignal().connect( boost::bind( &Collect::inputRemoved, this, ::_2 ) );
}

Collect::~Collect()
{
}

StringPlug *Collect::contextVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const StringPlug *Collect::contextVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

StringPlug *Collect::indexContextVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const StringPlug *Collect::indexContextVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

StringVectorDataPlug *Collect::contextValuesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 2 );
}

const StringVectorDataPlug *Collect::contextValuesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 2 );
}

BoolPlug *Collect::enabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

const BoolPlug *Collect::enabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

ValuePlug *Collect::inPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 4 );
}

const ValuePlug *Collect::inPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 4 );
}

ValuePlug *Collect::outPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 5 );
}

const ValuePlug *Collect::outPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 5 );
}

ObjectPlug *Collect::enabledValuesPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 6 );
}

const ObjectPlug *Collect::enabledValuesPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 6 );
}

CompoundObjectPlug *Collect::collectionPlug()
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 7 );
}

const CompoundObjectPlug *Collect::collectionPlug() const
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 7 );
}

bool Collect::canAddInput( const ValuePlug *prototype ) const
{
	bool result = false;
	dispatchPlugFunction( prototype, [&result] ( auto *plug ) { result = true; } );
	return result;
}

ValuePlug *Collect::addInput( const ValuePlug *prototype )
{
	ValuePlugPtr output;
	dispatchPlugFunction(
		prototype, [&output] ( auto *plug ) {
			using OutputTraits = OutputTraits<remove_const_t<remove_pointer_t<decltype( plug )>>>;
			output = new typename OutputTraits::PlugType( plug->getName(), Plug::Out );
		}
	);

	if( !output )
	{
		throw IECore::Exception( fmt::format( "Unsupported plug type {}", prototype->typeName() ) );
	}

	PlugPtr input = prototype->createCounterpart( prototype->getName(), Plug::In );
	input->setFlags( Plug::Dynamic, false );
	inPlug()->addChild( input );
	outPlug()->addChild( output );

	return static_cast<ValuePlug *>( input.get() );
}

void Collect::removeInput( ValuePlug *inputPlug )
{
	outPlug()->removeChild( outputPlugForInput( inputPlug ) );
	inPlug()->removeChild( inputPlug );
}

ValuePlug *Collect::outputPlugForInput( const ValuePlug *inputPlug )
{
	return const_cast<ValuePlug *>( const_cast<const Collect *>( this )->outputPlugForInput( inputPlug ) );
}

const ValuePlug *Collect::outputPlugForInput( const ValuePlug *inputPlug ) const
{
	if( inputPlug->parent() != inPlug() )
	{
		throw IECore::Exception(
			fmt::format( "`{}` is not an input of `{}`", inputPlug->fullName(), fullName() )
		);
	}

	const ValuePlug *result = outPlug()->getChild<ValuePlug>( inputPlug->getName() );
	if( !result )
	{
		throw IECore::Exception(
			fmt::format( "Expected output `{}.{}` not found", fullName(), inputPlug->getName().string() )
		);
	}
	return result;
}

ValuePlug *Collect::inputPlugForOutput( const ValuePlug *outputPlug )
{
	return const_cast<ValuePlug *>( const_cast<const Collect *>( this )->inputPlugForOutput( outputPlug ) );
}

const ValuePlug *Collect::inputPlugForOutput( const ValuePlug *outputPlug ) const
{
	if( outputPlug->parent() != outPlug() )
	{
		throw IECore::Exception(
			fmt::format( "`{}` is not an output of `{}`", outputPlug->fullName(), fullName() )
		);
	}

	const ValuePlug *result = inPlug()->getChild<ValuePlug>( outputPlug->getName() );
	if( !result )
	{
		throw IECore::Exception(
			fmt::format( "Expected input `{}.{}` not found", fullName(), outputPlug->getName().string() )
		);
	}
	return result;
}

void Collect::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if(
		input == contextValuesPlug() ||
		input == contextVariablePlug() ||
		input == indexContextVariablePlug() ||
		input == enabledPlug() ||
		inPlug()->isAncestorOf( input )
	)
	{
		outputs.push_back( collectionPlug() );
	}

	if( input == collectionPlug() )
	{
		outputs.push_back( enabledValuesPlug() );
		for( auto output : Plug::OutputRange( *outPlug() ) )
		{
			outputs.push_back( output.get() );
		}
	}
}

void Collect::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( output == collectionPlug() )
	{
		ConstStringVectorDataPtr contextValuesData = contextValuesPlug()->getValue();
		const vector<string> &contextValues = contextValuesData->readable();
		const InternedString contextVariable = contextVariablePlug()->getValue();
		const InternedString indexContextVariable = indexContextVariablePlug()->getValue();

		for( auto &input : ValuePlug::Range( *inPlug() ) )
		{
			h.append( input->typeId() );
			h.append( input->getName() );
		}

		const ThreadState &threadState = ThreadState::current();
		tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );

		const IECore::MurmurHash reduction = tbb::parallel_deterministic_reduce(

			IntRange( 0, contextValues.size() ),
			MurmurHash(),

			[&] ( const IntRange &range, MurmurHash hash )
			{
				Context::EditableScope scope( threadState );
				for( int index = range.begin(); index < range.end(); ++index )
				{
					scope.set( contextVariable, &contextValues[index] );
					scope.set( indexContextVariable, &index );
					hash.append( contextValues[index] );
					enabledPlug()->hash( hash );
					for( auto &input : ValuePlug::Range( *inPlug() ) )
					{
						input->hash( hash );
					}
				}
				return hash;
			},

			[] ( MurmurHash x, const MurmurHash &y ) {
				x.append( y );
				return x;
			},

			simple_partitioner(),
			taskGroupContext
		);

		h.append( reduction );
	}
	else if( output->parent() == outPlug() || output == enabledValuesPlug() )
	{
		collectionPlug()->hash( h );
	}
}

void Collect::compute( ValuePlug *output, const Context *context) const
{
	ComputeNode::compute( output, context );

	if( output == collectionPlug() )
	{
		ConstStringVectorDataPtr contextValuesData = contextValuesPlug()->getValue();
		const vector<string> &contextValues = contextValuesData->readable();
		const InternedString contextVariable = contextVariablePlug()->getValue();
		const InternedString indexContextVariable = indexContextVariablePlug()->getValue();

		// Allocate storage to collect into.

		vector<pair<const ValuePlug *, Object *>> toCollect;

		UCharVectorDataPtr enabledData = new UCharVectorData;
		enabledData->writable().resize( contextValues.size() );
		toCollect.push_back( { enabledPlug(), enabledData.get() } );

		CompoundObjectPtr result = new CompoundObject;
		for( auto &input : ValuePlug::Range( *inPlug() ) )
		{
			dispatchPlugFunction(
				input.get(),
				[&] ( auto *plug ) {
					using OutputTraits = OutputTraits<remove_const_t<remove_pointer_t<decltype( plug )>>>;
					typename OutputTraits::ObjectType::Ptr object = new typename OutputTraits::ObjectType;
					OutputTraits::container( *object ).resize( contextValues.size() );
					toCollect.push_back( { input.get(), object.get() } );
					result->members()[input->getName()] = object;
				}
			);
		}

		// Perform collection in parallel.

		const ThreadState &threadState = ThreadState::current();
		tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );

		tbb::parallel_for(
			IntRange( 0, contextValues.size() ),
			[&] ( const IntRange &range )
			{
				Context::EditableScope scope( threadState );
				for( int index = range.begin(); index < range.end(); ++index )
				{
					scope.set( contextVariable, &contextValues[index] );
					scope.set( indexContextVariable, &index );

					for( auto [input, object] : toCollect )
					{
						dispatchPlugFunction(
							input,
							[&, object=object] ( auto *plug ) {
								using OutputTraits = OutputTraits<remove_const_t<remove_pointer_t<decltype( plug )>>>;
								auto typedObject = static_cast<typename OutputTraits::ObjectType *>( object );
								OutputTraits::container( *typedObject )[index] = OutputTraits::collect( plug );
							}
						);
					}
				}
			},
			taskGroupContext
		);

		// Add context values and filter.

		result->members()[g_enabledOutputs] = contextValuesData->copy();
		filterVectors( result.get(), enabledData->readable() );

		static_cast<CompoundObjectPlug *>( output )->setValue( result );
	}
	else if( output->parent() == outPlug() )
	{
		ConstCompoundObjectPtr collection = collectionPlug()->getValue();
		const ValuePlug *input = inputPlugForOutput( output );

		dispatchPlugFunction(
			input,
			[&] ( auto *plug ) {

				using OutputTraits = OutputTraits<remove_const_t<remove_pointer_t<decltype( plug )>>>;
				auto object = collection->member<typename OutputTraits::PlugType::ValueType>( output->getName(), true );
				static_cast<typename OutputTraits::PlugType *>( output )->setValue( object );
			}
		);
	}
	else if( output == enabledValuesPlug() )
	{
		ConstCompoundObjectPtr collection = collectionPlug()->getValue();
		static_cast<ObjectPlug *>( output )->setValue( collection->member<StringVectorData>( g_enabledOutputs, /* throwExceptions = */ true ) );
	}
}

ValuePlug::CachePolicy Collect::hashCachePolicy( const ValuePlug *output ) const
{
	if( output == collectionPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return ComputeNode::hashCachePolicy( output );
}

ValuePlug::CachePolicy Collect::computeCachePolicy( const ValuePlug *output ) const
{
	if( output == collectionPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return ComputeNode::computeCachePolicy( output );
}

void Collect::inputAdded( GraphComponent *input )
{
	m_inputNameChangedConnections[input] = input->nameChangedSignal().connect( boost::bind( &Collect::inputNameChanged, this, ::_1, ::_2 ) );
}

void Collect::inputRemoved( GraphComponent *input )
{
	m_inputNameChangedConnections.erase( input );
}

void Collect::inputNameChanged( GraphComponent *input, IECore::InternedString oldName )
{
	if( input->parent() == inPlug() )
	{
		if( auto out = outPlug()->getChild( oldName ) )
		{
			out->setName( input->getName() );
		}
	}
}
