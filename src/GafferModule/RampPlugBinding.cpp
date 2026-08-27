//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "RampPlugBinding.h"

#include "GafferBindings/PlugBinding.h"
#include "GafferBindings/ValuePlugBinding.h"

#include "Gaffer/Node.h"
#include "Gaffer/RampPlug.h"
#include "Gaffer/TypedPlug.h"

#include "IECorePython/IECoreBinding.h"
#include "IECorePython/RunTimeTypedBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

const IECore::InternedString g_interpolation( "interpolation" );
const IECore::InternedString g_omitParentNodePlugValues( "valuePlugSerialiser:omitParentNodePlugValues" );

class RampPlugSerialiser : public ValuePlugSerialiser
{

	public :

		std::string postConstructor( const Gaffer::GraphComponent *plug, const std::string &identifier, Serialisation &serialisation ) const override
		{
			std::string result = ValuePlugSerialiser::postConstructor( plug, identifier, serialisation );
			if( !omitValue( plug, serialisation ) )
			{
				// This isn't ideal, but the newly constructed ramp plug will already have child plugs representing the points for the
				// default value. So we get rid of those so the real value can be loaded appropriately by serialising plug constructors
				// (see below).
				result += identifier + ".clearPoints()\n";
			}
			return result;
		}

		bool childNeedsSerialisation( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
		{
			if( child->getName() == g_interpolation )
			{
				return ValuePlugSerialiser::childNeedsSerialisation( child, serialisation );
			}
			// Plug representing a point. These are added dynamically so we need to serialise them
			// if we want to serialise the value.
			return !omitValue( child, serialisation );
		}

	private :

		bool omitValue( const Gaffer::GraphComponent *plug, const Serialisation &serialisation ) const
		{
			return
				plug->ancestor<Node>() == serialisation.parent() &&
				Context::current()->get<bool>( g_omitParentNodePlugValues, false )
			;
		}

};

template<typename T>
ValuePlugPtr pointPlug( T &s, size_t index )
{
	return s.pointPlug( index );
}

template<typename T>
typename T::XPlugType::Ptr pointXPlug( T &s, size_t index )
{
	return s.pointXPlug( index );
}

template<typename T>
typename T::YPlugType::Ptr pointYPlug( T &s, size_t index )
{
	return s.pointYPlug( index );
}

template<typename T>
void setValue( T &plug, const typename T::ValueType &value )
{
	IECorePython::ScopedGILRelease r;
	return plug.setValue( value );
}

template<typename T>
typename T::ValueType getValue( const T &plug )
{
	// Must release GIL in case computation spawns threads which need
	// to reenter Python.
	IECorePython::ScopedGILRelease r;
	return plug.getValue();
}

template<typename T>
unsigned addPoint( T &plug )
{
	IECorePython::ScopedGILRelease r;
	return plug.addPoint();
}

template<typename T>
void removePoint( T &plug, unsigned pointIndex )
{
	IECorePython::ScopedGILRelease r;
	plug.removePoint( pointIndex );
}

template<typename T>
void clearPoints( T &plug )
{
	IECorePython::ScopedGILRelease r;
	plug.clearPoints();
}

template<typename T>
void bind()
{
	PlugClass<T>()
		.def( init<const std::string &, Plug::Direction, const typename T::ValueType &, unsigned>(
				(
					boost::python::arg_( "name" )=GraphComponent::defaultName<T>(),
					boost::python::arg_( "direction" )=Plug::In,
					boost::python::arg_( "defaultValue" )=typename T::ValueType(),
					boost::python::arg_( "flags" )=Plug::Default
				)
			)
		)
		.def( "defaultValue", &T::defaultValue, return_value_policy<copy_const_reference>() )
		.def( "setValue", &setValue<T> )
		.def( "getValue", &getValue<T> )
		.def( "numPoints", &T::numPoints )
		.def( "addPoint", &addPoint<T> )
		.def( "removePoint", &removePoint<T> )
		.def( "clearPoints", &clearPoints<T> )
		.def( "pointPlug",  &pointPlug<T> )
		.def( "pointXPlug", &pointXPlug<T> )
		.def( "pointYPlug", &pointYPlug<T> )
	;

	Serialisation::registerSerialiser( T::staticTypeId(), new RampPlugSerialiser );

}

} // namespace

void GafferModule::bindRampPlug()
{
	bind<RampffPlug>();
	bind<RampfColor3fPlug>();
	bind<RampfColor4fPlug>();
}
