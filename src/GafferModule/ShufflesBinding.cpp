//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Image Engine Design Inc. All rights reserved.
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

#include "ShufflesBinding.h"

#include "GafferBindings/ValuePlugBinding.h"

#include "Gaffer/ShufflePlug.h"

#include "IECore/CompoundData.h"

#include "IECorePython/ScopedGILRelease.h"

using namespace boost::python;
using namespace IECore;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

CompoundObjectPtr shuffleCompoundObject( const ShufflesPlug &shufflesPlug, CompoundObject &source )
{
	IECorePython::ScopedGILRelease gilRelease;

	CompoundObjectPtr result = new CompoundObject;
	result->members() = shufflesPlug.shuffle<CompoundObject::ObjectMap>( source.members() );
	return result;
}

CompoundDataPtr shuffleCompoundData( const ShufflesPlug &shufflesPlug, CompoundData &source )
{
	IECorePython::ScopedGILRelease gilRelease;
	return new CompoundData( shufflesPlug.shuffle<CompoundDataMap>( source.readable() ) );
}

class ShufflePlugSerialiser : public ValuePlugSerialiser
{
	public :

		bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
		{
			return false;
		}
};

} // namespace

void GafferModule::bindShuffles()
{
	PlugClass<ShufflePlug>()
		.def(
			init<const std::string &, Plug::Direction, unsigned>(
				(
					arg_( "name" ) = GraphComponent::defaultName<ShufflePlug>(),
					arg_( "direction" ) = Plug::In,
					arg_( "flags" ) = Plug::Default
				)
			)
		)
		.def(
			init<const std::string &, const std::string &, bool, bool>(
				(
					arg_( "source" ),
					arg_( "destination" ),
					arg_( "deleteSource" ) = false,
					arg_( "enabled" ) = true
				)
			)
		)
	;

	Serialisation::registerSerialiser( ShufflePlug::staticTypeId(), new ShufflePlugSerialiser );

	PlugClass<ShufflesPlug>()
		.def(
			init<const std::string &, Plug::Direction, unsigned>(
				(
					arg_( "name" ) = GraphComponent::defaultName<ShufflesPlug>(),
					arg_( "direction" ) = Plug::In,
					arg_( "flags" ) = Plug::Default
				)
			)
		)
		.def( "shuffle", &shuffleCompoundObject, ( arg( "sourceContainer" ) ) )
		.def( "shuffle", &shuffleCompoundData, ( arg( "sourceContainer" ) ) )
	;

}
