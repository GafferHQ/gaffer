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

#include "IOBinding.h"

#include "GafferImage/Constant.h"
#include "GafferImage/Checkerboard.h"
#include "GafferImage/ImageReader.h"
#include "GafferImage/ImageWriter.h"
#include "GafferImage/OpenImageIOReader.h"
#include "GafferImage/Ramp.h"

#include "GafferDispatchBindings/TaskNodeBinding.h"

#include "GafferBindings/DependencyNodeBinding.h"

#include "boost/mpl/vector.hpp"

using namespace std;
using namespace boost::python;
using namespace Gaffer;
using namespace GafferImage;
using namespace GafferBindings;
using namespace GafferDispatchBindings;

namespace
{

struct DefaultColorSpaceFunction
{
	DefaultColorSpaceFunction( object fn )
		:	m_fn( fn )
	{
	}

	string operator()( const std::string &fileName, const std::string &fileFormat, const std::string &dataType, const IECore::CompoundData *metadata )
	{

		IECorePython::ScopedGILLock gilock;
		try
		{
			return extract<string>( m_fn( fileName, fileFormat, dataType, IECore::CompoundDataPtr( const_cast<IECore::CompoundData *>( metadata ) ) ) );
		}
		catch( const error_already_set &e )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}

	private:

		object m_fn;
};

template<typename T>
void setDefaultColorSpaceFunction( object f )
{
	T::setDefaultColorSpaceFunction( DefaultColorSpaceFunction( f ) );
}

template<typename T>
object getDefaultColorSpaceFunction()
{
	return make_function(
		T::getDefaultColorSpaceFunction(),
		default_call_policies(),
		boost::mpl::vector<string, const string &, const string &, const string &, const IECore::CompoundData *>()
	);
}

template<typename T>
boost::python::list supportedExtensions()
{
	std::vector<std::string> e;
	T::supportedExtensions( e );

	boost::python::list result;
	for( std::vector<std::string>::const_iterator it = e.begin(), eIt = e.end(); it != eIt; ++it )
	{
		result.append( *it );
	}

	return result;
}

} // namespace

void GafferImageModule::bindIO()
{

	DependencyNodeClass<Constant>();
	DependencyNodeClass<Checkerboard>();
	DependencyNodeClass<Ramp>();

	{
		scope s = GafferBindings::DependencyNodeClass<OpenImageIOReader>()
			.def( "setOpenFilesLimit", &OpenImageIOReader::setOpenFilesLimit )
			.staticmethod( "setOpenFilesLimit" )
			.def( "getOpenFilesLimit", &OpenImageIOReader::getOpenFilesLimit )
			.staticmethod( "getOpenFilesLimit" )
			.def( "supportedExtensions", &supportedExtensions<OpenImageIOReader> )
			.staticmethod( "supportedExtensions" )
		;

		enum_<OpenImageIOReader::MissingFrameMode>( "MissingFrameMode" )
			.value( "Error", OpenImageIOReader::Error )
			.value( "Black", OpenImageIOReader::Black )
			.value( "Hold", OpenImageIOReader::Hold )
		;
	}

	{
		scope s = GafferBindings::DependencyNodeClass<ImageReader>()
			.def( "supportedExtensions", &supportedExtensions<ImageReader> )
			.staticmethod( "supportedExtensions" )
			.def( "setDefaultColorSpaceFunction", &setDefaultColorSpaceFunction<ImageReader> )
			.staticmethod( "setDefaultColorSpaceFunction" )
			.def( "getDefaultColorSpaceFunction", &getDefaultColorSpaceFunction<ImageReader> )
			.staticmethod( "getDefaultColorSpaceFunction" )
		;

		enum_<ImageReader::MissingFrameMode>( "MissingFrameMode" )
			.value( "Error", ImageReader::Error )
			.value( "Black", ImageReader::Black )
			.value( "Hold", ImageReader::Hold )
		;

		enum_<ImageReader::FrameMaskMode>( "FrameMaskMode" )
			.value( "None", ImageReader::None )
			.value( "None_", ImageReader::None )
			.value( "BlackOutside", ImageReader::BlackOutside )
			.value( "ClampToFrame", ImageReader::ClampToFrame )
		;
	}

	{
		using ImageWriterWrapper = TaskNodeWrapper<ImageWriter>;

		scope s = TaskNodeClass<ImageWriter, ImageWriterWrapper>()
			.def( "currentFileFormat", &ImageWriter::currentFileFormat )
			.def( "setDefaultColorSpaceFunction", &setDefaultColorSpaceFunction<ImageWriter> )
			.staticmethod( "setDefaultColorSpaceFunction" )
			.def( "getDefaultColorSpaceFunction", &getDefaultColorSpaceFunction<ImageWriter> )
			.staticmethod( "getDefaultColorSpaceFunction" )
		;

		enum_<ImageWriter::Mode>( "Mode" )
			.value( "Scanline", ImageWriter::Scanline )
			.value( "Tile", ImageWriter::Tile )
		;
	}
}
