//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "IECorePython/RunTimeTypedBinding.h"

#include "GafferBindings/ComputeNodeBinding.h"
#include "GafferBindings/ValuePlugBinding.h"

#include "GafferImage/DeleteChannels.h"
#include "GafferImage/CollectImages.h"
#include "GafferImage/CopyChannels.h"
#include "GafferImage/Merge.h"
#include "GafferImage/Mix.h"
#include "GafferImage/Shuffle.h"

#include "ImageProcessorBinding.h"

using namespace boost::python;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferImage;

namespace
{

std::string maskedChannelPlugRepr( const Shuffle::ChannelPlug *plug, unsigned flagsMask )
{
	// the only reason we have a different __repr__ implementation than Gaffer::Plug is
	// because we can't determine the nested class name from a PyObject.
	std::string result = "GafferImage.Shuffle.ChannelPlug( \"" + plug->getName().string() + "\", ";

	if( plug->direction()!=Plug::In )
	{
		result += "direction = " + PlugSerialiser::directionRepr( plug->direction() ) + ", ";
	}

	const unsigned flags = plug->getFlags() & flagsMask;
	if( flags != Plug::Default )
	{
		result += "flags = " + PlugSerialiser::flagsRepr( flags ) + ", ";
	}

	result += ")";

	return result;
}

std::string channelPlugRepr( const Shuffle::ChannelPlug *plug )
{
	return maskedChannelPlugRepr( plug, Plug::All );
}

class ChannelPlugSerialiser : public ValuePlugSerialiser
{

	public :

		virtual std::string constructor( const Gaffer::GraphComponent *graphComponent, const Serialisation &serialisation ) const
		{
			return maskedChannelPlugRepr( static_cast<const Shuffle::ChannelPlug *>( graphComponent ), Plug::All & ~Plug::ReadOnly );
		}

};

} // namespace

void GafferImageModule::bindImageProcessor()
{

	typedef ComputeNodeWrapper<ImageProcessor> ImageProcessorWrapper;
	GafferBindings::DependencyNodeClass<ImageProcessor, ImageProcessorWrapper>()
		.def( init<const std::string &, size_t, size_t>(
				(
					arg( "name" ) = GraphComponent::defaultName<ImageProcessor>(),
					arg( "minInputs" ),
					arg( "maxInputs" ) = Imath::limits<size_t>::max()
				)
			)
		)
	;

	DependencyNodeClass<CollectImages>();
	DependencyNodeClass<CopyChannels>();
	DependencyNodeClass<Mix>();

	{
		scope s = GafferBindings::DependencyNodeClass<DeleteChannels>();

		enum_<DeleteChannels::Mode>( "Mode" )
			.value( "Keep", DeleteChannels::Keep )
			.value( "Delete", DeleteChannels::Delete )
		;
	}

	{
		scope s = GafferBindings::DependencyNodeClass<Merge>();

		enum_<Merge::Operation>( "Operation" )
			.value( "Add", Merge::Add )
			.value( "Atop", Merge::Atop )
			.value( "Divide", Merge::Divide )
			.value( "In", Merge::In )
			.value( "Out", Merge::Out )
			.value( "Mask", Merge::Mask )
			.value( "Matte", Merge::Matte )
			.value( "Multiply", Merge::Multiply )
			.value( "Over", Merge::Over )
			.value( "Subtract", Merge::Subtract )
			.value( "Difference", Merge::Difference )
			.value( "Under", Merge::Under )
			.value( "Min", Merge::Min )
			.value( "Max", Merge::Max )
		;
	}

	{
		scope s = DependencyNodeClass<Shuffle>();

		PlugClass<Shuffle::ChannelPlug>()
			.def( init<const char *, Plug::Direction, unsigned>(
					(
						boost::python::arg_( "name" )=GraphComponent::defaultName<Shuffle::ChannelPlug>(),
						boost::python::arg_( "direction" )=Plug::In,
						boost::python::arg_( "flags" )=Plug::Default
					)
				)
			)
			.def( init<const std::string &, const std::string &>() )
			.def( "__repr__", channelPlugRepr )
		;
	}

	Serialisation::registerSerialiser( Shuffle::ChannelPlug::staticTypeId(), new ChannelPlugSerialiser );

}
