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
#include "boost/format.hpp"

#include "IECorePython/RunTimeTypedBinding.h"

#include "Gaffer/ArrayPlug.h"
#include "GafferBindings/CompoundPlugBinding.h"
#include "GafferBindings/ArrayPlugBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

static std::string maskedRepr( const ArrayPlug *plug, unsigned flagsMask )
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
	
	const unsigned flags = plug->getFlags() & flagsMask;
	if( flags != Plug::Default )
	{
		result += "flags = " + PlugSerialiser::flagsRepr( flags ) + ", ";
	}
			
	result += ")";

	return result;

}

static std::string repr( const ArrayPlug *plug )
{
	return maskedRepr( plug, Plug::All );
}

class ArrayPlugSerialiser : public CompoundPlugSerialiser
{

	public :
	
		virtual std::string constructor( const Gaffer::GraphComponent *graphComponent ) const
		{
			return maskedRepr( static_cast<const ArrayPlug *>( graphComponent ), Plug::All & ~Plug::ReadOnly );
		}
		
};

void GafferBindings::bindArrayPlug()
{
	IECorePython::RunTimeTypedClass<ArrayPlug>()
		.def(	init< const std::string &, Plug::Direction, PlugPtr, size_t, size_t, unsigned >
				(
					(
						arg( "name" ) = GraphComponent::defaultName<ArrayPlug>(),
						arg( "direction" ) = Plug::In,
						arg( "element" ) = PlugPtr(),
						arg( "minSize" ) = 1,
						arg( "maxSize" ) = Imath::limits<size_t>::max(),
						arg( "flags" ) = Plug::Default
					)
				)	
		)
		.def( "minSize", &ArrayPlug::minSize )
		.def( "maxSize", &ArrayPlug::maxSize )
		.GAFFERBINDINGS_DEFPLUGWRAPPERFNS( ArrayPlug )
		.def( "__repr__", &repr )
	;

	Serialisation::registerSerialiser( ArrayPlug::staticTypeId(), new ArrayPlugSerialiser );

}
