//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferML/Inference.h"

#include "Gaffer/Context.h"
#include "Gaffer/Metadata.h"

#include "IECore/SearchPath.h"
#include "IECore/StringAlgo.h"

#include "onnxruntime_cxx_api.h"

#include <mutex>
#include <condition_variable>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferML;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

Ort::Env &acquireEnv()
{
	static Ort::Env g_env( ORT_LOGGING_LEVEL_WARNING, "Gaffer" );
	return g_env;
}

// Constructing a session (loading a model) is relatively expensive,
// so we only ever create a single session per model. I can't find
// a reference for this in the docs, but `Session::Run()` is thread-safe
// and can be called concurrently by multiple clients :
//
// https://github.com/microsoft/onnxruntime/issues/114
Ort::Session &acquireSession( const std::string &fileName )
{
	static std::mutex g_mutex;
	static std::unordered_map<string, Ort::Session> g_map;
	lock_guard<mutex> lock( g_mutex );

	auto it = g_map.find( fileName );
	if( it != g_map.end() )
	{
		return it->second;
	}

	const char *sp = getenv( "GAFFERML_MODEL_PATHS" );
	IECore::SearchPath searchPath( sp ? sp : "" );

	/// \todo Convert SearchPath to deal in `std::filesystem` rather than `boost::filesystem`.
	std::filesystem::path path = searchPath.find( fileName ).string();
	if( path.empty() )
	{
		throw Exception( fmt::format( "Could not find file \"{}\" on GAFFERML_MODEL_PATHS", fileName ) );
	}

	it = g_map.try_emplace( fileName, acquireEnv(), path.c_str(), Ort::SessionOptions() ).first;
	return it->second;
}

struct AsyncWaiter
{

	AsyncWaiter( Ort::RunOptions &runOptions )
		:	m_runOptions( runOptions )
	{
	}

	void wait( const IECore::Canceller *canceller )
	{
		while( true )
		{
			std::unique_lock<std::mutex> lock( m_mutex );
			m_conditionVariable.wait_for( lock, std::chrono::milliseconds( 100 ) );

			if( m_resultStatus )
			{
				// Run has completed. Throw if it errored or was cancelled,
				// otherwise return.
				Ort::ThrowOnError( *m_resultStatus );
				IECore::Canceller::check( canceller );
				return;
			}
			else if( canceller && canceller->cancelled() )
			{
				m_runOptions.SetTerminate();
			}
		}
	}

	static void callback( void *userData, OrtValue **outputs, size_t numOutputs, OrtStatusPtr status )
	{
		// Run has completed. Set status so we can pick it up in `wait()`.
		auto that = (AsyncWaiter *)userData;
		{
			std::unique_lock<std::mutex> lock( that->m_mutex );
			that->m_resultStatus = status;
		}
		that->m_conditionVariable.notify_all();
	}

	private :

		Ort::RunOptions &m_runOptions;
		std::mutex m_mutex;
		std::condition_variable m_conditionVariable;
		std::optional<OrtStatusPtr> m_resultStatus;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Inference
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Inference );

size_t Inference::g_firstPlugIndex = 0;

Inference::Inference( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "model" ) );
	addChild( new ArrayPlug( "in", Plug::In, new TensorPlug( "in0" ), 0, std::numeric_limits<size_t>::max(), Plug::Default, false ) );
	addChild( new ArrayPlug( "out", Plug::Out, new TensorPlug( "out0" ), 0, std::numeric_limits<size_t>::max(), Plug::Default, false ) );
	addChild( new CompoundObjectPlug( "__inference", Plug::Out ) );
}

Inference::~Inference()
{
}

void Inference::loadModel()
{
	Ort::Session &session = acquireSession( modelPlug()->getValue() );

	// Input and output names can contain characters like `.` that cannot be
	// used in plug names. Furthermore, many models have inputs and outputs
	// which are interchangeable other than trivial differences in naming. So
	// instead of using the names as plug names, we store inputs and outputs as
	// ArrayPlugs, where only index matters. Then we add label metadata using
	// the true name, to make the UI a little more helpful.

	size_t numInputs = 0;
	for( size_t i = 0; i < session.GetInputCount(); ++i )
	{
		if( session.GetInputTypeInfo( i ).GetONNXType() != ONNXType::ONNX_TYPE_TENSOR )
		{
			continue;
		}

		numInputs++;
		inPlug()->resize( std::max( inPlug()->children().size(), numInputs ) ); // Add new plug if needed.

		Ort::AllocatedStringPtr ortName = session.GetInputNameAllocated( i, Ort::AllocatorWithDefaultOptions() );
		IECore::ConstStringDataPtr label = new StringData( ortName.get() );
		Metadata::registerValue( inPlug()->getChild( i ), "label", label );
		Metadata::registerValue( inPlug()->getChild( i ), "noduleLayout:label", label );
	}
	inPlug()->resize( numInputs ); // Remove old plugs we don't need.

	size_t numOutputs = 0;
	for( size_t i = 0; i < session.GetOutputCount(); ++i )
	{
		if( session.GetOutputTypeInfo( i ).GetONNXType() != ONNXType::ONNX_TYPE_TENSOR )
		{
			continue;
		}

		numOutputs++;
		outPlug()->resize( std::max( outPlug()->children().size(), numOutputs ) );

		Ort::AllocatedStringPtr ortName = session.GetOutputNameAllocated( i, Ort::AllocatorWithDefaultOptions() );
		IECore::ConstStringDataPtr label = new StringData( ortName.get() );
		Metadata::registerValue( outPlug()->getChild( i ), "label", label );
		Metadata::registerValue( outPlug()->getChild( i ), "noduleLayout:label", label );
	}
	outPlug()->resize( numOutputs );
}

Gaffer::StringPlug *Inference::modelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Inference::modelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::ArrayPlug *Inference::inPlug()
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::ArrayPlug *Inference::inPlug() const
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 1 );
}

Gaffer::ArrayPlug *Inference::outPlug()
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::ArrayPlug *Inference::outPlug() const
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 2 );
}

Gaffer::CompoundObjectPlug *Inference::inferencePlug()
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 3);
}

const Gaffer::CompoundObjectPlug *Inference::inferencePlug() const
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 3 );
}

void Inference::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if(
		input == modelPlug() ||
		input->parent() == inPlug()
	)
	{
		outputs.push_back( inferencePlug() );
	}

	if( input == inferencePlug() )
	{
		for( auto p : Gaffer::ValuePlug::Range( *outPlug() ) )
		{
			outputs.push_back( p.get() );
		}
	}
}

void Inference::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == inferencePlug() )
	{
		ComputeNode::hash( output, context, h );
		modelPlug()->hash( h );
		for( auto &p : TensorPlug::InputRange( *inPlug() ) )
		{
			p->hash( h );
		}
	}
	else if( output->parent() == outPlug() )
	{
		ComputeNode::hash( output, context, h );
		inferencePlug()->hash( h );
	}
	else
	{
		ComputeNode::hash( output, context, h );
	}
}

void Inference::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == inferencePlug() )
	{
		// Set up input and output tensor arrays.

		const string model = modelPlug()->getValue();
		Ort::Session &session = acquireSession( model );

		vector<Ort::AllocatedStringPtr> inputNameOwners;
		vector<const char *> inputNames;
		vector<ConstTensorPtr> inputOwners;
		vector<OrtValue *> inputs;

		for( auto &p : TensorPlug::InputRange( *inPlug() ) )
		{
			int inputIndex = StringAlgo::numericSuffix( p->getName().string() );
			inputNameOwners.push_back( session.GetInputNameAllocated( inputIndex, Ort::AllocatorWithDefaultOptions() ) );
			inputNames.push_back( inputNameOwners.back().get() );
			inputOwners.push_back( p->getValue() );
			inputs.push_back( inputOwners.back()->value() );
		}

		vector<Ort::AllocatedStringPtr> outputNameOwners;
		vector<const char *> outputNames;
		vector<Ort::Value> outputs;
		for( auto &p : TensorPlug::OutputRange( *outPlug() ) )
		{
			int outputIndex = StringAlgo::numericSuffix( p->getName().string() );
			outputNameOwners.push_back( session.GetOutputNameAllocated( outputIndex, Ort::AllocatorWithDefaultOptions() ) );
			outputNames.push_back( outputNameOwners.back().get() );
			outputs.push_back( Ort::Value( nullptr ) );
		}

		// Run inference asynchronously on an ONNX thread. This allows us
		// to check for cancellation via our AsyncWaiter.

		Ort::RunOptions runOptions;
		AsyncWaiter waiter( runOptions );

		session.RunAsync(
			runOptions, inputNames.data(),
			// The Ort C++ API wants us to pass `Ort::Value *`, but `Ort::Value`
			// is non-copyable and the original `Ort::Value` instances are in
			// separate TensorDatas and can't be moved. But `Ort::Value` has the
			// same layout as `OrtValue *` (the underlying C type) so we can
			// just reinterpret cast from the latter. Indeed, `Run()` is going
			// to cast straight back to `OrtValue *` to call the C API!
			reinterpret_cast<Ort::Value *>( inputs.data() ),
			inputs.size(),
			outputNames.data(),
			outputs.data(),
			outputNames.size(),
			waiter.callback,
			&waiter
		);

		waiter.wait( context->canceller() );

		CompoundObjectPtr result = new CompoundObject;
		for( size_t i = 0; i < outputs.size(); ++i )
		{
			result->members()[outPlug()->children()[i]->getName()] = new Tensor( std::move( outputs[i] ) );
		}

		static_cast<CompoundObjectPlug *>( output )->setValue( result );
	}
	else if( output->parent() == outPlug() )
	{
		ConstCompoundObjectPtr inferenceData = inferencePlug()->getValue();
		static_cast<TensorPlug *>( output )->setValue( inferenceData->member<Tensor>( output->getName() ) );
	}
	else
	{
		ComputeNode::compute( output, context );
	}
}

Gaffer::ValuePlug::CachePolicy Inference::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == inferencePlug() )
	{
		// We're not actually capable of task collaboration, because all the work is done by ONNX
		// on its own threads. But we use the TaskCollaboration policy to avoid concurrent computes
		// of the same thing, which would be incredibly wasteful.
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	else if( output->parent() == outPlug() )
	{
		// We're just going to reference data that is already cached in
		// `inferencePlug()`. Avoid double-counting of cache memory by not
		// caching again (the compute is fast enough that we don't care anyway).
		return ValuePlug::CachePolicy::Uncached;
	}
	return ComputeNode::computeCachePolicy( output );
}
