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

#include "onnxruntime_cxx_api.h"

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

Ort::Env &ortEnv()
{
	// TODO : FIGURE OUT THE THREADING SITUATION
	// TODO : SHARE THIS WITH EVERYTHING ELSE
	static Ort::Env g_env( ORT_LOGGING_LEVEL_WARNING, "Gaffer" );
	return g_env;
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
	addChild( new AtomicCompoundDataPlug( "__inference", Plug::Out ) );
}

Inference::~Inference()
{
}

void Inference::loadModel( const std::filesystem::path &model )
{
	/// \todo Would it be useful to have searchpaths?
	Ort::Session session( ortEnv(), model.c_str(), Ort::SessionOptions() );

	inPlug()->clearChildren();
	outPlug()->clearChildren();

	for( size_t i = 0; i < session.GetInputCount(); ++i )
	{
		if( session.GetInputTypeInfo( i ).GetONNXType() != ONNXType::ONNX_TYPE_TENSOR )
		{
			continue;
		}

		Ort::AllocatedStringPtr name = session.GetInputNameAllocated( i, Ort::AllocatorWithDefaultOptions() );
		inPlug()->addChild( new TensorPlug( std::string( name.get() ) ) );
	}

	for( size_t i = 0; i < session.GetOutputCount(); ++i )
	{
		if( session.GetOutputTypeInfo( i ).GetONNXType() != ONNXType::ONNX_TYPE_TENSOR )
		{
			continue;
		}

		Ort::AllocatedStringPtr name = session.GetOutputNameAllocated( i, Ort::AllocatorWithDefaultOptions() );
		outPlug()->addChild( new TensorPlug( std::string( name.get() ), Plug::Out ) );
	}

	/// TODO : WHEN DIFFERENT MODELS HAVE THE SAME INPUTS/OUTPUTS IT WOULD BE USEFUL
	/// TO BE ABLE TO SWAP THEM DYNAMICALLY, WITHOUT RELOADING THE MODEL. FOR INSTANCE,
	/// ALL THE STYLE TRANSFER MODELS HAVE THE SAME IO. IT ALSO SEEMS LIKELY THAT LOTS
	/// OF IMAGE PROCESSING MODELS WILL HAVE ONE INPUT AND ONE OUTPUT, AND IT's ANNOYING
	/// WHEN THE NAMES DON'T MATCH. CAN WE DO ANYTHING ABOUT THAT?
	///
	/// TODO : IT WOULD ALSO BE USEFUL TO BE ABLE TO QUERY THE REQUIRED DIMENSIONS OF INPUTS
	/// AUTOMATICALLY, AND USE IT TO DRIVE A RESIZE ON THE FLY>

	modelPlug()->setValue( model );
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

Gaffer::AtomicCompoundDataPlug *Inference::inferencePlug()
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 3);
}

const Gaffer::AtomicCompoundDataPlug *Inference::inferencePlug() const
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 3 );
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

		// TODO : ARE THESE REUSABLE? SHOULD WE CACHE THEM BY MODEL PATH???
		Ort::Session session( ortEnv(), model.c_str(), Ort::SessionOptions() );

		vector<const char *> inputNames;
		vector<ConstTensorDataPtr> inputOwners;
		vector<OrtValue *> inputs;
		for( auto &p : TensorPlug::InputRange( *inPlug() ) )
		{
			inputNames.push_back( p->getName().c_str() );
			inputOwners.push_back( p->getValue() );
			inputs.push_back( inputOwners.back()->value );
		}

		vector<const char *> outputNames;
		for( auto &p : TensorPlug::OutputRange( *outPlug() ) )
		{
			outputNames.push_back( p->getName().c_str() );
		}

		// TODO : WE REALLY WANT TO BE ABLE TO CANCEL THIS
		// LOOKS POSSIBLE VIA RUNOPTIONS, BUT IT ISN'T POLLED - WE'D
		// NEED TO CALL `SetTerminate()` SOMEHOW.

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

		CompoundDataPtr result = new CompoundData;
		for( size_t i = 0; i < outputs.size(); ++i )
		{
			result->writable()[outputNames[i]] = new TensorData( std::move( outputs[i] ) );
		}

		static_cast<AtomicCompoundDataPlug *>( output )->setValue( result );
	}
	else if( output->parent() == outPlug() )
	{
		ConstCompoundDataPtr inferenceData = inferencePlug()->getValue();
		static_cast<TensorPlug *>( output )->setValue( inferenceData->member<TensorData>( output->getName() ) );
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
