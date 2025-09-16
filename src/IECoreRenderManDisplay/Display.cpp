//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2010-2013, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "IECoreImage/DisplayDriver.h"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/StringAlgo.h"
#include "IECore/VectorTypedData.h"

#include "display/display.h"
#include "display/renderoutput.h"
#include "ndspy.h"

#include "fmt/format.h"

#include <vector>

using namespace std;
using namespace Imath;
using namespace IECore;

// Implementation of original RenderMan driver API, as used by RIS
// ===============================================================

/// \todo This code originated from `src/IECoreDelight/Display.cpp`, with modifications
/// to deal with RenderMan-specific issues. There's not much point in trying to recombine
/// them into a single driver, since RenderMan will be dropping this API when XPU
/// becomes the new RenderMan.

extern "C"
{

PtDspyError DspyImageOpen( PtDspyImageHandle *image, const char *driverName, const char *fileName, int width, int height, int paramcount, const UserParameter *parameters, int formatCount, PtDspyDevFormat *format, PtFlagStuff *flags )
{
	*image = nullptr;

	// Get channel names.

	vector<string> channels;

	for( int i = 0; i < formatCount; i++ )
	{
		// RenderMan gives us names in the following format :
		//
		// `<outputName>.<annoyingInteger>[.<channeName>]`
		//
		// Where `channelName` is lower case, or is omitted for single-channel
		// outputs. The `quicklyNoiseless` man-in-the-middle driver gives us
		// similar names but without the annoying integer in the middle.
		//
		// Parse this mess into a channel name conformant with the EXR/Gaffer
		// specification.

		vector<string> tokens;
		StringAlgo::tokenize( format[i].name, '.', tokens );
		if( tokens.size() == 2 && std::all_of( tokens[0].begin(), tokens[0].end(), [] ( unsigned char c ) { return std::isdigit( c ); } ) )
		{
			tokens.erase( tokens.begin() );
		}
		else if( tokens.size() > 1 && std::all_of( tokens[1].begin(), tokens[1].end(), [] ( unsigned char c ) { return std::isdigit( c ); } ) )
		{
			tokens.erase( tokens.begin() + 1 );
		}

		string layerName;
		string baseName;
		if( tokens.size() == 1 )
		{
			baseName = tokens[0];
		}
		else if( tokens.size() == 2 )
		{
			if( tokens[0] != "Ci" )
			{
				layerName = tokens[0];
			}
			baseName = tokens[1];
		}
		else
		{
			msg( Msg::Error, "Dspy::imageOpen",  fmt::format( "Unexpected format name \"{}\"", format[i].name ) );
			return PkDspyErrorBadParams;
		}

		if( baseName == "r" ) baseName = "R";
		if( baseName == "g" ) baseName = "G";
		if( baseName == "b" ) baseName = "B";
		if( baseName == "a" ) baseName = "A";
		if( baseName == "z" && layerName.empty() ) baseName = "Z";

		if( layerName.empty() )
		{
			channels.push_back( baseName );
		}
		else
		{
			channels.push_back( layerName + "." + baseName );
		}

		format[i].type = PkDspyFloat32 | PkDspyByteOrderNative;
	}

	// Process the parameter list. We use some of the parameters to help determine
	// the display and data windows, and the others we convert ready to passed to
	// `DisplayDriver::create()`.

	V2i originalSize( width, height );
	V2i origin( 0 );

	CompoundDataPtr convertedParameters = new CompoundData;

	for( int p = 0; p < paramcount; p++ )
	{
		if ( !strcmp( parameters[p].name, "OriginalSize" ) && parameters[p].vtype == (char)'i' && parameters[p].vcount == (char)2 && parameters[p].nbytes == (int) (parameters[p].vcount * sizeof(int)) )
		{
			originalSize.x = static_cast<const int *>(parameters[p].value)[0];
			originalSize.y = static_cast<const int *>(parameters[p].value)[1];
		}
		else if ( !strcmp( parameters[p].name, "origin" ) && parameters[p].vtype == (char)'i' && parameters[p].vcount == (char)2 && parameters[p].nbytes == (int)(parameters[p].vcount * sizeof(int)) )
		{
			origin.x = static_cast<const int *>(parameters[p].value)[0];
			origin.y = static_cast<const int *>(parameters[p].value)[1];
		}
		else
		{
			DataPtr newParam;

			if ( !parameters[p].nbytes )
			{
				continue;
			}

			const int *pInt;
			const float *pFloat;
			char const **pChar;

			// generic converter
			switch( parameters[p].vtype )
			{
			case 'i':
				// sanity check
				if ( parameters[p].nbytes / parameters[p].vcount != sizeof(int) )
				{
					msg( Msg::Error, "Dspy::imageOpen", "Invalid int data size" );
					continue;
				}
				pInt = static_cast<const int *>(parameters[p].value);
				if ( parameters[p].vcount == 1 )
				{
					newParam = new IntData( pInt[0] );
				}
				else
				{
					std::vector< int > newVec( pInt, pInt + parameters[p].vcount );
					newParam = new IntVectorData( newVec );
				}
				break;
			case 'f':
				if ( parameters[p].nbytes / parameters[p].vcount != sizeof(float) )
				{
					msg( Msg::Error, "Dspy::imageOpen", "Invalid float data size" );
					continue;
				}
				pFloat = static_cast<const float *>(parameters[p].value);
				if ( parameters[p].vcount == 1 )
				{
					newParam = new FloatData( pFloat[0] );
				}
				else
				{
					std::vector< float > newVec( pFloat, pFloat + parameters[p].vcount );
					newParam = new FloatVectorData( newVec );
				}
				break;
			case 's':
				pChar = (const char **)(parameters[p].value);
				if ( parameters[p].vcount == 1 )
				{
					newParam = new StringData( pChar[0] );
				}
				else
				{
					StringVectorDataPtr newStringVec = new StringVectorData();
					for ( int s = 0; s < parameters[p].vcount; s++ )
					{
						newStringVec->writable().push_back( pChar[s] );
					}
					newParam = newStringVec;
				}
				break;
			default :
				// We shouldn't ever get here...
				break;
			}
			if( newParam )
			{
				convertedParameters->writable()[ parameters[p].name ] = newParam;
			}
		}
	}

	convertedParameters->writable()[ "fileName" ] = new StringData( fileName );

	// Calculate display and data windows

	Box2i displayWindow(
		V2i( 0 ),
		originalSize - V2i( 1 )
	);

	Box2i dataWindow(
		origin,
		origin + V2i( width - 1, height - 1)
	);

	// Create the display driver

	IECoreImage::DisplayDriverPtr dd = nullptr;
	try
	{
		const StringData *driverType = convertedParameters->member<StringData>( "driverType", true /* throw if missing */ );
		dd = IECoreImage::DisplayDriver::create( driverType->readable(), displayWindow, dataWindow, channels, convertedParameters );
	}
	catch( std::exception &e )
	{
		msg( Msg::Error, "Dspy::imageOpen", e.what() );
		return PkDspyErrorUnsupported;
	}

	if( !dd )
	{
		msg( Msg::Error, "Dspy::imageOpen", "DisplayDriver::create returned 0." );
		return PkDspyErrorUnsupported;
	}

	// Update flags and return

	if( dd->scanLineOrderOnly() )
	{
		flags->flags |= PkDspyFlagsWantsScanLineOrder;
	}

	dd->addRef(); // This will be removed in imageClose()
	*image = (PtDspyImageHandle)dd.get();
	return PkDspyErrorNone;

}


PtDspyError DspyImageQuery( PtDspyImageHandle image, PtDspyQueryType type, int size, void *data )
{
	IECoreImage::DisplayDriver *dd = static_cast<IECoreImage::DisplayDriver *>( image );

	if( type == PkRedrawQuery )
	{
		if( (!dd->scanLineOrderOnly()) && dd->acceptsRepeatedData() )
		{
			((PtDspyRedrawInfo *)data)->redraw = 1;
		}
		else
		{
			((PtDspyRedrawInfo *)data)->redraw = 0;
		}
		return PkDspyErrorNone;
	}

	return PkDspyErrorUnsupported;
}

PtDspyError DspyImageData( PtDspyImageHandle image, int xMin, int xMaxPlusOne, int yMin, int yMaxPlusOne, int entrySize, const unsigned char *data )
{
	IECoreImage::DisplayDriver *dd = static_cast<IECoreImage::DisplayDriver *>( image );
	Box2i dataWindow = dd->dataWindow();

	// Convert coordinates from cropped image to original image coordinates.
	Box2i box( V2i( xMin + dataWindow.min.x, yMin + dataWindow.min.y ), V2i( xMaxPlusOne - 1 + dataWindow.min.x, yMaxPlusOne - 1 + dataWindow.min.y ) );
	int channels = dd->channelNames().size();
	int blockSize = (xMaxPlusOne - xMin) * (yMaxPlusOne - yMin);
	int bufferSize = channels * blockSize;

	if( entrySize % sizeof(float) )
	{
		msg( Msg::Error, "Dspy::imageData", "The entry size is not multiple of sizeof(float)!" );
		return PkDspyErrorUnsupported;
	}

	const float *buffer;
	vector<float> bufferStorage;

	/// \todo Integer ID support

	if( entrySize == (int)(channels*sizeof(float)) )
	{
		// This is the case we like - we can just send the data as-is.
		buffer = (const float *)data;
	}
	else
	{
		// PRMan seems to pad pixels sometimes for unknown reasons, and we need
		// to unpad them before sending. This is a pity.
		/// \todo Figure out why this is happening, and see if we can avoid it.
		bufferStorage.reserve( bufferSize );
		auto source = (const float *)data;
		const size_t stride = entrySize / sizeof( float );
		for( int i = 0; i < blockSize; ++i )
		{
			for( int c = 0; c < channels; ++c )
			{
				bufferStorage.push_back( source[c] );
			}
			source += stride;
		}
		buffer = bufferStorage.data();
	}

	try
	{
		dd->imageData( box, buffer, bufferSize );
	}
	catch( std::exception &e )
	{
		if( strcmp( e.what(), "stop" ) == 0 )
		{
			/// \todo Is this even used?
			return PkDspyErrorUndefined;
		}
		else
		{
			msg( Msg::Error, "Dspy::imageData", e.what() );
			return PkDspyErrorUndefined;
		}
	}

	return PkDspyErrorNone;
}

PtDspyError DspyImageClose( PtDspyImageHandle image )
{
	if ( !image )
	{
		return PkDspyErrorNone;
	}

	IECoreImage::DisplayDriver *dd = static_cast<IECoreImage::DisplayDriver*>( image );
	try
	{
		dd->imageClose();
	}
	catch( std::exception &e )
	{
		msg( Msg::Error, "Dspy::imageClose", e.what() );
	}

	try
	{
		dd->removeRef();
	}
	catch( std::exception &e )
	{
		msg( Msg::Error, "DspyImageData", e.what() );
		return PkDspyErrorBadParams;
	}

	return PkDspyErrorNone;
}

} // extern "C"

// Implementation of new driver API, as used by XPU
// ================================================

#if DISPLAY_INTERFACE_VERSION >= 2

namespace
{

template<typename T>
DataPtr typedParameterData( const pxrcore::ParamList &paramList, const pxrcore::ParamList::ParamInfo &paramInfo )
{
	unsigned paramId;
	paramList.GetParamId( paramInfo.name, paramId );
	const T *value = static_cast<const T *>( paramList.GetParam( paramId ) );
	if( !paramInfo.array )
	{
		return new TypedData<T>( *value );
	}
	else
	{
		return new TypedData<vector<T>>( vector<T>( value, value + paramInfo.length ) );
	}
}

template<>
DataPtr typedParameterData<string>( const pxrcore::ParamList &paramList, const pxrcore::ParamList::ParamInfo &paramInfo )
{
	unsigned paramId;
	paramList.GetParamId( paramInfo.name, paramId );
	const RtUString *value = static_cast<const RtUString *>( paramList.GetParam( paramId ) );
	if( !paramInfo.array )
	{
		return new StringData( value->CStr() );
	}
	else
	{
		StringVectorDataPtr result = new StringVectorData();
		result->writable().reserve( paramInfo.length );
		for( size_t i = 0; i < paramInfo.length; ++i )
		{
			result->writable().push_back( value[i].CStr() );
		}
		return result;
	}
}

struct IEDisplay : public display::Display
{

	IEDisplay( const pxrcore::ParamList &paramList, const pxrcore::ParamList &metadata )
		:	m_parameters( new CompoundData() )
	{
		// Convert parameter list into the form needed by `IECoreImage::DisplayDriver::create()`.
		pxrcore::ParamList::ParamInfo paramInfo;
		for( unsigned i = 0, n = paramList.GetNumParams(); i < n; ++i )
		{
			if( !paramList.GetParamInfo( i, paramInfo ) )
			{
				continue;
			}

			switch( paramInfo.type )
			{
				case pxrcore::DataType::k_string : {
					m_parameters->writable()[paramInfo.name.CStr()] = typedParameterData<string>( paramList, paramInfo );
					break;
				}
				case pxrcore::DataType::k_float :
					m_parameters->writable()[paramInfo.name.CStr()] = typedParameterData<float>( paramList, paramInfo );
					break;
				case pxrcore::DataType::k_integer :
					m_parameters->writable()[paramInfo.name.CStr()] = typedParameterData<int>( paramList, paramInfo );
					break;
				case pxrcore::DataType::k_color :
					m_parameters->writable()[paramInfo.name.CStr()] = typedParameterData<Imath::Color3f>( paramList, paramInfo );
					break;
				default :
					msg( Msg::Warning, "IEDisplay", fmt::format( "Ignoring parameter \"{}\" because it has an unsupported type ({})", paramInfo.name.CStr(), (int)paramInfo.type ) );
					break;
			}
		}
	}

	uint64_t GetRequirements() const override
	{
		return k_reqFrameBuffer;
	}

	bool Rebind(
		const uint32_t width, const uint32_t height, const char *srfaddrhandle,
		const void *srfaddr, const size_t srfsizebytes,
		const size_t *offsets,
		const size_t *sampleoffsets,
		const display::RenderOutput *outputs, const size_t noutputs
	) override
	{
		// Create an `IECoreImage::DisplayDriver` with the appropriate number of channels,
		// and fill `m_channelPointers` with the source data to copy each channel from in
		// `Notify()`.
		try
		{
			m_channelPointers.clear();

			if( m_driver )
			{
				m_driver->imageClose();
			}

			std::vector<std::string> channelNames;
			for( size_t outputIndex = 0; outputIndex < noutputs; ++outputIndex )
			{
				const display::RenderOutput &output = outputs[outputIndex];
				if( output.nelems == 1 )
				{
					std::string baseName = output.displayName.CStr();
					if( baseName == "a" ) baseName = "A";
					else if( baseName == "z" ) baseName = "Z";
					channelNames.push_back( baseName );
				}
				else
				{
					string layerName = output.displayName.CStr();
					if( layerName == "Ci" )
					{
						layerName = "";
					}
					for( uint8_t elementIndex = 0; elementIndex < output.nelems; elementIndex++ )
					{
						std::string baseName = output.displaySuffix[elementIndex].CStr();
						if( baseName == "r" ) baseName = "R";
						else if( baseName == "g" ) baseName = "G";
						else if( baseName == "b" ) baseName = "B";

						if( layerName.empty() )
						{
							channelNames.push_back( baseName );
						}
						else
						{
							channelNames.push_back( layerName + "." + baseName );
						}
					}
				}

				const float *channelPointer = reinterpret_cast<const float *>( static_cast<const std::byte *>( srfaddr ) + offsets[outputIndex] );
				for( size_t element = 0; element < output.nelems; ++element )
				{
					m_channelPointers.push_back( channelPointer );
					channelPointer += width * height;
				}
			}

			m_displayWindow = Box2i( V2i( 0 ), V2i( width - 1, height - 1 ) );
			m_dataWindow = m_displayWindow;
			if( const auto cropWindow = m_parameters->member<IntVectorData>( "CropWindow" ) )
			{
				m_dataWindow.min = V2i( cropWindow->readable()[0], cropWindow->readable()[1] );
				m_dataWindow.max = V2i( cropWindow->readable()[2], cropWindow->readable()[3] );
			}

			const StringData *driverType = m_parameters->member<StringData>( "driverType", /* throwIfMissing = */ true );
			m_driver = IECoreImage::DisplayDriver::create( driverType->readable(), m_displayWindow, m_dataWindow, channelNames, m_parameters );
		}
		catch( const std::exception &e )
		{
			IECore::msg( IECore::Msg::Error, "IEDisplay", e.what() );
			return false;
		}
		return true;
	}

	void Notify(
		const uint32_t iteration, const uint32_t totaliterations,
		const NotifyFlags flags, const pxrcore::ParamList &metadata
	) override
	{
		try
		{
			if( flags != k_notifyIteration && flags != k_notifyRender )
			{
				return;
			}

			const size_t width = m_dataWindow.size().x + 1;
			const size_t height = m_dataWindow.size().y + 1 ;
			const size_t numChannels = m_channelPointers.size();
			const size_t bufferSize = width * height *numChannels;
			const size_t offset = m_dataWindow.min.y * ( m_displayWindow.size().x + 1 ) + m_dataWindow.min.x;
			const size_t stride = m_displayWindow.size().x - m_dataWindow.size().x;

			std::unique_ptr<float[]> buffer( new float[bufferSize] );

			for( size_t channelIndex = 0; channelIndex < m_channelPointers.size(); ++channelIndex )
			{
				float *out = buffer.get() + channelIndex;
				const float *in = m_channelPointers[channelIndex] + offset;
				for( size_t y = 0; y < height; ++y )
				{
					for( size_t x = 0; x < width; ++x )
					{
						*out = *in++;
						out += numChannels;
					}
					in += stride;
				}
			}

			m_driver->imageData( m_dataWindow, buffer.get(), bufferSize );
		}
		catch( const std::exception &e )
		{
			IECore::msg( IECore::Msg::Error, "IEDisplay", e.what() );
		}
	}

	void Close() override
	{
		try
		{
			m_driver->imageClose();
			m_driver = nullptr;
		}
		catch( const std::exception &e )
		{
			IECore::msg( IECore::Msg::Error, "IEDisplay", e.what() );
		}
	}

	private :

		CompoundDataPtr m_parameters;
		Box2i m_displayWindow;
		Box2i m_dataWindow;
		IECoreImage::DisplayDriverPtr m_driver;
		vector<const float *> m_channelPointers;

};

} // namespace

// Factory

extern "C"
{

DISPLAYEXPORTVERSION

DISPLAYEXPORT display::Display *CreateDisplay( const pxrcore::UString &name, const pxrcore::ParamList &paramList, const pxrcore::ParamList &metadata )
{
	return new IEDisplay( paramList, metadata );
}

DISPLAYEXPORT void DestroyDisplay( const display::Display *d )
{
	delete d;
}

} // extern "C"

#endif // DISPLAY_INTERFACE_VERSION >= 2
