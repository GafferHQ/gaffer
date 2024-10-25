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

#include "GafferML/DataToTensor.h"

#include "Gaffer/Context.h"

#include "onnxruntime_cxx_api.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferML;

GAFFER_NODE_DEFINE_TYPE( DataToTensor );

size_t DataToTensor::g_firstPlugIndex = 0;

DataToTensor::DataToTensor( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new FloatVectorDataPlug( "data" ) );
	addChild( new Int64VectorDataPlug( "shape" ) );
	addChild( new TensorPlug( "tensor", Plug::Out ) );
}

DataToTensor::~DataToTensor()
{
}

Gaffer::FloatVectorDataPlug *DataToTensor::dataPlug()
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex );
}

const Gaffer::FloatVectorDataPlug *DataToTensor::dataPlug() const
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex );
}

Gaffer::Int64VectorDataPlug *DataToTensor::shapePlug()
{
	return getChild<Int64VectorDataPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::Int64VectorDataPlug *DataToTensor::shapePlug() const
{
	return getChild<Int64VectorDataPlug>( g_firstPlugIndex + 1 );
}

TensorPlug *DataToTensor::tensorPlug()
{
	return getChild<TensorPlug>( g_firstPlugIndex + 2 );
}

const TensorPlug *DataToTensor::tensorPlug() const
{
	return getChild<TensorPlug>( g_firstPlugIndex + 2 );
}

void DataToTensor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if(
		input == dataPlug() ||
		input == shapePlug()
	)
	{
		outputs.push_back( tensorPlug() );
	}
}

void DataToTensor::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == tensorPlug() )
	{
		ComputeNode::hash( output, context, h );
		dataPlug()->hash( h );
		shapePlug()->hash( h );
	}
	else
	{
		ComputeNode::hash( output, context, h );
	}
}

void DataToTensor::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == tensorPlug() )
	{
		ConstFloatVectorDataPtr bufferData = dataPlug()->getValue();
		ConstInt64VectorDataPtr shapeData = shapePlug()->getValue();
		ConstTensorPtr tensorData = new Tensor( bufferData, shapeData->readable() );
		static_cast<TensorPlug *>( output )->setValue( tensorData );
	}

	ComputeNode::compute( output, context );
}

Gaffer::ValuePlug::CachePolicy DataToTensor::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == tensorPlug() )
	{
		// Tensors can be really big. Prevent concurrent creation of identical
		// tensors that could cause a memory spike before the cache deduplicates
		// them.
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return ComputeNode::computeCachePolicy( output );
}

