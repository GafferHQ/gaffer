//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "tbb/mutex.h"
#include "tbb/null_mutex.h"

#include "IECore/SimpleTypedData.h"

#include "Gaffer/Context.h"

#include "GafferImage/OpenColorIOTransform.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

namespace
{

// Although the OpenColorIO library is advertised as threadsafe,
// it seems to crash regularly on OS X in getProcessor(), while
// mucking around with the locale(). we mutex the call to getProcessor()
// but still do the actual processing in parallel - this seems to
// have negligible performance impact but a nice not-crashing impact.
// On other platforms we use a null_mutex so there should be no
// performance impact at all.
#ifdef __APPLE__
typedef tbb::mutex OCIOMutex;
#else
typedef tbb::null_mutex OCIOMutex;
#endif

static OCIOMutex g_ocioMutex;

} // namespace

IE_CORE_DEFINERUNTIMETYPED( OpenColorIOTransform );

OpenColorIOTransform::OpenColorIOTransform( const std::string &name )
	:	ColorProcessor( name )
{
}

OpenColorIOTransform::~OpenColorIOTransform()
{
}

bool OpenColorIOTransform::enabled() const
{
	if( !ColorProcessor::enabled() )
	{
		return false;
	}

	MurmurHash h;
	hashTransform( Context::current(), h );
	return ( h != MurmurHash() );
}

bool OpenColorIOTransform::affectsColorData( const Gaffer::Plug *input ) const
{
	if( ColorProcessor::affectsColorData( input ) )
	{
		return true;
	}

	return affectsTransform( input );
}

void OpenColorIOTransform::hashColorData( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ColorProcessor::hashColorData( context, h );

	hashTransform( context, h );
}

void OpenColorIOTransform::processColorData( const Gaffer::Context *context, IECore::FloatVectorData *r, IECore::FloatVectorData *g, IECore::FloatVectorData *b ) const
{
	OpenColorIO::ConstTransformRcPtr colorTransform = transform();
	if( !colorTransform )
	{
		return;
	}

	OpenColorIO::ConstProcessorRcPtr processor;
	{
		OCIOMutex::scoped_lock lock( g_ocioMutex );
		OpenColorIO::ConstConfigRcPtr config = OpenColorIO::GetCurrentConfig();
		processor = config->getProcessor( colorTransform );
	}

	OpenColorIO::PlanarImageDesc image(
		r->baseWritable(),
		g->baseWritable(),
		b->baseWritable(),
		0, // alpha
		ImagePlug::tileSize(), // width
		ImagePlug::tileSize() // height
	);

	processor->apply( image );
}

void OpenColorIOTransform::availableColorSpaces( std::vector<std::string> &colorSpaces )
{
	OpenColorIO::ConstConfigRcPtr config = OpenColorIO::GetCurrentConfig();

	colorSpaces.clear();
	colorSpaces.reserve( config->getNumColorSpaces() );

	for( int i = 0; i < config->getNumColorSpaces(); ++i )
	{
		colorSpaces.push_back( config->getColorSpaceNameByIndex( i ) );
	}
}
