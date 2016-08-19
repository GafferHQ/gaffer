//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, John Haddon. All rights reserved.
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

#include "GafferBindings/DependencyNodeBinding.h"

#include "GafferImage/FlatToDeep.h"
#include "GafferImage/DeepMerge.h"
#include "GafferImage/DeepState.h"
#include "GafferImage/Empty.h"

#include "DeepNodeBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace GafferImage;

void GafferImageModule::bindDeepNodes()
{
	{
		scope s = DependencyNodeClass<FlatToDeep>();
		enum_<FlatToDeep::ZMode>( "ZMode" )
			.value( "Constant", FlatToDeep::ZMode::Constant )
			.value( "Channel", FlatToDeep::ZMode::Channel )
		;
		enum_<FlatToDeep::ZBackMode>( "ZBackMode" )
			.value( "None", FlatToDeep::ZBackMode::None )
			.value( "Thickness", FlatToDeep::ZBackMode::Thickness )
			.value( "Channel", FlatToDeep::ZBackMode::Channel )
		;
	}
	DependencyNodeClass<DeepMerge>();
	{
		scope s = DependencyNodeClass<DeepState>();

		enum_<DeepState::TargetState>( "TargetState" )
			.value( "Sorted", DeepState::TargetState::Sorted )
			.value( "Tidy", DeepState::TargetState::Tidy )
			.value( "Flat", DeepState::TargetState::Flat )
		;
	}
	DependencyNodeClass<Empty>();
}
