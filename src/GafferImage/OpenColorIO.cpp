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

#include "tbb/mutex.h"
#include "tbb/null_mutex.h"

#include "OpenColorIO/OpenColorIO.h"

#include "Gaffer/Context.h"

#include "GafferImage/OpenColorIO.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;

// code is in the namespace to avoid clashes between OpenColorIO the gaffer class,
// and OpenColorIO the library namespace.
namespace GafferImage
{

namespace Detail
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

} // namespace Detail

IE_CORE_DEFINERUNTIMETYPED( OpenColorIO );

size_t OpenColorIO::g_firstPlugIndex = 0;

OpenColorIO::OpenColorIO( const std::string &name )
	:	ColorProcessor( name )
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
	if( !ColorProcessor::enabled() )
	{
		return false;
	}

	std::string outSpaceString( outputSpacePlug()->getValue() );
	std::string inSpaceString( inputSpacePlug()->getValue() );

	return outSpaceString != inSpaceString &&
		outSpaceString.size() &&
		inSpaceString.size();
}

bool OpenColorIO::affectsColorData( const Gaffer::Plug *input ) const
{
	if( ColorProcessor::affectsColorData( input ) )
	{
		return true;
	}
	return input == inputSpacePlug() || input == outputSpacePlug();
}

void OpenColorIO::hashColorData( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ColorProcessor::hashColorData( context, h );

	inputSpacePlug()->hash( h );
	outputSpacePlug()->hash( h );
}

void OpenColorIO::processColorData( const Gaffer::Context *context, IECore::FloatVectorData *r, IECore::FloatVectorData *g, IECore::FloatVectorData *b ) const
{
	string inputSpace( inputSpacePlug()->getValue() );
	string outputSpace( outputSpacePlug()->getValue() );

	::OpenColorIO::ConstProcessorRcPtr processor;
	{
		Detail::OCIOMutex::scoped_lock lock( Detail::g_ocioMutex );
		::OpenColorIO::ConstConfigRcPtr config = ::OpenColorIO::GetCurrentConfig();
		processor = config->getProcessor( inputSpace.c_str(), outputSpace.c_str() );
	}

	::OpenColorIO::PlanarImageDesc image(
		r->baseWritable(),
		g->baseWritable(),
		b->baseWritable(),
		0, // alpha
		ImagePlug::tileSize(), // width
		ImagePlug::tileSize() // height
	);

	processor->apply( image );
}

} // namespace GafferImage
