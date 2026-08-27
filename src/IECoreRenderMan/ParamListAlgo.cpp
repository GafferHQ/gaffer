//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, John Haddon. All rights reserved.
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

#include "ParamListAlgo.h"

#include "IECore/DataAlgo.h"
#include "IECore/MessageHandler.h"

#include "fmt/format.h"

using namespace IECore;

//////////////////////////////////////////////////////////////////////////
// Internal Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

const bool g_legacyTextureCoordinates = [] () {
	const char *c = getenv( "IECORERENDERMAN_LEGACY_TEXTURECOORDINATE_BEHAVIOUR" );
	return c && !strcmp( c, "1" );
}();

struct ParameterConverter
{

	void operator()( const BoolData *data, RtUString name, RtParamList &paramList ) const
	{
		paramList.SetInteger( name, data->readable() );
	}

	void operator()( const IntData *data, RtUString name, RtParamList &paramList ) const
	{
		paramList.SetInteger( name, data->readable() );
	}

	void operator()( const FloatData *data, RtUString name, RtParamList &paramList ) const
	{
		paramList.SetFloat( name, data->readable() );
	}

	void operator()( const StringData *data, RtUString name, RtParamList &paramList ) const
	{
		paramList.SetString( name, RtUString( data->readable().c_str() ) );
	}

	void operator()( const InternedStringData *data, RtUString name, RtParamList &paramList ) const
	{
		paramList.SetString( name, RtUString( data->readable().c_str() ) );
	}

	void operator()( const Color3fData *data, RtUString name, RtParamList &paramList ) const
	{
		paramList.SetColor( name, RtColorRGB( data->readable().getValue() ) );
	}

	void operator()( const V2iData *data, RtUString name, RtParamList &paramList ) const
	{
		paramList.SetIntegerArray( name, data->readable().getValue(), 2 );
	}

	void operator()( const V2fData *data, RtUString name, RtParamList &paramList ) const
	{
		paramList.SetFloatArray( name, data->readable().getValue(), 2 );
	}

	void operator()( const V3fData *data, RtUString name, RtParamList &paramList ) const
	{
		const RtDataType type = IECoreRenderMan::ParamListAlgo::dataType( data->getInterpretation() );
		paramList.SetParam(
			{
				name, type, RtDetailType::k_constant,
				/* length = */ type == RtDataType::k_float ? 3u : 1u,
				/* array = */ type == RtDataType::k_float,
				/* motion = */ false,
				/* deduplicated = */ false
			},
			data->readable().getValue()
		);
	}

	void operator()( const M44fData *data, RtUString name, RtParamList &paramList ) const
	{
		paramList.SetMatrix( name, reinterpret_cast<const pxrcore::Matrix4x4 &>( data->readable() ) );
	}

	void operator()( const M44dData *data, RtUString name, RtParamList &paramList ) const
	{
		const Imath::M44f m( data->readable() );
		paramList.SetMatrix( name, pxrcore::Matrix4x4( m.x ) );
	}

	void operator()( const IntVectorData *data, RtUString name, RtParamList &paramList ) const
	{
		paramList.SetIntegerArray( name, data->readable().data(), data->readable().size() );
	}

	void operator()( const FloatVectorData *data, RtUString name, RtParamList &paramList ) const
	{
		paramList.SetFloatArray( name, data->readable().data(), data->readable().size() );
	}

	void operator()( const StringVectorData *data, RtUString name, RtParamList &paramList ) const
	{
		std::vector<RtUString> value; value.reserve( data->readable().size() );
		for( const auto &s : data->readable() )
		{
			value.push_back( RtUString( s.c_str() ) );
		}
		paramList.SetStringArray( name, value.data(), value.size() );
	}

	void operator()( const InternedStringVectorData *data, RtUString name, RtParamList &paramList ) const
	{
		std::vector<RtUString> value; value.reserve( data->readable().size() );
		for( const auto &s : data->readable() )
		{
			value.push_back( RtUString( s.c_str() ) );
		}
		paramList.SetStringArray( name, value.data(), value.size() );
	}

	void operator()( const Color3fVectorData *data, RtUString name, RtParamList &paramList ) const
	{
		paramList.SetColorArray( name, reinterpret_cast<const RtColorRGB *>( data->readable().data() ), data->readable().size() );
	}

	void operator()( const V3fVectorData *data, RtUString name, RtParamList &paramList ) const
	{
		const RtDataType type = IECoreRenderMan::ParamListAlgo::dataType( data->getInterpretation() );
		paramList.SetParam(
			{
				name, type, RtDetailType::k_constant,
				/* length = */ (uint32_t)data->readable().size() * (type == RtDataType::k_float ? 3 : 1),
				/* array = */ true,
				/* motion = */ false,
				/* deduplicated = */ false
			},
			data->readable().front().getValue()
		);
	}

	void operator()( const Data *data, RtUString name, RtParamList &paramList ) const
	{
		IECore::msg(
			IECore::Msg::Warning,
			"IECoreRenderMan",
			fmt::format( "Unsupported parameter \"{}\" of type \"{}\"", name.CStr(), data->typeName() )
		);
	}

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Public API
//////////////////////////////////////////////////////////////////////////

RtDataType IECoreRenderMan::ParamListAlgo::dataType( IECore::GeometricData::Interpretation interpretation )
{
	switch( interpretation )
	{
		case GeometricData::Vector :
			return RtDataType::k_vector;
		case GeometricData::Normal :
			return RtDataType::k_normal;
		case GeometricData::Point :
			return RtDataType::k_point;
		case GeometricData::UV :
			// This is what we end up with when loading `texCoord3f` from USD.
			// It should be treated as pure floats so that the values don't
			// get transformed at all, but at least one pipeline is dependent
			// on them being treated as points for use as `__Pref`.
			/// \todo Remove the legacy behaviour.
			return g_legacyTextureCoordinates ? RtDataType::k_point : RtDataType::k_float;
		default :
			return RtDataType::k_float;
	}
}

void IECoreRenderMan::ParamListAlgo::convertParameter( const RtUString &name, const Data *data, RtParamList &paramList )
{
	dispatch( data, ParameterConverter(), name, paramList );
}

void IECoreRenderMan::ParamListAlgo::convertParameters( const IECore::CompoundDataMap &parameters, RtParamList &paramList )
{
	for( auto &p : parameters )
	{
		convertParameter( RtUString( p.first.c_str() ), p.second.get(), paramList );
	}
}
