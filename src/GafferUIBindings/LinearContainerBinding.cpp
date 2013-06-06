//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

#include "boost/python.hpp"

#include "GafferUIBindings/LinearContainerBinding.h"
#include "GafferUIBindings/GadgetBinding.h"
#include "GafferUI/LinearContainer.h"

#include "Gaffer/Node.h"

#include "IECorePython/RunTimeTypedBinding.h"

using namespace boost::python;
using namespace GafferUIBindings;
using namespace GafferUI;

void GafferUIBindings::bindLinearContainer()
{
	/// \todo It would be nice if we could make this behave a lot like the ListContainer
	IECorePython::RunTimeTypedClass<LinearContainer> c;
		c.def( "setOrientation", &LinearContainer::setOrientation )
		.def( "getOrientation", &LinearContainer::getOrientation )
		.def( "setAlignment", &LinearContainer::setAlignment )
		.def( "getAlignment", &LinearContainer::getAlignment )
		.def( "setSpacing", &LinearContainer::setSpacing )
		.def( "getSpacing", &LinearContainer::getSpacing )
		.def( "setDirection", &LinearContainer::setDirection )
		.def( "getDirection", &LinearContainer::getDirection )
		.GAFFERUIBINDINGS_DEFGADGETWRAPPERFNS( LinearContainer )
	;
	
	scope s = c;
	
	enum_<LinearContainer::Orientation>( "Orientation" )
		.value( "InvalidOrientation", LinearContainer::InvalidOrientation )
		.value( "X", LinearContainer::X )
		.value( "Y", LinearContainer::Y )
		.value( "Z", LinearContainer::Z )
	;
	
	enum_<LinearContainer::Alignment>( "Alignment" )
		.value( "InvalidAlignment", LinearContainer::InvalidAlignment )
		.value( "Min", LinearContainer::Min )
		.value( "Centre", LinearContainer::Centre )
		.value( "Max", LinearContainer::Max )
	;
	
	enum_<LinearContainer::Direction>( "Direction" )
		.value( "InvalidDirection", LinearContainer::InvalidDirection )
		.value( "Increasing", LinearContainer::Increasing )
		.value( "Decreasing", LinearContainer::Decreasing )
	;
	
	// we have to define the constructor after the enums, as they must be registered in order for boost::python to figure out the correct
	// python values for the default arguments
	c.def( init< optional<const std::string &, LinearContainer::Orientation, LinearContainer::Alignment, float, LinearContainer::Direction> >(
			(
				arg_( "name" )=Gaffer::GraphComponent::defaultName<LinearContainer>(),
				arg_( "orientation" )=LinearContainer::X,
				arg_( "alignment" )=LinearContainer::Centre,
				arg_( "spacing" )=0.0f,
				arg_( "direction" )=LinearContainer::Increasing
			)
		)
	);

}
