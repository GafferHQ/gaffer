//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Hypothetical Inc. All rights reserved.
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

#include "GafferScene/ImageSampler.h"

#include "GafferImage/Sampler.h"

#include "IECoreScene/Primitive.h"

using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

using OutputVariableFunction = std::function<void ( size_t, size_t, Sampler &, float, float )>;

template <typename T>
typename T::Ptr getVariableData( Primitive *outputPrimitive, const std::string &name, const PrimitiveVariable::Interpolation outputInterpolation, const size_t &size )
{
	auto it = outputPrimitive->variables.find( name );
	if( it == outputPrimitive->variables.end() || 
		it->second.data->typeId() != T::staticTypeId() ||
		it->second.interpolation != outputInterpolation
	)
	{
		typename T::Ptr data = new T();
		data->writable().resize( size );
		outputPrimitive->variables[name] = PrimitiveVariable( outputInterpolation, data );
		return data;
	}

	typename T::Ptr data = runTimeCast<T>( it->second.data );
	if( data->writable().size() != size )
	{
		data->writable().resize( size );
	}
	return data;
}

OutputVariableFunction addPrimitiveVariable( Primitive *outputPrimitive, const std::string &name, const PrimitiveVariable::Interpolation outputInterpolation )
{
	const size_t size = outputPrimitive->variableSize( outputInterpolation );

	if( name == "Cs" )
	{
		Color3fVectorDataPtr data = getVariableData<Color3fVectorData>( outputPrimitive, name, outputInterpolation, size );
		Color3f *d = data->writable().data();
		return [ d ] ( size_t index, size_t subIndex, Sampler &s, float x, float y ) {
			d[index][subIndex] = s.sample( x, y );
		};
	}
	else if( name == "N" )
	{
		V3fVectorDataPtr data = getVariableData<V3fVectorData>( outputPrimitive, name, outputInterpolation, size );
		data->setInterpretation( GeometricData::Interpretation::Normal );
		V3f *d = data->writable().data();
		return [ d ] ( size_t index, size_t subIndex, Sampler &s, float x, float y ) {
			d[index][subIndex] = s.sample( x, y );
		};
	}
	else if( name == "P" )
	{
		V3fVectorDataPtr data = getVariableData<V3fVectorData>( outputPrimitive, name, outputInterpolation, size );
		data->setInterpretation( GeometricData::Interpretation::Point );
		V3f *d = data->writable().data();
		return [ d ] ( size_t index, size_t subIndex, Sampler &s, float x, float y ) {
			d[index][subIndex] = s.sample( x, y );
		};
	}
	else if( name == "Pref" || name == "scale" || name == "velocity" )
	{
		V3fVectorDataPtr data = getVariableData<V3fVectorData>( outputPrimitive, name, outputInterpolation, size );
		data->setInterpretation( GeometricData::Interpretation::Vector );
		V3f *d = data->writable().data();
		return [ d ] ( size_t index, size_t subIndex, Sampler &s, float x, float y ) {
			d[index][subIndex] = s.sample( x, y );
		};
	}
	
	else if( name == "uv" )
	{
		V2fVectorDataPtr data = getVariableData<V2fVectorData>( outputPrimitive, name, outputInterpolation, size );
		data->setInterpretation( GeometricData::Interpretation::UV );
		V2f *d = data->writable().data();
		return [ d ] ( size_t index, size_t subIndex, Sampler &s, float x, float y ) {
			d[index][subIndex] = s.sample( x, y );
		};
	}
	else {
		FloatVectorDataPtr data = getVariableData<FloatVectorData>( outputPrimitive, name, outputInterpolation, size );
		float *d = data->writable().data();
		return [ d ] ( size_t index, size_t subIndex, Sampler &s, float x, float y ) {
			d[index] = s.sample( x, y );
		};
	}   
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Sampler
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( ImageSampler );

size_t ImageSampler::g_firstPlugIndex = 0;

ImageSampler::ImageSampler( const std::string &name )
	:	Deformer( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ImagePlug( "image" ) );
	addChild( new StringPlug( "primitiveVariable" ) );
	addChild( new StringPlug( "uvSet", Gaffer::Plug::Direction::In, "uv" ) );
	addChild( 
		new IntPlug( "uvBoundsMode", 
			Gaffer::Plug::Direction::In, 
			GafferScene::ImageSampler::UVBoundsMode::Clamp,
			GafferScene::ImageSampler::UVBoundsMode::First,
			GafferScene::ImageSampler::UVBoundsMode::Last
		)
	);
	addChild( new StringPlug( "channels" ) );
	
}

ImageSampler::~ImageSampler()
{
}

GafferImage::ImagePlug *ImageSampler::imagePlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const GafferImage::ImagePlug *ImageSampler::imagePlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *ImageSampler::primVarNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *ImageSampler::primVarNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *ImageSampler::uvVarNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *ImageSampler::uvVarNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::IntPlug *ImageSampler::uvBoundsModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::IntPlug *ImageSampler::uvBoundsModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *ImageSampler::channelsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *ImageSampler::channelsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

bool ImageSampler::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	bool val =
		Deformer::affectsProcessedObject( input ) ||
		input == imagePlug()->channelNamesPlug() ||
		input == imagePlug()->channelDataPlug() ||
		input == imagePlug()->dataWindowPlug() ||
		input == primVarNamePlug() ||
		input == uvVarNamePlug() ||
		input == uvBoundsModePlug() ||
		input == channelsPlug() ||
		input == inPlug()->objectPlug()
	;
	return val;
}

void ImageSampler::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Deformer::hashProcessedObject( path, context, h );

	const std::string channelNames = channelsPlug()->getValue();
	const std::string primVarName = primVarNamePlug()->getValue();
	const std::string uvVarName = uvVarNamePlug()->getValue();
	const int boundsMode = uvBoundsModePlug()->getValue();

	if( channelNames.empty() || primVarName.empty() || uvVarName.empty() )
	{
		return;
	}

	h.append( channelNames );
	h.append( primVarName );
	h.append( uvVarName );
	h.append( boundsMode );

	inPlug()->objectPlug()->hash( h );

	imagePlug()->channelNamesPlug()->hash( h );
	imagePlug()->dataWindowPlug()->hash( h );

	ConstStringVectorDataPtr inChannelNamesData = imagePlug()->channelNamesPlug()->getValue();
	const std::vector<std::string> inChannelNames = inChannelNamesData->readable();

	std::vector<std::string> channels;
	IECore::StringAlgo::tokenize(channelNames, ' ', channels);

	for( std::vector<std::string>::const_iterator it = channels.begin(), eIt = channels.end(); it != eIt; ++it )
	{
		std::vector<std::string>::const_iterator match = find(inChannelNames.begin(), inChannelNames.end(), *it);
		if( match != inChannelNames.end() )
		{
			Sampler s( imagePlug(), *it, imagePlug()->dataWindow() );
			s.hash( h );
		}
	}
}

IECore::ConstObjectPtr ImageSampler::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const Primitive *primitive = runTimeCast<const Primitive>( inputObject );
	if( !primitive )
	{
		return inputObject;
	}
	
	const std::string channelNames = channelsPlug()->getValue();
	const std::string primVarName = primVarNamePlug()->getValue();
	const std::string uvVarName = uvVarNamePlug()->getValue();

	if( channelNames.empty() || primVarName.empty() || uvVarName.empty() )
	{
		return inputObject;
	}

	PrimitivePtr outputPrimitive = primitive->copy();

	const auto uvVarNameIt = outputPrimitive->variables.find( uvVarName );
	if( uvVarNameIt == outputPrimitive->variables.end() )
	{
		throw IECore::Exception( "UV primitive variable \"" + uvVarName + "\" does not exist." );
	}

	PrimitiveVariable::IndexedView<V2f> uvView( uvVarNameIt->second );
	const PrimitiveVariable::Interpolation interpolation = uvVarNameIt->second.interpolation;

	ConstStringVectorDataPtr inChannelNamesData = imagePlug()->channelNamesPlug()->getValue();
	const std::vector<std::string> inChannelNames = inChannelNamesData->readable();

	const Imath::Box2i displayWindow = imagePlug()->format().getDisplayWindow();
	const Imath::V2i imageSize = displayWindow.size();
	const Imath::V2i imageMin = displayWindow.min;

	std::vector<std::string> channels;
	IECore::StringAlgo::tokenize( channelNames, ' ', channels );

	// TODO: Check for missing channels?

	if( ( primVarName == "Cs" && channels.size() != 3 ) ||
		( primVarName == "N" && channels.size() != 3 ) ||
		( primVarName == "P" && channels.size() != 3 ) ||
		( primVarName == "Pref" && channels.size() != 3 ) ||
		( primVarName == "scale" && channels.size() != 3 ) ||
		( primVarName == "velocity" && channels.size() != 3 )
		
	)
	{
		throw IECore::Exception( "Primitive variable \"" + primVarName + "\" must sample three channels." );
	}

	if( primVarName == "uv" && channels.size() != 2 )
	{
		throw IECore::Exception( "Primitive variable \"uv\" must sample two channels." );
	}

	if( primVarName == "width" && channels.size() != 1)
	{
		throw IECore::Exception( "Primitive variable \"width\" must sample one channels." );
	}

	std::vector<OutputVariableFunction> outputs;

	if( primVarName == "Cs" ||
		primVarName == "N" ||
		primVarName == "P" ||
		primVarName == "Pref" ||
		primVarName == "scale" ||
		primVarName == "uv" ||
		primVarName == "velocity" ||
		primVarName == "width"
	)
	{
		for( size_t i = 0; i < channels.size(); ++i )
		{
			if( auto o = addPrimitiveVariable( outputPrimitive.get(), primVarName, interpolation ) )
			{
				outputs.push_back( o );
			}
		}
	}
	else
	{
		for( size_t i = 0; i < channels.size(); ++i )
		{
			if( auto o = addPrimitiveVariable( outputPrimitive.get(), primVarName + "." + channels[i], interpolation ) )
			{
				outputs.push_back( o );
			}
		}
	}

	const int uvBoundsMode = uvBoundsModePlug()->getValue();

	for( size_t channelIndex = 0; channelIndex < outputs.size(); ++channelIndex )
	{
		Sampler sampler( imagePlug(), channels[channelIndex], displayWindow );
		const OutputVariableFunction &o = outputs[channelIndex];

		for( size_t i = 0; i < uvView.size(); ++i )
		{
			V2f uv = uvView[i];

			if( uv.x < 0 || uv.x > 1 )
			{
				switch( uvBoundsMode )
				{
					case UVBoundsMode::Clamp : 
						uv.x = std::max( std::min( uv.x, 1.f ), 0.f );
						break;
					case UVBoundsMode::Tile : 
						uv.x = abs( uv.x - floor( uv.x ) );
						break;
				}
			}

			if( uv.y < 0 || uv.y > 1 )
			{
				switch( uvBoundsMode )
				{
					case UVBoundsMode::Clamp : 
						uv.y = std::max( std::min( uv.y, 1.f ), 0.f );
						break;
					case UVBoundsMode::Tile : 
						uv.y = abs( uv.y - floor( uv.y ) );
						break;
				}
			}
			
			o(  i, 
				channelIndex, 
				sampler,
				( uv.x * ( ( float )imageSize.x - 1.0f ) + imageMin.x ) + 0.5f, 
				( uv.y * ( ( float )imageSize.y - 1.0f ) + imageMin.y ) + 0.5f
			);
		}
	}

	return outputPrimitive;
}

bool ImageSampler::adjustBounds() const
{
	return
		Deformer::adjustBounds() &&

		StringAlgo::matchMultiple( "P", primVarNamePlug()->getValue() )
	;
}
