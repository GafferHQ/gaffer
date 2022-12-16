//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "RandomBinding.h"

#include "GafferBindings/DependencyNodeBinding.h"

#include "Gaffer/Random.h"
#include "Gaffer/RandomChoice.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

Imath::Color3f randomColor( Random &r, int seed )
{
	IECorePython::ScopedGILRelease gilRelease;
	return r.randomColor( std::max( seed, 0 ) );
}

void setupWrapper( RandomChoice &r, const Gaffer::ValuePlug &p )
{
	IECorePython::ScopedGILRelease gilRelease;
	return r.setup( &p );
}

class RandomChoiceSerialiser : public NodeSerialiser
{

	bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
	{
		const RandomChoice *node = child->parent<RandomChoice>();
		if( child == node->outPlug() )
		{
			// We'll serialise a `setup()` call to construct this.
			return false;
		}
		return NodeSerialiser::childNeedsConstruction( child, serialisation );
	}

	std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const override
	{
		std::string result = NodeSerialiser::postConstructor( graphComponent, identifier, serialisation );

		const RandomChoice *node = static_cast<const RandomChoice *>( graphComponent );
		if( !node->outPlug() )
		{
			// `RandomChoice::setup()` hasn't been called yet.
			return result;
		}

		// Add a call to `setup()` to recreate the plugs.

		if( result.size() )
		{
			result += "\n";
		}

		const Serialiser *plugSerialiser = Serialisation::acquireSerialiser( node->outPlug() );
		result += identifier + ".setup( " + plugSerialiser->constructor( node->outPlug(), serialisation ) + " )\n";

		return result;
	}

};

} // namespace

void GafferModule::bindRandom()
{

	DependencyNodeClass<Random>()
		.def( "randomColor", &randomColor )
	;

	DependencyNodeClass<RandomChoice>()
		.def( "setup", &setupWrapper )
		.def( "canSetup", &RandomChoice::canSetup ).staticmethod( "canSetup" )
	;

	Serialisation::registerSerialiser( RandomChoice::staticTypeId(), new RandomChoiceSerialiser );

}
