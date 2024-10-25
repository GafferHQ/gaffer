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

#include "GafferML/DataToTensor.h"
#include "GafferML/ImageToTensor.h"
#include "GafferML/Inference.h"
#include "GafferML/Tensor.h"
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

template<typename T>
TensorPtr tensorConstructorWrapper( const boost::intrusive_ptr<T> &data, object pythonShape )
{
	std::vector<int64_t> shape;
	boost::python::container_utils::extend_container( shape, pythonShape );
	return new Tensor( data, shape );
}

list shapeWrapper( const Tensor &tensor )
{
	list result;
	for( const auto &x : tensor.shape() )
	{
		result.append( x );
	}
	return result;
}

void loadModelWrapper( Inference &inference )
{
	IECorePython::ScopedGILRelease gilRelease;
	inference.loadModel();
}

} // namespace

BOOST_PYTHON_MODULE( _GafferML )
{

	IECorePython::RunTimeTypedClass<GafferML::Tensor>()
		.def( init<>() )
		.def( "__init__", make_constructor( tensorConstructorWrapper<FloatVectorData> ) )
		.def( "__init__", make_constructor( tensorConstructorWrapper<DoubleVectorData> ) )
		.def( "__init__", make_constructor( tensorConstructorWrapper<UShortVectorData> ) )
		.def( "__init__", make_constructor( tensorConstructorWrapper<ShortVectorData> ) )
		.def( "__init__", make_constructor( tensorConstructorWrapper<UIntVectorData> ) )
		.def( "__init__", make_constructor( tensorConstructorWrapper<IntVectorData> ) )
		.def( "__init__", make_constructor( tensorConstructorWrapper<UInt64VectorData> ) )
		.def( "__init__", make_constructor( tensorConstructorWrapper<Int64VectorData> ) )
		.def( "asData", (IECore::DataPtr (Tensor::*)())&Tensor::asData )
		.def( "shape", &shapeWrapper )
	;

	GafferBindings::TypedObjectPlugClass<GafferML::TensorPlug>();

	GafferBindings::DependencyNodeClass<DataToTensor>();
	GafferBindings::DependencyNodeClass<ImageToTensor>();
	GafferBindings::DependencyNodeClass<TensorToImage>();
	GafferBindings::DependencyNodeClass<TensorReader>();
	GafferBindings::DependencyNodeClass<Inference>()
		.def( "loadModel", &loadModelWrapper )
	;

}
