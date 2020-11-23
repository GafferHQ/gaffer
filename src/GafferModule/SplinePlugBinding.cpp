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

#include "SplinePlugBinding.h"

#include "GafferBindings/PlugBinding.h"
#include "GafferBindings/ValuePlugBinding.h"

#include "Gaffer/Node.h"
#include "Gaffer/SplinePlug.h"
#include "Gaffer/TypedPlug.h"

#include "IECorePython/IECoreBinding.h"
#include "IECorePython/RunTimeTypedBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

template<typename T>
std::string splineDefinitionRepr( object x )
{
	std::stringstream s;
	const std::string name = extract<std::string>( x.attr( "__class__").attr( "__name__" ) );
	s << "Gaffer." << name << "( ";
	const T splineDefinition = extract<T>( x );
	s << "(";
	int i = 0;
	int l = splineDefinition.points.size();
	typename T::PointContainer::const_iterator it;
	for( it=splineDefinition.points.begin(); it!=splineDefinition.points.end(); it++, i++ )
	{
		// TODO - without this const_cast I get a link error because the const version of repr<Color3f>
		// hasn't been defined
		s << " ( " << it->first << ", " << IECorePython::repr( const_cast<typename T::YType&>( it->second ) ) << " )";
		if( i!=l-1 )
		{
			s << ",";
		}
	}
	s << "), ";
	s << "Gaffer.SplineDefinitionInterpolation( " << splineDefinition.interpolation << " )";
	s << ")";
	return s.str();
}

template<typename T>
static T *splineDefinitionConstruct( object o, const SplineDefinitionInterpolation &interpolation )
{
	typename T::PointContainer points;
	int s = extract<int>( o.attr( "__len__" )() );
	for( int i=0; i<s; i++ )
	{
		object e = o[i];
		int es = extract<int>( e.attr( "__len__" )() );
		if( es!=2 )
		{
			throw IECore::Exception( "Each entry in the point sequence must contain two values." );
		}
		object xo = e[0];
		object yo = e[1];
		float x = extract<float>( xo );
		typename T::YType y = extract<typename T::YType>( yo );
		points.insert( typename T::PointContainer::value_type( x, y ) );
	}
	return new T( points, interpolation );
}

template<typename T>
static boost::python::tuple splineDefinitionPoints( const T &s )
{
	boost::python::list p;
	typename T::PointContainer::const_iterator it;
	for( it=s.points.begin(); it!=s.points.end(); it++ )
	{
		p.append( make_tuple( it->first, it->second ) );
	}
	return boost::python::tuple( p );
}

template<typename T>
void bindSplineDefinition( const char *name)
{
	class_<T>( name )
		.def( "__init__", make_constructor( &splineDefinitionConstruct<T> ) )
		.def( "__repr__", &splineDefinitionRepr<T> )
		.def( "points", &splineDefinitionPoints<T>, "Read only access to the control points as a tuple of tuples of ( x, y ) pairs." )
		.def_readwrite("interpolation", &T::interpolation)
		.def( self==self )
		.def( self!=self )
		.def( "spline", &T::spline )
		.def( "trimEndPoints", &T::trimEndPoints )
	;
}

const IECore::InternedString g_interpolation( "interpolation" );
const IECore::InternedString g_omitParentNodePlugValues( "valuePlugSerialiser:omitParentNodePlugValues" );

class SplinePlugSerialiser : public ValuePlugSerialiser
{

	public :

		std::string postConstructor( const Gaffer::GraphComponent *plug, const std::string &identifier, const Serialisation &serialisation ) const override
		{
			std::string result = ValuePlugSerialiser::postConstructor( plug, identifier, serialisation );
			if( !omitValue( plug, serialisation ) )
			{
				// This isn't ideal, but the newly constructed spline plug will already have child plugs representing the points for the
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

	Serialisation::registerSerialiser( T::staticTypeId(), new SplinePlugSerialiser );

}

} // namespace

void GafferModule::bindSplinePlug()
{
	enum_<SplineDefinitionInterpolation>( "SplineDefinitionInterpolation" )
		.value( "Linear", SplineDefinitionInterpolationLinear )
		.value( "CatmullRom", SplineDefinitionInterpolationCatmullRom )
		.value( "BSpline", SplineDefinitionInterpolationBSpline )
		.value( "MonotoneCubic", SplineDefinitionInterpolationMonotoneCubic )
	;

	bindSplineDefinition<SplineDefinitionff >( "SplineDefinitionff" );
	bindSplineDefinition<SplineDefinitionfColor3f >( "SplineDefinitionfColor3f" );
	bindSplineDefinition<SplineDefinitionfColor4f >( "SplineDefinitionfColor4f" );
	bind<SplineffPlug>();
	bind<SplinefColor3fPlug>();
	bind<SplinefColor4fPlug>();
}
