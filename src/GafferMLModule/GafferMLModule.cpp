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

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/TypedObjectPlugBinding.h"

#include "GafferML/DataToTensor.h"
#include "GafferML/Tensor.h"
#include "GafferML/TensorPlug.h"

#include "IECorePython/RunTimeTypedBinding.h"

#include "boost/python/suite/indexing/container_utils.hpp"

#include "fmt/format.h"

using namespace boost::python;
using namespace IECore;
using namespace Gaffer;
using namespace GafferML;
using namespace GafferBindings;

namespace
{

TensorPtr tensorConstructorWrapper( const DataPtr &data, object pythonShape )
{
	if( pythonShape != object() )
	{
		std::vector<int64_t> shape;
		boost::python::container_utils::extend_container( shape, pythonShape );
		return new Tensor( data, shape );
	}
	else
	{
		return new Tensor( data );
	}
}

list tensorShapeWrapper( const Tensor &tensor )
{
	list result;
	for( const auto &x : tensor.shape() )
	{
		result.append( x );
	}
	return result;
}

std::string tensorRepr( const Tensor &tensor )
{
	if( !tensor.value() )
	{
		// The most common use of `repr()` is in serialising the
		// empty default value for TensorPlug constructors. Make sure
		// we have a nice clean serialisation for that.
		return "GafferML.Tensor()";
	}
	else
	{
		// We don't have a good `repr()` for this - just return a default one
		// and the ValuePlugSerialiser will attempt a base 64 encoding instead.
		return fmt::format( "<GafferML._GafferML.Tensor object at {}>", (void *)&tensor );
	}
}

template<typename T>
object tensorGetItemTyped( const Tensor &tensor, const std::vector<int64_t> &location )
{
	return object(
		const_cast<Ort::Value &>( tensor.value() ).At<T>( location )
	);
}

object tensorGetItem( const Tensor &tensor, const std::vector<int64_t> &location )
{
	const auto elementType = tensor.value().GetTensorTypeAndShapeInfo().GetElementType();
	/// \todo Should we make Tensor.cpp's `dispatchTensorData()` public and use
	/// it here?
	switch( elementType )
	{
		case ONNX_TENSOR_ELEMENT_DATA_TYPE_FLOAT :
			return tensorGetItemTyped<float>( tensor, location );
		case ONNX_TENSOR_ELEMENT_DATA_TYPE_DOUBLE :
			return tensorGetItemTyped<double>( tensor, location );
		case ONNX_TENSOR_ELEMENT_DATA_TYPE_BOOL :
			return tensorGetItemTyped<bool>( tensor, location );
		case ONNX_TENSOR_ELEMENT_DATA_TYPE_UINT16 :
			return tensorGetItemTyped<uint16_t>( tensor, location );
		case ONNX_TENSOR_ELEMENT_DATA_TYPE_INT16 :
			return tensorGetItemTyped<int16_t>( tensor, location );
		case ONNX_TENSOR_ELEMENT_DATA_TYPE_UINT32 :
			return tensorGetItemTyped<uint32_t>( tensor, location );
		case ONNX_TENSOR_ELEMENT_DATA_TYPE_INT32 :
			return tensorGetItemTyped<int32_t>( tensor, location );
		case ONNX_TENSOR_ELEMENT_DATA_TYPE_UINT64 :
			return tensorGetItemTyped<uint64_t>( tensor, location );
		case ONNX_TENSOR_ELEMENT_DATA_TYPE_INT64 :
			return tensorGetItemTyped<int64_t>( tensor, location );
		default :
			throw IECore::Exception( fmt::format( "Unsupported element type {}", elementType ) );
	}
}

object tensorGetItem1D( const Tensor &tensor, int64_t index )
{
	return tensorGetItem( tensor, { index } );
}

object tensorGetItemND( const Tensor &tensor, tuple index )
{
	std::vector<int64_t> location;
	boost::python::container_utils::extend_container( location, index );
	return tensorGetItem( tensor, location );
}

void dataToTensorSetupWrapper( DataToTensor &dataToTensor, ValuePlug &prototypeDataPlug )
{
	IECorePython::ScopedGILRelease gilRelease;
	dataToTensor.setup( &prototypeDataPlug );
}

class DataToTensorSerialiser : public NodeSerialiser
{

	bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
	{
		auto dataToTensor = child->parent<DataToTensor>();
		if( child == dataToTensor->dataPlug() )
		{
			// We'll serialise a `setup()` call to construct this.
			return false;
		}
		return NodeSerialiser::childNeedsConstruction( child, serialisation );
	}

	std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const override
	{
		std::string result = NodeSerialiser::postConstructor( graphComponent, identifier, serialisation );

		auto dataPlug = static_cast<const DataToTensor *>( graphComponent )->dataPlug();
		if( !dataPlug )
		{
			return result;
		}

		if( result.size() )
		{
			result += "\n";
		}

		// Add a call to `setup()` to recreate the plug.

		const Serialiser *plugSerialiser = Serialisation::acquireSerialiser( dataPlug );
		result += identifier + ".setup( " + plugSerialiser->constructor( dataPlug, serialisation ) + " )\n";

		return result;
	}

};

} // namespace

BOOST_PYTHON_MODULE( _GafferML )
{

	IECorePython::RunTimeTypedClass<GafferML::Tensor>()
		.def( init<>() )
		.def( "__init__", make_constructor( tensorConstructorWrapper, default_call_policies(), ( arg( "data" ), arg( "shape" ) = object() ) ) )
		.def( "asData", (IECore::DataPtr (Tensor::*)())&Tensor::asData )
		.def( "shape", &tensorShapeWrapper )
		.def( "__repr__", &tensorRepr )
		.def( "__getitem__", &tensorGetItem1D )
		.def( "__getitem__", &tensorGetItemND )
	;

	GafferBindings::TypedObjectPlugClass<GafferML::TensorPlug>();

	{
		scope s = GafferBindings::DependencyNodeClass<DataToTensor>()
			.def( "canSetup", &DataToTensor::canSetup, ( arg( "prototypeDataPlug" ) ) )
			.def( "setup", &dataToTensorSetupWrapper, ( arg( "prototypeDataPlug" ) ) )
		;

		enum_<DataToTensor::ShapeMode>( "ShapeMode" )
			.value( "Automatic", DataToTensor::ShapeMode::Automatic )
			.value( "Custom", DataToTensor::ShapeMode::Custom )
		;
		Serialisation::registerSerialiser( DataToTensor::staticTypeId(), new DataToTensorSerialiser );
	}

}
