//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "CollectBinding.h"

#include "GafferBindings/ComputeNodeBinding.h"

#include "Gaffer/Collect.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

Gaffer::ValuePlugPtr addInputWrapper( Collect &c, const Gaffer::ValuePlug &p )
{
	IECorePython::ScopedGILRelease gilRelease;
	return c.addInput( &p );
}

void removeInputWrapper( Collect &c, Gaffer::ValuePlug &p )
{
	IECorePython::ScopedGILRelease gilRelease;
	return c.removeInput( &p );
}

class CollectSerialiser : public NodeSerialiser
{

	std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const override
	{
		std::string result = NodeSerialiser::postConstructor( graphComponent, identifier, serialisation );

		const Collect *node = static_cast<const Collect *>( graphComponent );
		for( auto &input : ValuePlug::InputRange( *node->inPlug() ) )
		{
			const Serialiser *plugSerialiser = Serialisation::acquireSerialiser( input.get() );
			result += identifier + ".addInput( " + plugSerialiser->constructor( input.get(), serialisation ) + " )\n";
		}

		return result;
	}

};

} // namespace

void GafferModule::bindCollect()
{

	DependencyNodeClass<Collect>()
		.def( "canAddInput", &Collect::canAddInput )
		.def( "addInput", &addInputWrapper )
		.def( "removeInput", &removeInputWrapper )
		.def( "outputPlugForInput", (ValuePlug *(Collect::*)( const ValuePlug *))&Collect::outputPlugForInput, return_value_policy<IECorePython::CastToIntrusivePtr>() )
		.def( "inputPlugForOutput", (ValuePlug *(Collect::*)( const ValuePlug *))&Collect::inputPlugForOutput, return_value_policy<IECorePython::CastToIntrusivePtr>() )
	;

	Serialisation::registerSerialiser( Collect::staticTypeId(), new CollectSerialiser );

}
