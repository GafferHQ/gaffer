//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

#include "IECore/SimpleTypedData.h"

#include "Gaffer/Context.h"

#include "GafferImage/ColorProcessor.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( ColorProcessor );

size_t ColorProcessor::g_firstPlugIndex = 0;

ColorProcessor::ColorProcessor( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild(
		new ObjectPlug(
			"__colorData",
			Gaffer::Plug::Out,
			new ObjectVector
		)
	);

	// Because our implementation of computeChannelData() is so simple,
	// just copying data out of our intermediate colorDataPlug(), it is
	// actually quicker not to cache the result.
	outPlug()->channelDataPlug()->setFlags( Plug::Cacheable, false );

	// We don't ever want to change the these, so we make pass-through connections.
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->deepStatePlug()->setInput( inPlug()->deepStatePlug() );
	outPlug()->sampleOffsetsPlug()->setInput( inPlug()->sampleOffsetsPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
}

ColorProcessor::~ColorProcessor()
{
}

Gaffer::ObjectPlug *ColorProcessor::colorDataPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex );
}

const Gaffer::ObjectPlug *ColorProcessor::colorDataPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex );
}

void ColorProcessor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	const ImagePlug *in = inPlug();
	if( affectsColorData( input ) )
	{
		outputs.push_back( colorDataPlug() );
	}
	else if( input == colorDataPlug()  )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if ( input->parent<ImagePlug>() == in && input != in->channelDataPlug() )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
}

void ColorProcessor::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hash( output, context, h );

	if( output == colorDataPlug() )
	{
		hashColorData( context, h );
	}
}

void ColorProcessor::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == colorDataPlug() )
	{
		FloatVectorDataPtr r, g, b;
		{
			ContextPtr tmpContext = new Context( *context, Context::Borrowed );
			Context::Scope scopedContext( tmpContext.get() );
			tmpContext->set( ImagePlug::channelNameContextName, string( "R" ) );
			r = inPlug()->channelDataPlug()->getValue()->copy();
			tmpContext->set( ImagePlug::channelNameContextName, string( "G" ) );
			g = inPlug()->channelDataPlug()->getValue()->copy();
			tmpContext->set( ImagePlug::channelNameContextName, string( "B" ) );
			b = inPlug()->channelDataPlug()->getValue()->copy();
		}

		processColorData( context, r.get(), g.get(), b.get() );

		ObjectVectorPtr result = new ObjectVector();
		result->members().push_back( r );
		result->members().push_back( g );
		result->members().push_back( b );

		static_cast<ObjectPlug *>( output )->setValue( result );
		return;
	}

	ImageProcessor::compute( output, context );
}

void ColorProcessor::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const std::string &channel = context->get<std::string>( ImagePlug::channelNameContextName );
	if( channel == "R" || channel == "G" || channel == "B" )
	{
		ImageProcessor::hashChannelData( output, context, h );
		h.append( channel );
		colorDataPlug()->hash( h );
	}
	else
	{
		// ColorProcessor only handles RGB values at present
		// so we just return the input hash otherwise.
		h = inPlug()->channelDataPlug()->hash();
	}
}

IECore::ConstFloatVectorDataPtr ColorProcessor::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstObjectVectorPtr colorData = boost::static_pointer_cast<const ObjectVector>( colorDataPlug()->getValue() );
	if( channelName == "R" )
	{
		return boost::static_pointer_cast<const FloatVectorData>( colorData->members()[0] );
	}
	else if( channelName == "G" )
	{
		return boost::static_pointer_cast<const FloatVectorData>( colorData->members()[1] );
	}
	else if( channelName == "B" )
	{
		return boost::static_pointer_cast<const FloatVectorData>( colorData->members()[2] );
	}

	// ColorProcessor only handles RGB values at present
	// so we just return the input value otherwise.
	return inPlug()->channelDataPlug()->getValue();
}

bool ColorProcessor::affectsColorData( const Gaffer::Plug *input ) const
{
	return input == inPlug()->channelDataPlug();
}

void ColorProcessor::hashColorData( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ContextPtr tmpContext = new Context( *context, Context::Borrowed );
	Context::Scope scopedContext( tmpContext.get() );
	tmpContext->set( ImagePlug::channelNameContextName, string( "R" ) );
	inPlug()->channelDataPlug()->hash( h );
	tmpContext->set( ImagePlug::channelNameContextName, string( "G" ) );
	inPlug()->channelDataPlug()->hash( h );
	tmpContext->set( ImagePlug::channelNameContextName, string( "B" ) );
	inPlug()->channelDataPlug()->hash( h );
}
