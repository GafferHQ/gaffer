//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

#include "OpenColorIO/OpenColorIO.h"

#include "Gaffer/Context.h"

#include "GafferImage/OpenColorIO.h"

using namespace IECore;
using namespace Gaffer;

// code is in the namespace to avoid clashes between OpenColorIO the gaffer class,
// and OpenColorIO the library namespace.
namespace GafferImage
{

IE_CORE_DEFINERUNTIMETYPED( OpenColorIO );

size_t OpenColorIO::g_firstPlugIndex = 0;

OpenColorIO::OpenColorIO( const std::string &name )
	:	FilterProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "inputSpace" ) );
	addChild( new StringPlug( "outputSpace" ) );	
}

OpenColorIO::~OpenColorIO()
{
}

Gaffer::StringPlug *OpenColorIO::inputSpacePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *OpenColorIO::inputSpacePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *OpenColorIO::outputSpacePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *OpenColorIO::outputSpacePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

bool OpenColorIO::enabled() const
{
	std::string outSpaceString( outputSpacePlug()->getValue() );
	std::string inSpaceString( inputSpacePlug()->getValue() );
	
	return outSpaceString != inSpaceString &&
		outSpaceString.size() &&
		inSpaceString.size()
		? FilterProcessor::enabled() : false;
}

void OpenColorIO::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilterProcessor::affects( input, outputs );
	
	if( input == inPlug()->channelDataPlug() ||
		input == inputSpacePlug() ||
		input == outputSpacePlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );	
	}
}

void OpenColorIO::hashChannelDataPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	if( channelName == "R" || channelName == "G" || channelName == "B" )
	{
		inPlug()->channelDataPlug()->hash( h );
		
		ContextPtr tmpContext = new Context( *Context::current() );
		Context::Scope scopedContext( tmpContext );	
		
		tmpContext->set( ImagePlug::channelNameContextName, std::string( "R" ) );
		inPlug()->channelDataPlug()->hash( h );
		tmpContext->set( ImagePlug::channelNameContextName, std::string( "G" ) );
		inPlug()->channelDataPlug()->hash( h );
		tmpContext->set( ImagePlug::channelNameContextName, std::string( "B" ) );
		inPlug()->channelDataPlug()->hash( h );
		
		inputSpacePlug()->hash( h );
		outputSpacePlug()->hash( h );
	}
}

IECore::ConstFloatVectorDataPtr OpenColorIO::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if( channelName == "R" || channelName == "G" || channelName == "B" )
	{
		std::string inputSpace = inputSpacePlug()->getValue();
		std::string outputSpace = outputSpacePlug()->getValue();
		if( inputSpace.size() && outputSpace.size() )
		{
			
			FloatVectorDataPtr r = inPlug()->channelData( "R", tileOrigin )->copy();
			FloatVectorDataPtr g = inPlug()->channelData( "G", tileOrigin )->copy();
			FloatVectorDataPtr b = inPlug()->channelData( "B", tileOrigin )->copy();
	   
			::OpenColorIO::ConstConfigRcPtr config = ::OpenColorIO::GetCurrentConfig();
			::OpenColorIO::ConstProcessorRcPtr processor = config->getProcessor( inputSpace.c_str(), outputSpace.c_str() );
			
			::OpenColorIO::PlanarImageDesc image(
				r->baseWritable(),
				g->baseWritable(),
				b->baseWritable(),
				0, // alpha
				ImagePlug::tileSize(), // width
				ImagePlug::tileSize() // height
			);
			
			processor->apply( image );
			
			if( channelName=="R" )
			{
				return r;
			}
			else if( channelName=="G" )
			{
				return g;
			}
			else if( channelName=="B" )
			{
				return b;
			}
			else
			{
				// shouldn't get here.
				assert( 0 );
			}
		}
		else
		{
			// colorspaces not specified - fall through
		}
	}
	
	return inPlug()->channelDataPlug()->getValue();
}

} // namespace GafferImage
