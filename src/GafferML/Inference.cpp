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
	addChild( new TensorPlug( "in" ) );
	addChild( new TensorPlug( "out", Plug::Out ) );
}

Inference::~Inference()
{
}

Gaffer::StringPlug *Inference::modelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Inference::modelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

TensorPlug *Inference::inPlug()
{
	return getChild<TensorPlug>( g_firstPlugIndex + 1 );

}

const TensorPlug *Inference::inPlug() const
{
	return getChild<TensorPlug>( g_firstPlugIndex + 1 );

}

TensorPlug *Inference::outPlug()
{
	return getChild<TensorPlug>( g_firstPlugIndex + 2 );
}

const TensorPlug *Inference::outPlug() const
{
	return getChild<TensorPlug>( g_firstPlugIndex + 2 );
}

void Inference::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input == inPlug() || input == modelPlug() )
	{
		outputs.push_back( outPlug() );
	}
}

void Inference::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == outPlug() )
	{
		ComputeNode::hash( output, context, h );
		inPlug()->hash( h );
		modelPlug()->hash( h );
	}
	else
	{
		ComputeNode::hash( output, context, h );
	}
}

void Inference::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == outPlug() )
	{
		const string model = modelPlug()->getValue();

		// TODO : ARE THESE REUSABLE? SHOULD WE CACHE THEM BY MODEL PATH???
		Ort::Session session( ortEnv(), model.c_str(), Ort::SessionOptions() );

		ConstTensorDataPtr inputTensor = inPlug()->getValue();

		// TODO : WE REALLY WANT TO BE ABLE TO CANCEL THIS
		// LOOKS POSSIBLE VIA RUNOPTIONS, BUT IT ISN'T POLLED - WE'D
		// NEED TO CALL `SetTerminate()` SOMEHOW.

		/// TODO : VALIDATE

		const char *inputNames[] = { "inputImage" };
		const char *outputNames[] = { "outputImage" };
		vector<Ort::Value> outputs = session.Run( Ort::RunOptions(), inputNames, &inputTensor->value, 1, outputNames, 1 );

		static_cast<TensorPlug *>( output )->setValue( new TensorData( std::move( outputs[0] ) ) );

	}
	else
	{
		ComputeNode::compute( output, context );
	}
}

Gaffer::ValuePlug::CachePolicy Inference::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == outPlug() )
	{
		// WE WANT TO DO THIS JUST TO AVOID PARALLEL WORK, EVEN IF WE'RE NOT USING TBB.
		// TODO : BUT WHAT _ARE_ WE USING BEHIND THE SCENES?
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return ComputeNode::computeCachePolicy( output );
}
