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
#include "GafferML/TensorReader.h"
#include "GafferML/TensorToImage.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/TypedObjectPlugBinding.h"

using namespace boost::python;
using namespace IECore;
using namespace GafferML;
using namespace GafferBindings;

namespace
{

/// TODO : WHERE DO I REALLY BELONG? MAYBE TENSORDATA SHOULD HAVE SOME CONVENIENCE
/// METHODS INSTEAD OF USING ONLY THE ORT API?
list shapeWrapper( const TensorData &data )
{
	const auto s = data.value.GetTensorTypeAndShapeInfo().GetShape();
	list o;
	for( const auto &x : s )
	{
		o.append( x );
	}
	return o;
}

IECore::DataPtr dataWrapper( const TensorData &data, bool copy )
{
	if( !data.data )
	{
		const size_t count = data.value.GetTensorTypeAndShapeInfo().GetElementCount();
		const float *source = data.value.GetTensorData<float>();
		// TODO : MAYBE WE SHOULD ALWAYS BACK THE TENSOR WITH DATA?
		// OR AT THE VERY LEAST, MOVE THIS FUNCTIONALITY INTO TENSORDATA ITSELF
		FloatVectorDataPtr result = new FloatVectorData;
		result->writable().insert(
			result->writable().end(),
			source, source + count
		);
		return result;
	}

	return copy ? data.data->copy() : boost::const_pointer_cast<IECore::Data>( data.data );
}

void loadModelWrapper( Inference &inference )
{
	IECorePython::ScopedGILRelease gilRelease;
	inference.loadModel();
}

} // namespace

BOOST_PYTHON_MODULE( _GafferML )
{

	IECorePython::RunTimeTypedClass<GafferML::TensorData>()
		.def( "data", &dataWrapper, ( arg( "_copy" ) = true ) )
		.def( "shape", &shapeWrapper )
	;

	GafferBindings::TypedObjectPlugClass<GafferML::TensorPlug>();

	GafferBindings::DependencyNodeClass<ImageToTensor>();
	GafferBindings::DependencyNodeClass<TensorToImage>();
	GafferBindings::DependencyNodeClass<TensorReader>();
	GafferBindings::DependencyNodeClass<Inference>()
		.def( "loadModel", &loadModelWrapper )
	;

}
