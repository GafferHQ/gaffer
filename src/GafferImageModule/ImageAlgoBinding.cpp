//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "boost/python.hpp"

#include "ImageAlgoBinding.h"

#include "GafferImage/ImageAlgo.h"

#include "IECorePython/ScopedGILLock.h"
#include "IECorePython/ScopedGILRelease.h"

#include "boost/python/suite/indexing/container_utils.hpp"

using namespace std;
using namespace boost::python;
using namespace GafferImage;

namespace
{

// Register a conversion from StringVectorData.
/// \todo We could instead do this in the Cortex bindings for all
/// VectorTypedData types.
struct StringVectorFromStringVectorData
{

	StringVectorFromStringVectorData()
	{
		boost::python::converter::registry::push_back(
			&convertible,
			nullptr,
			boost::python::type_id<std::vector<std::string> >()
		);
	}

	static void *convertible( PyObject *obj )
	{
		extract<IECore::StringVectorData *> dataExtractor( obj );
		if( dataExtractor.check() )
		{
			if( IECore::StringVectorData *data = dataExtractor() )
			{
				return &(data->writable());
			}
		}

		return nullptr;
	}

};

boost::python::list layerNamesWrapper( object pythonChannelNames )
{
	vector<string> channelNames;
	container_utils::extend_container( channelNames, pythonChannelNames );
	const vector<string> layerNames = GafferImage::ImageAlgo::layerNames( channelNames );
	boost::python::list result;
	for( vector<string>::const_iterator it = layerNames.begin(), eIt = layerNames.end(); it != eIt; ++it )
	{
		result.append( *it );
	}
	return result;
}

inline bool channelExistsWrapper( const GafferImage::ImagePlug *image, const std::string &channelName )
{
	IECorePython::ScopedGILRelease r;
	return GafferImage::ImageAlgo::channelExists( image, channelName );
}

boost::python::list sortChannelNamesWrapper( object pythonChannelNames )
{
	vector<string> channelNames;
	container_utils::extend_container( channelNames, pythonChannelNames );
	GafferImage::ImageAlgo::sortChannelNames( channelNames );
	boost::python::list result;
	for( const auto &it : channelNames )
	{
		result.append( it );
	}
	return result;
}

void deleteWithGIL( object *o )
{
	IECorePython::ScopedGILLock gilLock;
	delete o;
}

void parallelGatherTiles1( const GafferImage::ImagePlug &image, object pythonTileFunctor, object pythonGatherFunctor, const Imath::Box2i &window, ImageAlgo::TileOrder tileOrder )
{
	IECorePython::ScopedGILRelease gilRelease;
	ImageAlgo::parallelGatherTiles(

		&image,

		[ &pythonTileFunctor ] ( const ImagePlug *image, const Imath::V2i &tileOrigin )
		{
			IECorePython::ScopedGILLock gilLock;
			object tile = pythonTileFunctor( ImagePlugPtr( const_cast<ImagePlug *>( image ) ), tileOrigin );
			return std::shared_ptr<object>( new object( tile ), deleteWithGIL );
		},

		[ &pythonGatherFunctor ] ( const ImagePlug *image, const Imath::V2i &tileOrigin, std::shared_ptr<object> tile )
		{
			IECorePython::ScopedGILLock gilLock;
			pythonGatherFunctor( ImagePlugPtr( const_cast<ImagePlug *>( image ) ), tileOrigin, *tile );
		},

		window,
		tileOrder

	);
}

void parallelGatherTiles2( const GafferImage::ImagePlug &image, object pythonChannelNames, object pythonTileFunctor, object pythonGatherFunctor, const Imath::Box2i &window, ImageAlgo::TileOrder tileOrder )
{
	vector<string> channelNames;
	boost::python::container_utils::extend_container( channelNames, pythonChannelNames );

	IECorePython::ScopedGILRelease gilRelease;
	ImageAlgo::parallelGatherTiles(

		&image, channelNames,

		[ &pythonTileFunctor ] ( const ImagePlug *image, const std::string &channelName, const Imath::V2i &tileOrigin )
		{
			IECorePython::ScopedGILLock gilLock;
			object tile = pythonTileFunctor( ImagePlugPtr( const_cast<ImagePlug *>( image ) ), channelName, tileOrigin );
			return std::shared_ptr<object>( new object( tile ), deleteWithGIL );
		},

		[ &pythonGatherFunctor ] ( const ImagePlug *image, const std::string &channelName, const Imath::V2i &tileOrigin, std::shared_ptr<object> tile )
		{
			IECorePython::ScopedGILLock gilLock;
			pythonGatherFunctor( ImagePlugPtr( const_cast<ImagePlug *>( image ) ), channelName, tileOrigin, *tile );
		},

		window,
		tileOrder

	);
}

IECoreImage::ImagePrimitivePtr imageWrapper( const ImagePlug *plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	return ImageAlgo::image( plug );
}

IECore::MurmurHash imageHashWrapper( const ImagePlug *plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	return ImageAlgo::imageHash( plug );
}

IECore::CompoundObjectPtr tilesWrapper( const ImagePlug *plug, bool copy )
{
	IECorePython::ScopedGILRelease gilRelease;
	IECore::ConstCompoundObjectPtr d = ImageAlgo::tiles( plug );
	return copy ? d->copy() : boost::const_pointer_cast<IECore::CompoundObject>( d );
}


} // namespace

void GafferImageModule::bindImageAlgo()
{
	object module( borrowed( PyImport_AddModule( "GafferImage.ImageAlgo" ) ) );
	scope().attr( "ImageAlgo" ) = module;
	scope moduleScope( module );

	def( "layerNames", &layerNamesWrapper );
	def( "layerName", &GafferImage::ImageAlgo::layerName );
	def( "baseName", &GafferImage::ImageAlgo::baseName );
	def( "channelName", &GafferImage::ImageAlgo::channelName );
	def( "colorIndex", &GafferImage::ImageAlgo::colorIndex );
	def( "channelExists", &channelExistsWrapper );
	def( "channelExists", ( bool (*)( const std::vector<std::string> &channelNames, const std::string &channelName ) )&GafferImage::ImageAlgo::channelExists );
	def( "sortChannelNames", &sortChannelNamesWrapper );

	enum_<ImageAlgo::TileOrder>( "TileOrder" )
		.value( "Unordered", ImageAlgo::Unordered )
		.value( "TopToBottom", ImageAlgo::TopToBottom )
		.value( "BottomToTop", ImageAlgo::BottomToTop )
	;

	def(
		"parallelGatherTiles", &parallelGatherTiles1,
		(
			boost::python::arg( "image" ),
			boost::python::arg( "tileFunctor" ),
			boost::python::arg( "gatherFunctor" ),
			boost::python::arg( "window" ) = Imath::Box2i(),
			boost::python::arg( "tileOrder" ) = ImageAlgo::Unordered
		)
	);

	def(
		"parallelGatherTiles", &parallelGatherTiles2,
		(
			boost::python::arg( "image" ),
			boost::python::arg( "channelNames" ),
			boost::python::arg( "tileFunctor" ),
			boost::python::arg( "gatherFunctor" ),
			boost::python::arg( "window" ) = Imath::Box2i(),
			boost::python::arg( "tileOrder" ) = ImageAlgo::Unordered
		)
	);

	def( "image", &imageWrapper );
	def( "imageHash", &imageHashWrapper );
	def( "tiles", &tilesWrapper, ( boost::python::arg( "_copy" ) = true ) );

	StringVectorFromStringVectorData();

}
