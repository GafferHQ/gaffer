//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

#include <boost/python/suite/indexing/vector_indexing_suite.hpp>
#include <boost/python/suite/indexing/container_utils.hpp>
#include "boost/python.hpp"
#include "boost/format.hpp"
#include "IECorePython/RunTimeTypedBinding.h"
#include "GafferBindings/Serialisation.h"
#include "GafferImage/ChannelMaskPlug.h"
#include "GafferImageBindings/ChannelMaskPlugBindings.h"

using namespace boost::python;
using namespace IECore;
using namespace GafferImage;

static ChannelMaskPlugPtr constructChannelMask(
	const char *name,
	Gaffer::Plug::Direction direction,
	IECore::ConstStringVectorDataPtr defaultValue,
	unsigned flags
)
{
	if( !defaultValue )
	{
		throw std::invalid_argument( "Default value must not be None." );
	}
	return new ChannelMaskPlug( name, direction, defaultValue, flags );
}

static boost::python::list maskChannelList( GafferImage::ChannelMaskPlug &plug, boost::python::object channelList )
{
	std::vector<std::string> channels;

	container_utils::extend_container< std::vector<std::string> >( channels, channelList );

	plug.maskChannels( channels );

	boost::python::list result;
	for( std::vector<std::string>::const_iterator it = channels.begin(); it != channels.end(); it++ )
	{
		result.append( *it );
	}

	return result;
}

static boost::python::list removeDuplicates( boost::python::object channelList )
{
	std::vector<std::string> channels;

	container_utils::extend_container< std::vector<std::string> >( channels, channelList );

	GafferImage::ChannelMaskPlug::removeDuplicateIndices( channels );

	boost::python::list result;
	for( std::vector<std::string>::const_iterator it = channels.begin(); it != channels.end(); it++ )
	{
		result.append( *it );
	}

	return result;
}

namespace GafferImageBindings
{

	void bindChannelMaskPlug()
	{
		IECorePython::RunTimeTypedClass<ChannelMaskPlug>()
			.def( "__init__", make_constructor( constructChannelMask, default_call_policies(),
						(
						 boost::python::arg_( "name" )=Gaffer::GraphComponent::defaultName<ChannelMaskPlug>(),
						 boost::python::arg_( "direction" )=Gaffer::Plug::In,
						 boost::python::arg_( "defaultValue" ),
						 boost::python::arg_( "flags" )=Gaffer::Plug::Default
						)
			)
		)
		.def( "maskChannels", &maskChannelList )
		.def( "removeDuplicateIndices", &removeDuplicates ).staticmethod("removeDuplicateIndices")
		.def( "channelIndex", &ChannelMaskPlug::channelIndex ).staticmethod("channelIndex")
	;
}

} // namespace IECorePython

