//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
	
	if( input == inPlug()->formatPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input == inPlug()->channelNamesPlug()
	)
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );	
	}
	else if( affectsColorData( input ) )
	{
		outputs.push_back( colorDataPlug() );
	}
	else if( input == colorDataPlug()  )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

bool ColorProcessor::channelEnabled( const std::string &channel ) const
{
	if( !ImageProcessor::channelEnabled( channel ) )
	{
		return false;
	}

	return channel == "R" || channel == "G" || channel == "B";
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
			Context::Scope scopedContext( tmpContext );
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

void ColorProcessor::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inPlug()->formatPlug()->hash();
}

GafferImage::Format ColorProcessor::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug()->formatPlug()->getValue();
}

void ColorProcessor::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inPlug()->dataWindowPlug()->hash();
}

Imath::Box2i ColorProcessor::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug()->dataWindowPlug()->getValue();
}

void ColorProcessor::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inPlug()->channelNamesPlug()->hash();
}

IECore::ConstStringVectorDataPtr ColorProcessor::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug()->channelNamesPlug()->getValue();
}

void ColorProcessor::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelData( output, context, h );
	h.append( context->get<std::string>( ImagePlug::channelNameContextName ) );
	colorDataPlug()->hash( h );
}

IECore::ConstFloatVectorDataPtr ColorProcessor::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstObjectVectorPtr colorData = staticPointerCast<const ObjectVector>( colorDataPlug()->getValue() );
	if( channelName == "R" )
	{
		return staticPointerCast<const FloatVectorData>( colorData->members()[0] );
	}
	else if( channelName == "G" )
	{
		return staticPointerCast<const FloatVectorData>( colorData->members()[1] );
	}
	else if( channelName == "B" )
	{
		return staticPointerCast<const FloatVectorData>( colorData->members()[2] );
	}
	// We're not allowed to return NULL, but we should never get here because channelEnabled()
	// should be preventing it.
	return NULL;
}

bool ColorProcessor::affectsColorData( const Gaffer::Plug *input ) const
{
	return input == inPlug()->channelDataPlug();
}

void ColorProcessor::hashColorData( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ContextPtr tmpContext = new Context( *context, Context::Borrowed );
	Context::Scope scopedContext( tmpContext );
	tmpContext->set( ImagePlug::channelNameContextName, string( "R" ) );
	inPlug()->channelDataPlug()->hash( h );
	tmpContext->set( ImagePlug::channelNameContextName, string( "G" ) );
	inPlug()->channelDataPlug()->hash( h );
	tmpContext->set( ImagePlug::channelNameContextName, string( "B" ) );
	inPlug()->channelDataPlug()->hash( h );
}
