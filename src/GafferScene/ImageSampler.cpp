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

#include <unordered_map>

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

OutputVariableFunction addPrimitiveVariable( Primitive *outputPrimitive, const std::string &name, const PrimitiveVariable::Interpolation outputInterpolation, int interpretation )
{
	const size_t size = outputPrimitive->variableSize( outputInterpolation );

	if( interpretation == GeometricData::Interpretation::Color )
	{
		Color3fVectorDataPtr data = getVariableData<Color3fVectorData>( outputPrimitive, name, outputInterpolation, size );
		Color3f *d = data->writable().data();
		return [ d ] ( size_t index, size_t subIndex, Sampler &s, float x, float y ) {
			d[index][subIndex] = s.sample( x, y );
		};
	}
	else if( interpretation == GeometricData::Interpretation::Normal )
	{
		V3fVectorDataPtr data = getVariableData<V3fVectorData>( outputPrimitive, name, outputInterpolation, size );
		data->setInterpretation( GeometricData::Interpretation::Normal );
		V3f *d = data->writable().data();
		return [ d ] ( size_t index, size_t subIndex, Sampler &s, float x, float y ) {
			d[index][subIndex] = s.sample( x, y );
		};
	}
	else if( interpretation == GeometricData::Interpretation::Point )
	{
		V3fVectorDataPtr data = getVariableData<V3fVectorData>( outputPrimitive, name, outputInterpolation, size );
		data->setInterpretation( GeometricData::Interpretation::Point );
		V3f *d = data->writable().data();
		return [ d ] ( size_t index, size_t subIndex, Sampler &s, float x, float y ) {
			d[index][subIndex] = s.sample( x, y );
		};
	}
	else if( interpretation == GeometricData::Interpretation::UV )
	{
		V2fVectorDataPtr data = getVariableData<V2fVectorData>( outputPrimitive, name, outputInterpolation, size );
		data->setInterpretation( GeometricData::Interpretation::UV );
		V2f *d = data->writable().data();
		return [ d ] ( size_t index, size_t subIndex, Sampler &s, float x, float y ) {
			d[index][subIndex] = s.sample( x, y );
		};
	}
	
	else if( interpretation == GeometricData::Interpretation::Vector )
	{
		V3fVectorDataPtr data = getVariableData<V3fVectorData>( outputPrimitive, name, outputInterpolation, size );
		data->setInterpretation( GeometricData::Interpretation::Vector );
		V3f *d = data->writable().data();
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
	addChild( new ValuePlug( "primitiveVariables" ) );
	addChild( new StringPlug( "uvSet", Gaffer::Plug::Direction::In, "uv" ) );
	addChild( 
		new IntPlug( "uvBoundsMode", 
			Gaffer::Plug::Direction::In, 
			GafferScene::ImageSampler::UVBoundsMode::Clamp,
			GafferScene::ImageSampler::UVBoundsMode::First,
			GafferScene::ImageSampler::UVBoundsMode::Last
		)
	);
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

Gaffer::ValuePlug *ImageSampler::primitiveVariablesPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 1 );
}

const Gaffer::ValuePlug *ImageSampler::primitiveVariablesPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 1 );
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

Gaffer::ValuePlug *ImageSampler::addPrimitiveVariableSampler( const std::string &name, const int &interpretation, const std::string &channels )
{
	ValuePlugPtr primitiveVariablePlug = new ValuePlug( "pprimitiveVariable1" );
	primitiveVariablePlug->setFlags( Plug::Dynamic, true );

	StringPlugPtr namePlug = new StringPlug( "name", Plug::In, name );
	namePlug->setFlags( Plug::Dynamic, true );
	primitiveVariablePlug->addChild( namePlug );

	BoolPlugPtr activePlug = new BoolPlug( "active", Plug::In, true );
	activePlug->setFlags( Plug::Dynamic, true );
	primitiveVariablePlug->addChild( activePlug );

	IntPlugPtr interpretationPlug = new IntPlug( "interpretation", Plug::In, interpretation );
	interpretationPlug->setFlags( Plug::Dynamic, true );
	primitiveVariablePlug->addChild( interpretationPlug );

	StringPlugPtr channelsPlug = new StringPlug( "channels", Plug::In, channels );
	channelsPlug->setFlags( Plug::Dynamic, true );
	primitiveVariablePlug->addChild( channelsPlug );

	primitiveVariablesPlug()->addChild( primitiveVariablePlug );

	return primitiveVariablePlug.get();
}

bool ImageSampler::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	bool val =
		Deformer::affectsProcessedObject( input ) ||
		input == imagePlug()->channelNamesPlug() ||
		input == imagePlug()->channelDataPlug() ||
		input == imagePlug()->formatPlug() ||
		input == imagePlug()->dataWindowPlug() ||
		primitiveVariablesPlug()->isAncestorOf( input ) ||
		input == uvVarNamePlug() ||
		input == uvBoundsModePlug() ||
		input == inPlug()->objectPlug()
	;
	return val;
}

void ImageSampler::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const std::string uvVarName = uvVarNamePlug()->getValue();
	const ValuePlug *p = primitiveVariablesPlug();

	if( !p->children().size() || uvVarName.empty() )
	{
		h = inPlug()->objectPlug()->hash();
	}
	else
	{
		Deformer::hashProcessedObject( path, context, h );

		p->hash( h );

		h.append( uvVarName );

		h.append( uvBoundsModePlug()->getValue() );

		inPlug()->objectPlug()->hash( h );

		imagePlug()->channelNamesPlug()->hash( h );
		imagePlug()->dataWindowPlug()->hash( h );
		imagePlug()->formatPlug()->hash( h );

		ConstStringVectorDataPtr inChannelNamesData = imagePlug()->channelNamesPlug()->getValue();
		const std::vector<std::string> inChannelNames = inChannelNamesData->readable();

		for( InputValuePlugIterator samplerIt( p ); !samplerIt.done(); ++samplerIt )
		{
			const ValuePlug *samplerPlug = samplerIt->get();

			if( samplerPlug->getChild<BoolPlug>( "active" )->getValue() )
			{
				const std::string channelNames = samplerPlug->getChild<StringPlug>( "channels" )->getValue();

				std::vector<std::string> channels;
				IECore::StringAlgo::tokenize( channelNames, ' ', channels );

				for( std::vector<std::string>::const_iterator it = channels.begin(), eIt = channels.end(); it != eIt; ++it )
				{
					std::vector<std::string>::const_iterator match = find( inChannelNames.begin(), inChannelNames.end(), *it );
					if( match != inChannelNames.end() )
					{
						Sampler s( imagePlug(), *it, imagePlug()->dataWindow() );
						s.hash( h );
					}
					else
					{
						throw IECore::Exception( "Channel \"" + *it + "\" does not exist in input image." );
					}
				}
			}
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
	
	const ValuePlug *p = primitiveVariablesPlug();
	const std::string uvVarName = uvVarNamePlug()->getValue();

	if( !p->children().size() || uvVarName.empty() )
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

	// For cache coherency of the Sampler we put the Sampler call in the inner loop
	// of the UV sampling loop. We create the OutputVariableFunction and Sampler once
	// and store them for later use. Samplers are addressed using the channel name,
	// OutputVariableFuncitons are referenced using "<primitive variable name>.<channel name>"
	std::unordered_map<std::string, Sampler> samplers;
	std::unordered_map<std::string, OutputVariableFunction> outputs;

	for( InputValuePlugIterator samplerIt( p ); !samplerIt.done(); ++samplerIt )
	{
		const ValuePlug *samplerPlug = samplerIt->get();

		if( samplerPlug->getChild<BoolPlug>( "active" )->getValue() )
		{
			const int interpretation = samplerPlug->getChild<IntPlug>( "interpretation" )->getValue();
			const std::string name = samplerPlug->getChild<StringPlug>( "name" )->getValue();

			const std::string channelNames = samplerPlug->getChild<StringPlug>( "channels" )->getValue();
			std::vector<std::string> channels;
			IECore::StringAlgo::tokenize( channelNames, ' ', channels );

			if( ( interpretation == GeometricData::Interpretation::Color && channels.size() != 3 ) ||
				( interpretation == GeometricData::Interpretation::Normal && channels.size() != 3 ) ||
				( interpretation == GeometricData::Interpretation::Point && channels.size() != 3 ) ||
				( interpretation == GeometricData::Interpretation::Vector && channels.size() != 3 )
				
			)
			{
				throw IECore::Exception( "Primitive variable \"" + name + "\" must sample three channels." );
			}

			else if( interpretation == GeometricData::Interpretation::UV && channels.size() != 2 )
			{
				throw IECore::Exception( "Primitive variable \"" + name + "\" must sample two channels." );
			}

			else if( interpretation == GeometricData::Interpretation::None && channels.size() != 1 )
			{
				throw IECore::Exception( "Primitive variable \"" + name + "\" must sample one channel." );
			}

			for( std::vector<std::string>::const_iterator it = channels.begin(), eIt = channels.end(); it != eIt; ++it )
			{
				std::vector<std::string>::const_iterator match = find( inChannelNames.begin(), inChannelNames.end(), *it );
				if( match != inChannelNames.end() )
				{
					if( auto o = addPrimitiveVariable( outputPrimitive.get(), name, interpolation, interpretation ) )
					{
						outputs.insert( { name + "." + *it, o } );
						if( samplers.find( *it ) == samplers.end() )
						{
							Sampler sampler = Sampler( imagePlug(), *it, displayWindow );
							samplers.insert( { *it, sampler } );
						}
					}
				}
				else
				{
					throw IECore::Exception( "Channel \"" + *it + "\" does not exist in input image." );
				}
			}
		}
	}

	const int uvBoundsMode = uvBoundsModePlug()->getValue();

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
		const V2f pixelPosition = uv * ( ( V2f )imageSize - V2f( 1.0f ) ) + V2f( 0.5f );
		OutputVariableFunction o;

		for( InputValuePlugIterator samplerIt( p ); !samplerIt.done(); ++samplerIt )
		{
			const ValuePlug *samplerPlug = samplerIt->get();

			if( samplerPlug->getChild<BoolPlug>( "active" )->getValue() )
			{
				const int interpretation = samplerPlug->getChild<IntPlug>( "interpretation" )->getValue();
				const std::string name = samplerPlug->getChild<StringPlug>( "name" )->getValue();

				const std::string channelNames = samplerPlug->getChild<StringPlug>( "channels" )->getValue();

				std::vector<std::string> channels;
				IECore::StringAlgo::tokenize( channelNames, ' ', channels );

				if( interpretation == GeometricData::Interpretation::Color ||
					interpretation == GeometricData::Interpretation::Normal ||
					interpretation == GeometricData::Interpretation::Point ||
					interpretation == GeometricData::Interpretation::Vector
				)
				{
					outputs.at( name + "." + channels[0] )( i, 0, samplers.at( channels[0] ), pixelPosition.x, pixelPosition.y );
					outputs.at( name + "." + channels[1] )( i, 1, samplers.at( channels[1] ), pixelPosition.x, pixelPosition.y );
					outputs.at( name + "." + channels[2] )( i, 2, samplers.at( channels[2] ), pixelPosition.x, pixelPosition.y );
				}

				else if( interpretation == GeometricData::Interpretation::UV )
				{
					outputs.at( name + "." + channels[0] )( i, 0, samplers.at( channels[0] ), pixelPosition.x, pixelPosition.y );
					outputs.at( name + "." + channels[1] )( i, 1, samplers.at( channels[1] ), pixelPosition.x, pixelPosition.y );
				}

				else if( interpretation == GeometricData::Interpretation::None )
				{
					outputs.at( name + "." + channels[0] )( i, 0, samplers.at( channels[0] ), pixelPosition.x, pixelPosition.y );
				}
			}
		}
	}

	return outputPrimitive;
}

bool ImageSampler::adjustBounds() const
{
	const ValuePlug *p = primitiveVariablesPlug();
	for( InputValuePlugIterator samplerIt( p ); !samplerIt.done(); ++samplerIt )
	{
		const ValuePlug *samplerPlug = samplerIt->get();

		if( samplerPlug->getChild<BoolPlug>( "active" )->getValue() )
		{
			const std::string name = samplerPlug->getChild<StringPlug>( "name" )->getValue();

			if( Deformer::adjustBounds() &&
				name == "P"
			)
			{
				return true;
			}
		}
	}
	return false;
}
