//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferML/ImageToTensor.h"
#include "GafferML/Inference.h"
#include "GafferML/TensorPlug.h"
#include "GafferML/TensorToImage.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/TypedObjectPlugBinding.h"

using namespace boost::python;
using namespace GafferML;
using namespace GafferBindings;

namespace
{

void loadModelWrapper( Inference &inference, const std::filesystem::path &model )
{
	IECorePython::ScopedGILRelease gilRelease;
	inference.loadModel( model );
}

class InferenceSerialiser : public GafferBindings::NodeSerialiser
{

	std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const override
	{
		std::string result = GafferBindings::NodeSerialiser::postConstructor( graphComponent, identifier, serialisation );
		const Inference *inference = static_cast<const Inference *>( graphComponent );
		const std::string model = inference->modelPlug()->getValue();
		if( model.size() )
		{
			result += fmt::format( "{}.loadModel( \"{}\" )\n", identifier, model );
		}

		return result;
	}

};


} // namespace

BOOST_PYTHON_MODULE( _GafferML )
{

	IECorePython::RunTimeTypedClass<GafferML::TensorData>();

	GafferBindings::TypedObjectPlugClass<GafferML::TensorPlug>();

	GafferBindings::DependencyNodeClass<ImageToTensor>();
	GafferBindings::DependencyNodeClass<TensorToImage>();
	GafferBindings::DependencyNodeClass<Inference>()
		.def( "loadModel", &loadModelWrapper )
	;

	GafferBindings::Serialisation::registerSerialiser( Inference::staticTypeId(), new InferenceSerialiser() );

}
