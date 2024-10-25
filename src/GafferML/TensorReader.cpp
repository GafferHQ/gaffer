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

#include "GafferML/TensorReader.h"

#include "ProtoBuf.h"

#include <fstream>

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferML;

namespace
{

template<typename DataType, typename RepeatedFieldType>
typename DataType::Ptr typedData( const std::string &rawData, const RepeatedFieldType &field )
{
	using ElementType = typename DataType::ValueType::value_type;
	typename DataType::Ptr result = new DataType;
	if( field.size() )
	{
		result->writable().insert( result->writable().end(), field.begin(), field.end() );
	}
	else
	{
		result->writable().insert(
			result->writable().end(),
			reinterpret_cast<const ElementType *>( rawData.data() ),
			reinterpret_cast<const ElementType *>( rawData.data() + rawData.size() )
		);
	}
	return result;
}

} // namespace

GAFFER_NODE_DEFINE_TYPE( TensorReader );

size_t TensorReader::g_firstPlugIndex = 0;

TensorReader::TensorReader( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "fileName" ) );
	addChild( new TensorPlug( "tensor", Plug::Out ) );
}

TensorReader::~TensorReader()
{
}

Gaffer::StringPlug *TensorReader::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *TensorReader::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

TensorPlug *TensorReader::tensorPlug()
{
	return getChild<TensorPlug>( g_firstPlugIndex + 1 );
}

const TensorPlug *TensorReader::tensorPlug() const
{
	return getChild<TensorPlug>( g_firstPlugIndex + 1 );
}

void TensorReader::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input == fileNamePlug() )
	{
		outputs.push_back( tensorPlug() );
	}
}

void TensorReader::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == tensorPlug() )
	{
		ComputeNode::hash( output, context, h );
		fileNamePlug()->hash( h );
	}
	else
	{
		ComputeNode::hash( output, context, h );
	}
}

void TensorReader::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == tensorPlug() )
	{
		ConstTensorPtr tensor;
		const string fileName = fileNamePlug()->getValue();
		if( !fileName.empty() )
		{
			fstream input( fileName, ios::in | ios::binary );

			onnx::TensorProto proto;
			if (!proto.ParseFromIstream( &input ) )
			{
				throw IECore::Exception(
					fmt::format( "Failed to parse \"{}\"", fileName )
				);
			}

			if( proto.external_data_size() )
			{
				throw IECore::Exception(
					fmt::format( "\"{}\" : external data not currently supported", fileName )
				);
			}

			std::vector<int64_t> shape( proto.dims().begin(), proto.dims().end() );

			const int32_t dataType = proto.data_type();
			switch( dataType )
			{
				case onnx::TensorProto::FLOAT : {
					tensor = new Tensor( typedData<FloatVectorData>( proto.raw_data(), proto.float_data() ), shape );
					break;
				}
				default :
					throw IECore::Exception(
						fmt::format( "\"{}\" : unsupported data type {}", fileName, dataType )
					);
			}
		}
		else
		{
			tensor = tensorPlug()->defaultValue();
		}
		static_cast<TensorPlug *>( output )->setValue( tensor );
	}

	ComputeNode::compute( output, context );
}

Gaffer::ValuePlug::CachePolicy TensorReader::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == tensorPlug() )
	{
		// We don't actually use TBB, but neither do we want to allow
		// duplicate computes to happen in parallel - better that everyone
		// waits for a single reader.
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return ComputeNode::computeCachePolicy( output );
}

