//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#include "DotBinding.h"

#include "GafferBindings/DependencyNodeBinding.h"

#include "Gaffer/Dot.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

void setup( Dot &dot, const Plug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	dot.setup( &plug );
}

/// \todo This is almost identical to the serialisers for Switch, ContextProcessor and Loop.
/// Can we somehow consolidate them all into one? Or should `setup()` calls be supported by
/// the standard serialiser, driven by some metadata?
class DotSerialiser : public NodeSerialiser
{

	bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
	{
		const Dot *dot = child->parent<Dot>();
		if( child == dot->inPlug() || child == dot->outPlug() )
		{
			// We'll serialise a `setup()` call to construct these.
			return false;
		}
		return NodeSerialiser::childNeedsConstruction( child, serialisation );
	}

	std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const override
	{
		std::string result = NodeSerialiser::postConstructor( graphComponent, identifier, serialisation );

		auto dot = static_cast<const Dot *>( graphComponent );
		if( !dot->inPlug() )
		{
			// Dot::setup() hasn't been called yet.
			return result;
		}

		// Only serialise a call to setup() when we need to construct this node
		if( !Serialisation::acquireSerialiser( graphComponent->parent() )->childNeedsConstruction(
			graphComponent, serialisation ) )
		{
			return result;
		}

		if( result.size() )
		{
			result += "\n";
		}

		// Add a call to `setup()` to recreate the plugs.

		/// \todo Avoid creating a temporary plug.
		PlugPtr plug = dot->inPlug()->createCounterpart( "in", Plug::In );
		plug->setFlags( Plug::Dynamic, false );

		const Serialiser *plugSerialiser = Serialisation::acquireSerialiser( plug.get() );
		result += identifier + ".setup( " + plugSerialiser->constructor( plug.get(), serialisation ) + " )\n";

		return result;
	}

};

} // namespace

void GafferModule::bindDot()
{

	scope s = DependencyNodeClass<Dot>()
		.def( "setup", &setup )
	;

	enum_<Dot::LabelType>( "LabelType" )
		.value( "None", Dot::None )
		.value( "None_", Dot::None )
		.value( "NodeName", Dot::NodeName )
		.value( "UpstreamNodeName", Dot::UpstreamNodeName )
		.value( "Custom", Dot::Custom )
	;

	Serialisation::registerSerialiser( Dot::staticTypeId(), new DotSerialiser );

}
