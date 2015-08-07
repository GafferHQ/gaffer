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

#include "IECorePython/IECoreBinding.h"
#include "IECorePython/RunTimeTypedBinding.h"
#include "IECorePython/ScopedGILRelease.h"

#include "Gaffer/CompoundNumericPlug.h"

#include "GafferBindings/ValuePlugBinding.h"
#include "GafferBindings/CompoundNumericPlugBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

template<typename T>
std::string compoundNumericPlugRepr( const T *plug )
{
	return maskedCompoundNumericPlugRepr( plug, Plug::All );
}

template<typename T>
class CompoundNumericPlugSerialiser : public ValuePlugSerialiser
{

	protected :

		// Ideally we'll serialise the value as a single getValue() call for this plug,
		// but we can't do that if any of the children have input connections.
		virtual bool valueNeedsSerialisation( const Gaffer::ValuePlug *plug, const Serialisation &serialisation ) const
		{
			if( !ValuePlugSerialiser::valueNeedsSerialisation( plug, serialisation ) )
			{
				return false;
			}

			for( PlugIterator it( plug ); it != it.end(); ++it )
			{
				if( (*it)->getInput<Plug>() )
				{
					return false;
				}
			}
			return true;
		}

};

template<typename T>
void setValue( T *plug, const typename T::ValueType value )
{
	// we use a GIL release here to prevent a lock in the case where this triggers a graph
	// evaluation which decides to go back into python on another thread:
	IECorePython::ScopedGILRelease r;
	plug->setValue( value );
}

template<typename T>
typename T::ValueType getValue( const T *plug )
{
	// Must release GIL in case computation spawns threads which need
	// to reenter Python.
	IECorePython::ScopedGILRelease r;
	return plug->getValue();
}

template<typename T>
void gang( T *plug )
{
	// Must release GIL in case this triggers a graph evaluation
	// which wants to enter Python on another thread.
	IECorePython::ScopedGILRelease r;
	plug->gang();
}

template<typename T>
void ungang( T *plug )
{
	// Must release GIL in case this triggers a graph evaluation
	// which wants to enter Python on another thread.
	IECorePython::ScopedGILRelease r;
	plug->ungang();
}

template<typename T>
void bind()
{
	typedef typename T::ValueType V;

	PlugClass<T>()
		.def( init<const char *, Plug::Direction, V, V, V, unsigned>(
				(
					boost::python::arg_( "name" )=GraphComponent::defaultName<T>(),
					boost::python::arg_( "direction" )=Plug::In,
					boost::python::arg_( "defaultValue" )=V( 0 ),
					boost::python::arg_( "minValue" )=V(Imath::limits<typename V::BaseType>::min()),
					boost::python::arg_( "maxValue" )=V(Imath::limits<typename V::BaseType>::max()),
					boost::python::arg_( "flags" )=Plug::Default
				)
			)
		)
		.def( "defaultValue", &T::defaultValue )
		.def( "hasMinValue", &T::hasMinValue )
		.def( "hasMaxValue", &T::hasMaxValue )
		.def( "minValue", &T::minValue )
		.def( "maxValue", &T::maxValue )
		.def( "setValue", &setValue<T> )
		.def( "getValue", &getValue<T> )
		.def( "canGang", &T::canGang )
		.def( "gang", &gang<T> )
		.def( "isGanged", &T::isGanged )
		.def( "ungang", &ungang<T> )
	;

	Serialisation::registerSerialiser( T::staticTypeId(), new CompoundNumericPlugSerialiser<T>() );

}

} // namespace

void GafferBindings::bindCompoundNumericPlug()
{
	bind<V2fPlug>();
	bind<V3fPlug>();
	bind<V2iPlug>();
	bind<V3iPlug>();
	bind<Color3fPlug>();
	bind<Color4fPlug>();
}
