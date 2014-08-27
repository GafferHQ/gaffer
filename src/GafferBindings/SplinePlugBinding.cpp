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

#include "IECorePython/RunTimeTypedBinding.h"

#include "Gaffer/Node.h"
#include "Gaffer/SplinePlug.h"
#include "Gaffer/TypedPlug.h"

#include "GafferBindings/SplinePlugBinding.h"
#include "GafferBindings/PlugBinding.h"
#include "GafferBindings/CompoundPlugBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace GafferBindings
{
namespace Detail
{

class SplinePlugSerialiser : public CompoundPlugSerialiser
{

	public :

		virtual std::string postConstructor( const Gaffer::GraphComponent *child, const std::string &identifier, const Serialisation &serialisation ) const
		{
			// this isn't ideal, but the newly constructed spline plug will already have child plugs representing the points for the
			// default value - so we get rid of those so the real value can be loaded appropriately (using the usual mechanism for
			// dynamic plugs). the alternative would be to have a special private SplinePlug constructor used only by the serialisation,
			// which wouldn't make the plugs in the first place.
			return CompoundPlugSerialiser::postConstructor( child, identifier, serialisation ) + identifier + ".clearPoints()\n";
		}

};

template<typename T>
static CompoundPlugPtr pointPlug( T &s, size_t index )
{
	return s.pointPlug( index );
}

template<typename T>
static typename T::XPlugType::Ptr pointXPlug( T &s, size_t index )
{
	return s.pointXPlug( index );
}

template<typename T>
static typename T::YPlugType::Ptr pointYPlug( T &s, size_t index )
{
	return s.pointYPlug( index );
}

template<typename T>
static void bind()
{
	typedef typename T::ValueType V;

	PlugClass<T>()
		.def( init<const std::string &, Plug::Direction, const V &, unsigned>(
				(
					boost::python::arg_( "name" )=GraphComponent::defaultName<T>(),
					boost::python::arg_( "direction" )=Plug::In,
					boost::python::arg_( "defaultValue" )=V(),
					boost::python::arg_( "flags" )=Plug::Default
				)
			)
		)
		.def( "defaultValue", &T::defaultValue, return_value_policy<copy_const_reference>() )
		.def( "setValue", &T::setValue )
		.def( "getValue", &T::getValue )
		.def( "numPoints", &T::numPoints )
		.def( "addPoint", &T::addPoint )
		.def( "removePoint", &T::removePoint )
		.def( "clearPoints", &T::clearPoints )
		.def( "pointPlug",  &pointPlug<T> )
		.def( "pointXPlug", &pointXPlug<T> )
		.def( "pointYPlug", &pointYPlug<T> )
	;

	Serialisation::registerSerialiser( T::staticTypeId(), new SplinePlugSerialiser );

}

} // namespace Detail

void bindSplinePlug()
{
	Detail::bind<SplineffPlug>();
	Detail::bind<SplinefColor3fPlug>();
}

} // namespace GafferBindings
