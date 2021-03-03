//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

#include "CoreBinding.h"

#include "GafferImage/AtomicFormatPlug.h"
#include "GafferImage/FormatData.h"
#include "GafferImage/FormatPlug.h"
#include "GafferImage/ImageNode.h"
#include "GafferImage/ImagePlug.h"
#include "GafferImage/ImageProcessor.h"
#include "GafferImage/Sampler.h"
#include "GafferImage/FlatImageSource.h"

#include "GafferBindings/ComputeNodeBinding.h"
#include "GafferBindings/Serialisation.h"
#include "GafferBindings/TypedPlugBinding.h"
#include "GafferBindings/ValuePlugBinding.h"

#include "Gaffer/ScriptNode.h"

#include "IECorePython/SimpleTypedDataBinding.h"

using namespace boost::python;
using namespace Gaffer;
using namespace GafferImage;
using namespace GafferBindings;

namespace
{

IECore::FloatVectorDataPtr channelData( const ImagePlug &plug,  const std::string &channelName, const Imath::V2i &tile, bool copy  )
{
	IECorePython::ScopedGILRelease gilRelease;
	IECore::ConstFloatVectorDataPtr d = plug.channelData( channelName, tile );
	return copy ? d->copy() : boost::const_pointer_cast<IECore::FloatVectorData>( d );
}

IECore::MurmurHash channelDataHash( const ImagePlug &plug, const std::string &channelName, const Imath::V2i &tileOrigin )
{
	IECorePython::ScopedGILRelease gilRelease;
	return plug.channelDataHash( channelName, tileOrigin );
}

GafferImage::Format format( const ImagePlug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	return plug.format();
}

IECore::MurmurHash formatHash( const ImagePlug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	return plug.formatHash();
}

Imath::Box2i dataWindow( const ImagePlug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	return plug.dataWindow();
}

IECore::MurmurHash dataWindowHash( const ImagePlug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	return plug.dataWindowHash();
}

IECore::StringVectorDataPtr channelNames( const ImagePlug &plug, bool copy )
{
	IECorePython::ScopedGILRelease gilRelease;
	IECore::ConstStringVectorDataPtr d = plug.channelNames();
	return copy ? d->copy() : boost::const_pointer_cast<IECore::StringVectorData>( d );
}

IECore::MurmurHash channelNamesHash( const ImagePlug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	return plug.channelNamesHash();
}

IECore::CompoundDataPtr metadata( const ImagePlug &plug, bool copy )
{
	IECorePython::ScopedGILRelease gilRelease;
	IECore::ConstCompoundDataPtr d = plug.metadata();
	return copy ? d->copy() : boost::const_pointer_cast<IECore::CompoundData>( d );
}

IECore::MurmurHash metadataHash( const ImagePlug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	return plug.metadataHash();
}

bool deep( const ImagePlug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	return plug.deep();
}

IECore::MurmurHash deepHash( const ImagePlug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	return plug.deepHash();
}

IECore::IntVectorDataPtr sampleOffsets( const ImagePlug &plug, const Imath::V2i &tile, bool copy  )
{
	IECorePython::ScopedGILRelease gilRelease;
	IECore::ConstIntVectorDataPtr d = plug.sampleOffsets( tile );
	return copy ? d->copy() : boost::const_pointer_cast<IECore::IntVectorData>( d );
}

IECore::MurmurHash sampleOffsetsHash( const ImagePlug &plug, const Imath::V2i &tile )
{
	IECorePython::ScopedGILRelease gilRelease;
	return plug.sampleOffsetsHash( tile );
}

IECore::IntVectorDataPtr emptyTileSampleOffsets( bool copy )
{
	IECore::ConstIntVectorDataPtr d = ImagePlug::emptyTileSampleOffsets();
	return copy ? d->copy() : boost::const_pointer_cast<IECore::IntVectorData>( d );
}

IECore::IntVectorDataPtr flatTileSampleOffsets( bool copy )
{
	IECore::ConstIntVectorDataPtr d = ImagePlug::flatTileSampleOffsets();
	return copy ? d->copy() : boost::const_pointer_cast<IECore::IntVectorData>( d );
}

IECore::FloatVectorDataPtr emptyTile( bool copy )
{
	IECore::ConstFloatVectorDataPtr d = ImagePlug::emptyTile();
	return copy ? d->copy() : boost::const_pointer_cast<IECore::FloatVectorData>( d );
}

IECore::FloatVectorDataPtr blackTile( bool copy )
{
	IECore::ConstFloatVectorDataPtr d = ImagePlug::blackTile();
	return copy ? d->copy() : boost::const_pointer_cast<IECore::FloatVectorData>( d );
}

IECore::FloatVectorDataPtr whiteTile( bool copy )
{
	IECore::ConstFloatVectorDataPtr d = ImagePlug::whiteTile();
	return copy ? d->copy() : boost::const_pointer_cast<IECore::FloatVectorData>( d );
}

boost::python::list registeredFormats()
{
	std::vector<std::string> names;
	Format::registeredFormats( names );
	boost::python::list result;
	for( std::vector<std::string>::const_iterator it = names.begin(), eIt = names.end(); it != eIt; ++it )
	{
		result.append( *it );
	}
	return result;
}

std::string formatRepr( const GafferImage::Format &format )
{
	if ( format.getDisplayWindow().isEmpty() )
	{
		return std::string( "GafferImage.Format()" );
	}
	else if ( format.getDisplayWindow().min == Imath::V2i( 0 ) )
	{
		Imath::Box2i box( format.getDisplayWindow() );
		return std::string(
			boost::str( boost::format(
				"GafferImage.Format( %d, %d, %.3f )" )
				% box.max.x % box.max.y % format.getPixelAspect()
			)
		);
	}
	else
	{
		Imath::Box2i box( format.getDisplayWindow() );
		return std::string(
			boost::str( boost::format(
				"GafferImage.Format( imath.Box2i( imath.V2i( %d, %d ), imath.V2i( %d, %d ) ), %.3f )" )
				% box.min.x % box.min.y % box.max.x % box.max.y % format.getPixelAspect()
			)
		);
	}
}

class AtomicFormatPlugSerialiser : public GafferBindings::ValuePlugSerialiser
{

	public :

		void moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules, const Serialisation &serialisation ) const override
		{
			// Imath is needed when reloading Format values which reference Box2i.
			ValuePlugSerialiser::moduleDependencies( graphComponent, modules, serialisation );
			modules.insert( "imath" );
		}

};

void setValue( FormatPlug *plug, const Format &value )
{
	// we use a GIL release here to prevent a lock in the case where this triggers a graph
	// evaluation which decides to go back into python on another thread:
	IECorePython::ScopedGILRelease r;
	plug->setValue( value );
}

Format getValue( const FormatPlug *plug )
{
	// Must release GIL in case computation spawns threads which need
	// to reenter Python.
	IECorePython::ScopedGILRelease r;
	return plug->getValue();
}

class FormatPlugSerialiser : public GafferBindings::ValuePlugSerialiser
{

	public :

		void moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules, const Serialisation &serialisation ) const override
		{
			// Imath is needed when reloading Format values which reference Box2i.
			ValuePlugSerialiser::moduleDependencies( graphComponent, modules, serialisation );
			modules.insert( "imath" );
		}

};

} // namespace

void GafferImageModule::bindCore()
{

	PlugClass<ImagePlug>()
		.def(
			init< const std::string &, Gaffer::Plug::Direction, unsigned >
			(
				(
					arg( "name" ) = Gaffer::GraphComponent::defaultName<ImagePlug>(),
					arg( "direction" ) = Gaffer::Plug::In,
					arg( "flags" ) = Gaffer::Plug::Default
				)
			)
		)
		.def( "channelData", &channelData, ( arg( "_copy" ) = true ) )
		.def( "channelDataHash", &channelDataHash )
		.def( "format", &format )
		.def( "formatHash", &formatHash )
		.def( "dataWindow", &dataWindow )
		.def( "dataWindowHash", &dataWindowHash )
		.def( "channelNames", &channelNames, ( arg( "_copy" ) = true ) )
		.def( "channelNamesHash", &channelNamesHash )
		.def( "metadata", &metadata, ( arg( "_copy" ) = true ) )
		.def( "metadataHash", &metadataHash )
		.def( "deep", &deep )
		.def( "deepHash", &deepHash )
		.def( "sampleOffsets", &sampleOffsets, ( arg( "_copy" ) = true ) )
		.def( "sampleOffsetsHash", &sampleOffsetsHash )
		.def( "tileSize", &ImagePlug::tileSize ).staticmethod( "tileSize" )
		.def( "tilePixels", &ImagePlug::tilePixels ).staticmethod( "tilePixels" )
		.def( "tileIndex", &ImagePlug::tileIndex ).staticmethod( "tileIndex" )
		.def( "tileOrigin", &ImagePlug::tileOrigin ).staticmethod( "tileOrigin" )
		.def( "pixelIndex", &ImagePlug::pixelIndex ).staticmethod( "pixelIndex" )
		.def( "emptyTileSampleOffsets", &emptyTileSampleOffsets, ( arg( "_copy" ) = true ) ).staticmethod( "emptyTileSampleOffsets" )
		.def( "flatTileSampleOffsets", &flatTileSampleOffsets, ( arg( "_copy" ) = true ) ).staticmethod( "flatTileSampleOffsets" )
		.def( "emptyTile", &emptyTile, ( arg( "_copy" ) = true ) ).staticmethod( "emptyTile" )
		.def( "blackTile", &blackTile, ( arg( "_copy" ) = true ) ).staticmethod( "blackTile" )
		.def( "whiteTile", &whiteTile, ( arg( "_copy" ) = true ) ).staticmethod( "whiteTile" )
	;

	using ImageNodeWrapper = ComputeNodeWrapper<ImageNode>;
	GafferBindings::DependencyNodeClass<ImageNode, ImageNodeWrapper>();

	using FlatImageSourceWrapper = ComputeNodeWrapper<FlatImageSource>;
	GafferBindings::DependencyNodeClass<FlatImageSource, FlatImageSourceWrapper>();

	class_<Format>( "Format" )

		.def(
			init<int, int, double>(
				(
					boost::python::arg( "width" ),
					boost::python::arg( "height" ),
					boost::python::arg( "pixelAspect" ) = 1.0f
				)
			)
		)
		.def(
			init<const Imath::Box2i &, double, bool>(
				(
					boost::python::arg( "displayWindow" ),
					boost::python::arg( "pixelAspect" ) = 1.0f,
					boost::python::arg( "fromEXRSpace" ) = false
				)
			)
		)

		.def( "width", &Format::width )
		.def( "height", &Format::height )
		.def( "getPixelAspect", &Format::getPixelAspect )
		.def( "setPixelAspect", &Format::setPixelAspect )
		.def( "getDisplayWindow", &Format::getDisplayWindow, return_value_policy<copy_const_reference>() )
		.def( "setDisplayWindow", &Format::setDisplayWindow )

		.def( "fromEXRSpace", ( int (Format::*)( int ) const )&Format::fromEXRSpace )
		.def( "fromEXRSpace", ( Imath::V2i (Format::*)( const Imath::V2i & ) const )&Format::fromEXRSpace )
		.def( "fromEXRSpace", ( Imath::Box2i (Format::*)( const Imath::Box2i & ) const )&Format::fromEXRSpace )

		.def( "toEXRSpace", ( int (Format::*)( int ) const )&Format::toEXRSpace )
		.def( "toEXRSpace", ( Imath::V2i (Format::*)( const Imath::V2i & ) const )&Format::toEXRSpace )
		.def( "toEXRSpace", ( Imath::Box2i (Format::*)( const Imath::Box2i & ) const )&Format::toEXRSpace )

		.def( "__eq__", &Format::operator== )
		.def( "__repr__", &formatRepr )
		.def( "__str__", &boost::lexical_cast<std::string, Format> )

		.def( "registerFormat", &Format::registerFormat ).staticmethod( "registerFormat" )
		.def( "deregisterFormat", &Format::deregisterFormat ).staticmethod( "deregisterFormat" )
		.def( "registeredFormats", &registeredFormats ).staticmethod( "registeredFormats" )
		.def( "format", &Format::format ).staticmethod( "format" )
		.def( "name", &Format::name ).staticmethod( "name" )
	;

	IECorePython::RunTimeTypedClass<FormatData>()
		.def( init<>() )
		.def( init<const Format &>() )
		.add_property( "value", make_function( &FormatData::writable, return_internal_reference<1>() ) )
		.def( "hasBase", &FormatData::hasBase ).staticmethod( "hasBase" )
	;

	IECorePython::TypedDataFromType<FormatData>();

	TypedPlugClass<AtomicFormatPlug>();

	Serialisation::registerSerialiser( static_cast<IECore::TypeId>(AtomicFormatPlugTypeId), new AtomicFormatPlugSerialiser );

	PlugClass<FormatPlug>()
		.def(
			boost::python::init<const std::string &, Gaffer::Plug::Direction, const Format &, unsigned>(
				(
					boost::python::arg_( "name" ) = GraphComponent::defaultName<FormatPlug>(),
					boost::python::arg_( "direction" ) = Plug::In,
					boost::python::arg_( "defaultValue" ) = Format(),
					boost::python::arg_( "flags" ) = Plug::Default
				)
			)
		)
		.def( "defaultValue", &FormatPlug::defaultValue )
		.def( "setValue", &setValue )
		.def( "getValue", &getValue )
		.def( "setDefaultFormat", &FormatPlug::setDefaultFormat )
		.staticmethod( "setDefaultFormat" )
		.def( "getDefaultFormat", &FormatPlug::getDefaultFormat )
		.staticmethod( "getDefaultFormat" )
		.def( "acquireDefaultFormatPlug", &FormatPlug::acquireDefaultFormatPlug, return_value_policy<IECorePython::CastToIntrusivePtr>() )
		.staticmethod( "acquireDefaultFormatPlug" )
	;

	Serialisation::registerSerialiser( FormatPlug::staticTypeId(), new FormatPlugSerialiser );

		class_<Sampler> cls( "Sampler", no_init );

	{
		// Must bind the BoundingMode first, so that it can be used in the default
		// arguments to the init methods.
		scope s = cls;
		enum_<Sampler::BoundingMode>( "BoundingMode" )
			.value( "Black", Sampler::Black )
			.value( "Clamp", Sampler::Clamp )
		;
	}

	cls.def(
			init<const GafferImage::ImagePlug *, const std::string &, const Imath::Box2i &, Sampler::BoundingMode>
			(
				(
					arg( "boundingMode" ) = Sampler::Black
				)
			)
		)
		.def( "hash", (IECore::MurmurHash (Sampler::*)() const)&Sampler::hash )
		.def( "hash", (void (Sampler::*)( IECore::MurmurHash & ) const)&Sampler::hash )
		.def( "sample", (float (Sampler::*)( float, float ) )&Sampler::sample )
		.def( "sample", (float (Sampler::*)( int, int ) )&Sampler::sample )
	;

}
