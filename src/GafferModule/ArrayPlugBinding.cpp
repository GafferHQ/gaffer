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

#include "fmt/format.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

std::string constructor( const ArrayPlug *plug, Serialisation *serialisation = nullptr )
{
	std::string result = Serialisation::classPath( plug ) + "( \"" + plug->getName().string() + "\", ";

	if( plug->direction()!=Plug::In )
	{
		result += "direction = " + PlugSerialiser::directionRepr( plug->direction() ) + ", ";
	}

	if( serialisation && plug->elementPrototype() )
	{
		const Serialisation::Serialiser *plugSerialiser = Serialisation::acquireSerialiser( plug->elementPrototype() );
		result += fmt::format( "elementPrototype = {}, ", plugSerialiser->constructor( plug->elementPrototype(), *serialisation ) );
	}

	if( plug->minSize() != 1 )
	{
		result += fmt::format( "minSize = {}, ", plug->minSize() );
	}

	if( plug->maxSize() != std::numeric_limits<size_t>::max() )
	{
		result += fmt::format( "maxSize = {}, ", plug->maxSize() );
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

std::string repr( const ArrayPlug &plug )
{
	return constructor( &plug );
}

class ArrayPlugSerialiser : public PlugSerialiser
{

	public :

		bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
		{
			// We'll call `resize()` in our `postConstructor()` to create all
			// the child elements.
			return false;
		}

		std::string constructor( const Gaffer::GraphComponent *graphComponent, Serialisation &serialisation ) const override
		{
			return ::constructor( static_cast<const ArrayPlug *>( graphComponent ), &serialisation );
		}

		std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const override
		{
			std::string result = PlugSerialiser::postConstructor( graphComponent, identifier, serialisation );

			auto arrayPlug = static_cast<const ArrayPlug *>( graphComponent );
			if( arrayPlug->children().size() != arrayPlug->minSize() )
			{
				if( result.size() )
				{
					result += "\n";
				}

				result += fmt::format( "{}.resize( {} )\n", identifier, arrayPlug->children().size() );
			}

			return result;
		}

};

PlugPtr elementPrototype( ArrayPlug &p, bool copy )
{
	// By default we copy, because allowing an unsuspecting Python
	// user to modify the prototype would lead to arrays with inconsistent
	// elements. We're protected by `const` in C++ but not so in Python.
	if( !copy || !p.elementPrototype() )
	{
		return const_cast<Plug *>( p.elementPrototype() );
	}
	return p.elementPrototype()->createCounterpart( p.elementPrototype()->getName(), p.elementPrototype()->direction() );
}

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
						arg( "elementPrototype" ) = PlugPtr(),
						arg( "minSize" ) = 1,
						arg( "maxSize" ) = std::numeric_limits<size_t>::max(),
						arg( "flags" ) = Plug::Default,
						arg( "resizeWhenInputsChange" ) = true
					)
				)
		)
		.def( "elementPrototype", &elementPrototype, ( arg( "_copy" ) = true ) )
		.def( "minSize", &ArrayPlug::minSize )
		.def( "maxSize", &ArrayPlug::maxSize )
		.def( "resize", &resize )
		.def( "resizeWhenInputsChange", &ArrayPlug::resizeWhenInputsChange )
		.def( "next", &next )
		.def( "__repr__", &repr )
	;

	Serialisation::registerSerialiser( ArrayPlug::staticTypeId(), new ArrayPlugSerialiser );

}
