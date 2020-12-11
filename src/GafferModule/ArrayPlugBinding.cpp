//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "ArrayPlugBinding.h"

#include "GafferBindings/PlugBinding.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/BoxIO.h"

#include "IECorePython/RunTimeTypedBinding.h"

#include "boost/format.hpp"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

std::string repr( const ArrayPlug *plug )
{
	std::string result = Serialisation::classPath( plug ) + "( \"" + plug->getName().string() + "\", ";

	if( plug->direction()!=Plug::In )
	{
		result += "direction = " + PlugSerialiser::directionRepr( plug->direction() ) + ", ";
	}

	if( plug->minSize() != 1 )
	{
		result += boost::str( boost::format( "minSize = %d, " ) % plug->minSize() );
	}

	if( plug->maxSize() != Imath::limits<size_t>::max() )
	{
		result += boost::str( boost::format( "maxSize = %d, " ) % plug->maxSize() );
	}

	const unsigned flags = plug->getFlags();
	if( flags != Plug::Default )
	{
		result += "flags = " + PlugSerialiser::flagsRepr( flags ) + ", ";
	}

	if( !plug->resizeWhenInputsChange() )
	{
		result += "resizeWhenInputsChange = False,";
	}

	result += ")";

	return result;

}

class ArrayPlugSerialiser : public PlugSerialiser
{

	public :

		bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
		{
			auto arrayPlug = static_cast<const ArrayPlug *>( child->parent() );
			if( arrayPlug->direction() == Plug::Out && arrayPlug->parent<BoxIO>() )
			{
				// BoxIO serialisation is different than most nodes, in that
				// the internal connection is made _before_ children are added
				// to the input ArrayPlug. The existence of the connection means
				// that when a child is added to the input plug, an equivalent
				// child is added to the output plug automatically. Hence we don't
				// need to serialise an explicit constructor for this child.
				/// \todo Figure out how we can do this cleanly, without the
				/// ArrayPlugSerialiser needing knowledge of BoxIO.
				return false;
			}
			return PlugSerialiser::childNeedsConstruction( child, serialisation );
		}

		std::string constructor( const Gaffer::GraphComponent *graphComponent, Serialisation &serialisation ) const override
		{
			return ::repr( static_cast<const ArrayPlug *>( graphComponent ) );
		}

};

void resize( ArrayPlug &p, size_t size )
{
	IECorePython::ScopedGILRelease gilRelease;
	p.resize( size );
}

PlugPtr next( ArrayPlug &p )
{
	IECorePython::ScopedGILRelease gilRelease;
	return p.next();
}

} // namespace

void GafferModule::bindArrayPlug()
{
	PlugClass<ArrayPlug>()
		.def(	init< const std::string &, Plug::Direction, PlugPtr, size_t, size_t, unsigned, bool >
				(
					(
						arg( "name" ) = GraphComponent::defaultName<ArrayPlug>(),
						arg( "direction" ) = Plug::In,
						arg( "element" ) = PlugPtr(),
						arg( "minSize" ) = 1,
						arg( "maxSize" ) = Imath::limits<size_t>::max(),
						arg( "flags" ) = Plug::Default,
						arg( "resizeWhenInputsChange" ) = true
					)
				)
		)
		.def( "minSize", &ArrayPlug::minSize )
		.def( "maxSize", &ArrayPlug::maxSize )
		.def( "resize", &resize )
		.def( "resizeWhenInputsChange", &ArrayPlug::resizeWhenInputsChange )
		.def( "next", &next )
		.def( "__repr__", &repr )
	;

	Serialisation::registerSerialiser( ArrayPlug::staticTypeId(), new ArrayPlugSerialiser );

}
