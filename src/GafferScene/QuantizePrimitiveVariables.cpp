//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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
//      * Neither the name of Image Engine Design Inc nor the names of
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

#include "GafferScene/QuantizePrimitiveVariables.h"

#include "IECore/DataAlgo.h"
#include "IECore/TypeTraits.h"

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

// Quantization logic copied from Instancer.cpp.

template<typename T>
inline T quantize( T v, float q )
{
	if( q == 0.0f )
	{
		return v;
	}

	if( std::is_integral_v<T> )
	{
		T intQuantize = round( q );
		if( intQuantize == 0 )
		{
			return v;
		}
		T halfQuantize = intQuantize / 2;
		return intQuantize * ( ( v + halfQuantize ) / intQuantize );
	}
	else
	{
		T r = q * round( v / q );
		// Convert negative zero to zero.
		if( r == 0 )
		{
			r = 0;
		}
		return r;
	}
}

} // namespace

GAFFER_NODE_DEFINE_TYPE( QuantizePrimitiveVariables );

size_t QuantizePrimitiveVariables::g_firstPlugIndex = 0;

QuantizePrimitiveVariables::QuantizePrimitiveVariables( const std::string &name ) : PrimitiveVariableProcessor( name, IECore::PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new FloatPlug( "quantization", Plug::In, 0, 0 ) );
}

QuantizePrimitiveVariables::~QuantizePrimitiveVariables()
{
}

Gaffer::FloatPlug *QuantizePrimitiveVariables::quantizationPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex );
}

const Gaffer::FloatPlug *QuantizePrimitiveVariables::quantizationPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex );
}

void QuantizePrimitiveVariables::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	PrimitiveVariableProcessor::affects( input, outputs );

	if( input == quantizationPlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

void QuantizePrimitiveVariables::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const float q = quantizationPlug()->getValue();
	if( q == 0.0f )
	{
		h = inPlug()->objectPlug()->hash();
	}
	else
	{
		PrimitiveVariableProcessor::hashProcessedObject( path, context, h );
		h.append( q );
	}
}

void QuantizePrimitiveVariables::processPrimitiveVariable( const ScenePath &path, const Gaffer::Context *context, IECoreScene::ConstPrimitivePtr inputGeometry, IECoreScene::PrimitiveVariable &variable ) const
{
	const float q = quantizationPlug()->getValue();
	if( q == 0.0f )
	{
		return;
	}

	dispatch(

		variable.data.get(),

		[&] ( auto *data ) -> void {

			using DataType = remove_const_t<remove_pointer_t<decltype( data )>>;

			if constexpr( TypeTraits::IsNumericBasedTypedData<DataType>::value )
			{
				/// \todo Thread using TBB. So we can deal with cache policies properly,
				/// this means rederiving PrimitiveVariableProcessor from ObjectProcessor.
				/// I'm not sure PrimitiveVariableProcessor is actually all that useful - it's
				/// kindof in the way right now.
				for( auto p = data->baseWritable(), e = data->baseWritable() + data->baseSize(); p < e; ++p )
				{
					*p = quantize( *p, q );
				}
			}

		}

	);
}
