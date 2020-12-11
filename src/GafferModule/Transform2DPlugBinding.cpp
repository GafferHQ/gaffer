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
//      * Neither the name of Image Engine Design nor the names of
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

#include "Transform2DPlugBinding.h"

#include "GafferBindings/ValuePlugBinding.h"

#include "Gaffer/Transform2DPlug.h"

using namespace boost::python;
using namespace Imath;
using namespace GafferBindings;
using namespace Gaffer;


namespace
{

class Transform2DPlugSerialiser : public ValuePlugSerialiser
{

	public :

		bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
		{
			// The children will be created by the constructor
			return false;
		}

		std::string constructor( const Gaffer::GraphComponent *graphComponent, Serialisation &serialisation ) const override
		{
			return repr( static_cast<const Transform2DPlug *>( graphComponent ), &serialisation );
		}

		static std::string repr( const Transform2DPlug *plug, const Serialisation *serialisation )
		{
			std::string result = "Gaffer.Transform2DPlug( \"" + plug->getName().string() + "\", ";

			if( plug->direction() != Plug::In )
			{
				result += "direction = " + PlugSerialiser::directionRepr( plug->direction() ) + ", ";
			}

			auto appendDefault = [&result]( const V2f &d, const V2f &defaultD, const char *name )
			{
				static boost::format formatter( "%1% = imath.V2f( %2%, %3% ), " );
				if( d != defaultD )
				{
					result += boost::str( formatter % name % d.x % d.y );
				}
			};
			appendDefault( plug->translatePlug()->defaultValue(), V2f( 0 ), "defaultTranslate" );
			if( plug->rotatePlug()->defaultValue() != 0.0f )
			{
				result += "defaultRotate = " + std::to_string( plug->rotatePlug()->defaultValue() ) + ", ";
			}
			appendDefault( plug->scalePlug()->defaultValue(), V2f( 1 ), "defaultScale" );
			appendDefault( plug->pivotPlug()->defaultValue(), V2f( 0 ), "defaultPivot" );

			const unsigned flags = plug->getFlags();
			if( flags != Plug::Default )
			{
				result += "flags = " + PlugSerialiser::flagsRepr( flags ) + ", ";
			}

			result += ")";
			return result;
		}

};

std::string repr( const Transform2DPlug *plug )
{
	Serialisation s( plug );
	return Transform2DPlugSerialiser::repr( plug, &s );
}

} // namespace

void GafferModule::bindTransform2DPlug()
{
	PlugClass<Transform2DPlug>()
		.def(
			init<const std::string &, Gaffer::Plug::Direction, const V2f &, float, const V2f &, const V2f &, unsigned >
			(
				(
					arg( "name" ) = Gaffer::GraphComponent::defaultName<Transform2DPlug>(),
					arg( "direction" ) = Gaffer::Plug::In,
					arg( "defaultTranslate" ) = V2f( 0 ),
					arg( "defaultRotate" ) = 0.0f,
					arg( "defaultScale" ) = V2f( 1 ),
					arg( "defaultPivot" ) = V2f( 0 ),
					arg( "flags" ) = Gaffer::Plug::Default
				)
			)
		)
		.def( "matrix", &Transform2DPlug::matrix )
		.def( "repr", &repr )
	;

	Serialisation::registerSerialiser( Gaffer::Transform2DPlug::staticTypeId(), new Transform2DPlugSerialiser );
}
