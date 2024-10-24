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

#include "GafferML/Inference.h"

#include "Gaffer/Context.h"
#include "Gaffer/Metadata.h"

#include "IECore/StringAlgo.h"

#include "boost/algorithm/string/replace.hpp"

#include "onnxruntime_cxx_api.h"

#include <mutex>

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
	// TODO : FIGURE OUT THE THREADING SITUATION
	// TODO : SHARE THIS WITH EVERYTHING ELSE
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
	if( it == g_map.end() )
	{
		/// \todo Would it be useful to have searchpaths?
		it = g_map.try_emplace( fileName, acquireEnv(), fileName.c_str(), Ort::SessionOptions() ).first;
	}

	return it->second;
}

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
	addChild( new ValuePlug( "in" ) );
	addChild( new ValuePlug( "out", Plug::Out ) );
	addChild( new CompoundObjectPlug( "__inference", Plug::Out ) );
}

Inference::~Inference()
{
}

void Inference::loadModel()
{
	Ort::Session &session = acquireSession( modelPlug()->getValue() );

	/// \todo Keep existing plugs where possible

	inPlug()->clearChildren();
	outPlug()->clearChildren();

	for( size_t i = 0; i < session.GetInputCount(); ++i )
	{
		if( session.GetInputTypeInfo( i ).GetONNXType() != ONNXType::ONNX_TYPE_TENSOR )
		{
			continue;
		}

		// Input names can contain characters like `.` that cannot be used in
		// plug names. Furthermore, many models have inputs and outputs which
		// are interchangeable other than trivial differences in naming. So we
		// use standard numeric names for all inputs instead of the true names.
		TensorPlugPtr in = new TensorPlug( fmt::format( "in{}", i ), Plug::In, new Tensor(), Plug::Default | Plug::Dynamic );
		inPlug()->addChild( in );
		// We instead use the true name as a metadata label to make the UI
		// potentially a little more friendly.
		Ort::AllocatedStringPtr ortName = session.GetInputNameAllocated( i, Ort::AllocatorWithDefaultOptions() );
		IECore::ConstStringDataPtr label = new StringData( ortName.get() );
		Metadata::registerValue( in.get(), "label", label );
		Metadata::registerValue( in.get(), "noduleLayout:label", label );
	}

	for( size_t i = 0; i < session.GetOutputCount(); ++i )
	{
		if( session.GetOutputTypeInfo( i ).GetONNXType() != ONNXType::ONNX_TYPE_TENSOR )
		{
			continue;
		}

		// As above, we use standard numeric names for plugs, and register
		// the true names as metadata labels.
		TensorPlugPtr out = new TensorPlug( fmt::format( "out{}", i ), Plug::Out, new Tensor(), Plug::Default | Plug::Dynamic );
		outPlug()->addChild( out );

		Ort::AllocatedStringPtr ortName = session.GetOutputNameAllocated( i, Ort::AllocatorWithDefaultOptions() );
		IECore::ConstStringDataPtr label = new StringData( ortName.get() );
		Metadata::registerValue( out.get(), "label", label );
		Metadata::registerValue( out.get(), "noduleLayout:label", label );
	}
}

Gaffer::StringPlug *Inference::modelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Inference::modelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::ValuePlug *Inference::inPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 1 );
}

const Gaffer::ValuePlug *Inference::inPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 1 );
}

Gaffer::ValuePlug *Inference::outPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 2 );
}

const Gaffer::ValuePlug *Inference::outPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 2 );
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

	if( input->parent() == inPlug() )
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
		inPlug()->hash( h );
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
			inputs.push_back( inputOwners.back()->value );
		}

		vector<Ort::AllocatedStringPtr> outputNameOwners;
		vector<const char *> outputNames;
		for( auto &p : TensorPlug::OutputRange( *outPlug() ) )
		{
			int outputIndex = StringAlgo::numericSuffix( p->getName().string() );
			outputNameOwners.push_back( session.GetOutputNameAllocated( outputIndex, Ort::AllocatorWithDefaultOptions() ) );
			outputNames.push_back( outputNameOwners.back().get() );
		}

		// TODO : WE REALLY WANT TO BE ABLE TO CANCEL THIS
		// LOOKS POSSIBLE VIA RUNOPTIONS, BUT IT ISN'T POLLED - WE'D
		// NEED TO CALL `SetTerminate()` SOMEHOW.
		// MAYBE WE CAN USE `RunAsync()`?

		vector<Ort::Value> outputs = session.Run(
			Ort::RunOptions(), inputNames.data(),
			// The Ort C++ API wants us to pass `Ort::Value *`, but `Ort::Value`
			// is non-copyable and the original `Ort::Value` instances are in
			// separate TensorDatas and can't be moved. But `Ort::Value` has the
			// same layout as `OrtValue *` (the underlying C type) so we can
			// just reinterpret cast from the latter. Indeed, `Run()` is going
			// to cast straight back to `OrtValue *` to call the C API!
			reinterpret_cast<Ort::Value *>( inputs.data() ),
			inputs.size(), outputNames.data(), outputNames.size()
		);

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
		// WE WANT TO DO THIS JUST TO AVOID PARALLEL WORK, EVEN IF WE'RE NOT USING TBB.
		// TODO : BUT WHAT _ARE_ WE USING BEHIND THE SCENES?
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
