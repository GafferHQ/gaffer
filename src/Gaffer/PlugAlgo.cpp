//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "Gaffer/PlugAlgo.h"

#include "Gaffer/Box.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/Node.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/SplinePlug.h"
#include "Gaffer/TransformPlug.h"
#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/ValuePlug.h"

#include "IECore/SplineData.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/algorithm/string/replace.hpp"
#include "boost/format.hpp"

using namespace std;
using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Replace
//////////////////////////////////////////////////////////////////////////

namespace
{

struct Connections
{
	Plug *plug;
	PlugPtr input;
	vector<PlugPtr> outputs;
};

using ConnectionsVector = vector<Connections>;

void replacePlugWalk( Plug *existingPlug, Plug *plug, ConnectionsVector &connections )
{
	// Record output connections.
	Connections c;
	c.plug = plug;
	c.outputs.insert( c.outputs.begin(), existingPlug->outputs().begin(), existingPlug->outputs().end() );

	if( plug->children().size() )
	{
		// Recurse
		for( Plug::Iterator it( plug ); !it.done(); ++it )
		{
			if( Plug *existingChildPlug = existingPlug->getChild<Plug>( (*it)->getName() ) )
			{
				replacePlugWalk( existingChildPlug, it->get(), connections );
			}
		}
	}
	else
	{
		// At a leaf - record input connection and transfer values if
		// necessary. We only store inputs for leaves because automatic
		// connection tracking will take care of connecting the parent
		// levels when all children are connected.
		c.input = existingPlug->getInput();
		if( !c.input && plug->direction() == Plug::In )
		{
			ValuePlug *existingValuePlug = runTimeCast<ValuePlug>( existingPlug );
			ValuePlug *valuePlug = runTimeCast<ValuePlug>( plug );
			if( existingValuePlug && valuePlug )
			{
				valuePlug->setFrom( existingValuePlug );
			}
		}
	}

	connections.push_back( c );
}

} // namespace

namespace Gaffer
{

namespace PlugAlgo
{

void replacePlug( Gaffer::GraphComponent *parent, PlugPtr plug )
{
	Plug *existingPlug = parent->getChild<Plug>( plug->getName() );
	if( !existingPlug )
	{
		parent->addChild( plug );
		return;
	}

	// Transfer values where necessary, and store connections
	// to transfer after reparenting.

	ConnectionsVector connections;
	replacePlugWalk( existingPlug, plug.get(), connections );

	// Replace old plug by parenting in new one.

	parent->setChild( plug->getName(), plug );

	// Transfer old connections. We do this after
	// parenting because downstream acceptsInput() methods
	// might care what sort of node the connection is coming
	// from.

	for( ConnectionsVector::const_iterator it = connections.begin(), eIt = connections.end(); it != eIt; ++it )
	{
		if( it->input )
		{
			it->plug->setInput( it->input.get() );
		}
		for( vector<PlugPtr>::const_iterator oIt = it->outputs.begin(), oeIt = it->outputs.end(); oIt != oeIt; ++oIt )
		{
			(*oIt)->setInput( it->plug );
		}
	}
}

} // namespace PlugAlgo

} // namespace Gaffer

//////////////////////////////////////////////////////////////////////////
// Convert to/from Data
//////////////////////////////////////////////////////////////////////////

namespace
{

template<typename T>
ValuePlugPtr boxValuePlug( const std::string &name, Plug::Direction direction, unsigned flags, const T *value )
{
	return new BoxPlug<typename T::ValueType>(
		name,
		direction,
		value->readable(),
		flags
	);
}

template<typename T>
ValuePlugPtr compoundNumericValuePlug( const std::string &name, Plug::Direction direction, unsigned flags, const T *value )
{
	using ValueType = typename T::ValueType;
	using BaseType = typename ValueType::BaseType;
	using PlugType = CompoundNumericPlug<ValueType>;

	typename PlugType::Ptr result = new PlugType(
		name,
		direction,
		value->readable(),
		ValueType( Imath::limits<BaseType>::min() ),
		ValueType( Imath::limits<BaseType>::max() ),
		flags
	);

	return result;
}

template<typename T>
ValuePlugPtr geometricCompoundNumericValuePlug( const std::string &name, Plug::Direction direction, unsigned flags, const T *value )
{
	using ValueType = typename T::ValueType;
	using BaseType = typename ValueType::BaseType;
	using PlugType = CompoundNumericPlug<ValueType>;

	typename PlugType::Ptr result = new PlugType(
		name,
		direction,
		value->readable(),
		ValueType( Imath::limits<BaseType>::min() ),
		ValueType( Imath::limits<BaseType>::max() ),
		flags,
		value->getInterpretation()
	);

	return result;
}

template<typename T>
ValuePlugPtr typedObjectValuePlug( const std::string &name, Plug::Direction direction, unsigned flags, const T *value )
{
	typename TypedObjectPlug<T>::Ptr result = new TypedObjectPlug<T>(
		name,
		direction,
		value,
		flags
	);

	return result;
}

}

namespace Gaffer
{

namespace PlugAlgo
{

ValuePlugPtr createPlugFromData( const std::string &name, Plug::Direction direction, unsigned flags, const IECore::Data *value )
{
	switch( value->typeId() )
	{
		case FloatDataTypeId :
		{
			FloatPlugPtr valuePlug = new FloatPlug(
				name,
				direction,
				static_cast<const FloatData *>( value )->readable(),
				Imath::limits<float>::min(),
				Imath::limits<float>::max(),
				flags
			);
			return valuePlug;
		}
		case IntDataTypeId :
		{
			IntPlugPtr valuePlug = new IntPlug(
				name,
				direction,
				static_cast<const IntData *>( value )->readable(),
				Imath::limits<int>::min(),
				Imath::limits<int>::max(),
				flags
			);
			return valuePlug;
		}
		case StringDataTypeId :
		{
			StringPlugPtr valuePlug = new StringPlug(
				name,
				direction,
				static_cast<const StringData *>( value )->readable(),
				flags
			);
			return valuePlug;
		}
		case BoolDataTypeId :
		{
			BoolPlugPtr valuePlug = new BoolPlug(
				name,
				direction,
				static_cast<const BoolData *>( value )->readable(),
				flags
			);
			return valuePlug;
		}
		case V2iDataTypeId :
		{
			return geometricCompoundNumericValuePlug( name, direction, flags, static_cast<const V2iData *>( value ) );
		}
		case V3iDataTypeId :
		{
			return geometricCompoundNumericValuePlug( name, direction, flags, static_cast<const V3iData *>( value ) );
		}
		case V2fDataTypeId :
		{
			return geometricCompoundNumericValuePlug( name, direction, flags, static_cast<const V2fData *>( value ) );
		}
		case V3fDataTypeId :
		{
			return geometricCompoundNumericValuePlug( name, direction, flags, static_cast<const V3fData *>( value ) );
		}
		case Color3fDataTypeId :
		{
			return compoundNumericValuePlug( name, direction, flags, static_cast<const Color3fData *>( value ) );
		}
		case Color4fDataTypeId :
		{
			return compoundNumericValuePlug( name, direction, flags, static_cast<const Color4fData *>( value ) );
		}
		case Box2fDataTypeId :
		{
			return boxValuePlug( name, direction, flags, static_cast<const Box2fData *>( value ) );
		}
		case Box2iDataTypeId :
		{
			return boxValuePlug( name, direction, flags, static_cast<const Box2iData *>( value ) );
		}
		case Box3fDataTypeId :
		{
			return boxValuePlug( name, direction, flags, static_cast<const Box3fData *>( value ) );
		}
		case Box3iDataTypeId :
		{
			return boxValuePlug( name, direction, flags, static_cast<const Box3iData *>( value ) );
		}
		case M44fDataTypeId :
		{
			M44fPlugPtr valuePlug = new M44fPlug(
				name,
				direction,
				static_cast<const M44fData *>( value )->readable(),
				flags
			);
			return valuePlug;
		}
		case FloatVectorDataTypeId :
		{
			return typedObjectValuePlug( name, direction, flags, static_cast<const FloatVectorData *>( value ) );
		}
		case IntVectorDataTypeId :
		{
			return typedObjectValuePlug( name, direction, flags, static_cast<const IntVectorData *>( value ) );
		}
		case StringVectorDataTypeId :
		{
			return typedObjectValuePlug( name, direction, flags, static_cast<const StringVectorData *>( value ) );
		}
		case InternedStringVectorDataTypeId :
		{
			return typedObjectValuePlug( name, direction, flags, static_cast<const InternedStringVectorData *>( value ) );
		}
		case BoolVectorDataTypeId :
		{
			return typedObjectValuePlug( name, direction, flags, static_cast<const BoolVectorData *>( value ) );
		}
		case V2iVectorDataTypeId :
		{
			return typedObjectValuePlug( name, direction, flags, static_cast<const V2iVectorData *>( value ) );
		}
		case V3fVectorDataTypeId :
		{
			return typedObjectValuePlug( name, direction, flags, static_cast<const V3fVectorData *>( value ) );
		}
		case Color3fVectorDataTypeId :
		{
			return typedObjectValuePlug( name, direction, flags, static_cast<const Color3fVectorData *>( value ) );
		}
		case M44fVectorDataTypeId :
		{
			return typedObjectValuePlug( name, direction, flags, static_cast<const M44fVectorData *>( value ) );
		}
		case M33fVectorDataTypeId :
		{
			return typedObjectValuePlug( name, direction, flags, static_cast<const M33fVectorData *>( value ) );
		}
		default :
			throw IECore::Exception(
				boost::str( boost::format( "Data for \"%s\" has unsupported value data type \"%s\"" ) % name % value->typeName() )
			);
	}
}

IECore::DataPtr getValueAsData( const ValuePlug *plug )
{
	switch( static_cast<Gaffer::TypeId>(plug->typeId()) )
	{
		case FloatPlugTypeId :
			return new FloatData( static_cast<const FloatPlug *>( plug )->getValue() );
		case IntPlugTypeId :
			return new IntData( static_cast<const IntPlug *>( plug )->getValue() );
		case StringPlugTypeId :
			return new StringData( static_cast<const StringPlug *>( plug )->getValue() );
		case BoolPlugTypeId :
			return new BoolData( static_cast<const BoolPlug *>( plug )->getValue() );
		case V2iPlugTypeId :
		{
			const V2iPlug *v2iPlug = static_cast<const V2iPlug *>( plug );
			V2iDataPtr data = new V2iData( v2iPlug->getValue() );
			data->setInterpretation( v2iPlug->interpretation() );
			return data;
		}
		case V3iPlugTypeId :
		{
			const V3iPlug *v3iPlug = static_cast<const V3iPlug *>( plug );
			V3iDataPtr data = new V3iData( v3iPlug->getValue() );
			data->setInterpretation( v3iPlug->interpretation() );
			return data;
		}
		case V2fPlugTypeId :
		{
			const V2fPlug *v2fPlug = static_cast<const V2fPlug *>( plug );
			V2fDataPtr data = new V2fData( v2fPlug->getValue() );
			data->setInterpretation( v2fPlug->interpretation() );
			return data;
		}
		case V3fPlugTypeId :
		{
			const V3fPlug *v3fPlug = static_cast<const V3fPlug *>( plug );
			V3fDataPtr data = new V3fData( v3fPlug->getValue() );
			data->setInterpretation( v3fPlug->interpretation() );
			return data;
		}
		case Color3fPlugTypeId :
			return new Color3fData( static_cast<const Color3fPlug *>( plug )->getValue() );
		case Color4fPlugTypeId :
			return new Color4fData( static_cast<const Color4fPlug *>( plug )->getValue() );
		case Box2fPlugTypeId :
			return new Box2fData( static_cast<const Box2fPlug *>( plug )->getValue() );
		case Box2iPlugTypeId :
			return new Box2iData( static_cast<const Box2iPlug *>( plug )->getValue() );
		case Box3fPlugTypeId :
			return new Box3fData( static_cast<const Box3fPlug *>( plug )->getValue() );
		case Box3iPlugTypeId :
			return new Box3iData( static_cast<const Box3iPlug *>( plug )->getValue() );
		case FloatVectorDataPlugTypeId :
			return static_cast<const FloatVectorDataPlug *>( plug )->getValue()->copy();
		case IntVectorDataPlugTypeId :
			return static_cast<const IntVectorDataPlug *>( plug )->getValue()->copy();
		case StringVectorDataPlugTypeId :
			return static_cast<const StringVectorDataPlug *>( plug )->getValue()->copy();
		case InternedStringVectorDataPlugTypeId :
			return static_cast<const InternedStringVectorDataPlug *>( plug )->getValue()->copy();
		case BoolVectorDataPlugTypeId :
			return static_cast<const BoolVectorDataPlug *>( plug )->getValue()->copy();
		case V2iVectorDataPlugTypeId :
			return static_cast<const V2iVectorDataPlug *>( plug )->getValue()->copy();
		case V3iVectorDataPlugTypeId :
			return static_cast<const V3iVectorDataPlug *>( plug )->getValue()->copy();
		case V2fVectorDataPlugTypeId :
			return static_cast<const V2fVectorDataPlug *>( plug )->getValue()->copy();
		case V3fVectorDataPlugTypeId :
			return static_cast<const V3fVectorDataPlug *>( plug )->getValue()->copy();
		case Color3fVectorDataPlugTypeId :
			return static_cast<const Color3fVectorDataPlug *>( plug )->getValue()->copy();
		case M44fVectorDataPlugTypeId :
			return static_cast<const M44fVectorDataPlug *>( plug )->getValue()->copy();
		case M33fVectorDataPlugTypeId :
			return static_cast<const M33fVectorDataPlug *>( plug )->getValue()->copy();
		case SplineffPlugTypeId :
			return new SplineffData( static_cast<const SplineffPlug *>( plug )->getValue().spline() );
		case SplinefColor3fPlugTypeId :
			return new SplinefColor3fData( static_cast<const SplinefColor3fPlug *>( plug )->getValue().spline() );
		case TransformPlugTypeId :
			return new M44fData( static_cast<const TransformPlug *>( plug )->matrix() );
		case M44fPlugTypeId :
			return new M44fData( static_cast<const M44fPlug *>( plug )->getValue() );
		case M33fPlugTypeId :
			return new M33fData( static_cast<const M33fPlug *>( plug )->getValue() );
		case NameValuePlugTypeId : {
			CompoundDataPtr result = new CompoundData;
			for( auto &childPlug : ValuePlug::Range( *plug ) )
			{
				result->writable()[childPlug->getName()] = getValueAsData( childPlug.get() );
			}
			return result;
		}
		default :
			throw IECore::Exception(
				boost::str( boost::format( "Plug \"%s\" has unsupported type \"%s\"" ) % plug->getName().string() % plug->typeName() )
			);
	}

}

IECore::DataPtr extractDataFromPlug( const ValuePlug *plug )
{
	return getValueAsData( plug );
}

} // namespace PlugAlgo

} // namespace Gaffer


//////////////////////////////////////////////////////////////////////////
// Set value from data
//////////////////////////////////////////////////////////////////////////

namespace
{

template<typename PlugType>
bool setNumericPlugValue( PlugType *plug, const Data *value )
{
	switch( value->typeId() )
	{
		case FloatDataTypeId :
			plug->setValue( static_cast<const FloatData *>( value )->readable() );
			return true;
		case IntDataTypeId :
			plug->setValue( static_cast<const IntData *>( value )->readable() );
			return true;
		case BoolDataTypeId :
			plug->setValue( static_cast<const BoolData *>( value )->readable() );
			return true;
		default :
			return false;
	}
}

template<typename PlugType>
bool setTypedDataPlugValue( PlugType *plug, const Data *value )
{
	if( auto typedValue = runTimeCast<const typename PlugType::ValueType>( value ) )
	{
		plug->setValue( typedValue );
		return true;
	}
	return false;
}

template<typename PlugType, typename ValueType>
bool setCompoundNumericChildPlugValue( const PlugType *plug, typename PlugType::ChildType *child, const ValueType &value )
{
	for( size_t i = 0, eI = plug->children().size(); i < eI; ++i )
	{
		if( child == plug->getChild( i ) )
		{
			if( i < ValueType::dimensions() )
			{
				child->setValue( value[i] );
			}
			else
			{
				// 1 for the alpha of Color4f, 0 for everything else
				child->setValue( i == 3 ? 1 : 0 );
			}
			return true;
		}
	}
	return false;
}

template<typename PlugType>
bool setCompoundNumericPlugValue( const PlugType *plug, Gaffer::ValuePlug *leafPlug, const Data *value )
{
	auto typedChild = runTimeCast<typename PlugType::ChildType>( leafPlug );

	switch( value->typeId() )
	{
		case Color4fDataTypeId :
			return setCompoundNumericChildPlugValue( plug, typedChild, static_cast<const Color4fData *>( value )->readable() );
		case Color3fDataTypeId :
			return setCompoundNumericChildPlugValue( plug, typedChild, static_cast<const Color3fData *>( value )->readable() );
		case V3fDataTypeId :
			return setCompoundNumericChildPlugValue( plug, typedChild, static_cast<const V3fData *>( value )->readable() );
		case V2fDataTypeId :
			return setCompoundNumericChildPlugValue( plug, typedChild, static_cast<const V2fData *>( value )->readable() );
		case V3iDataTypeId :
			return setCompoundNumericChildPlugValue( plug, typedChild, static_cast<const V3iData *>( value )->readable() );
		case V2iDataTypeId :
			return setCompoundNumericChildPlugValue( plug, typedChild, static_cast<const V2iData *>( value )->readable() );
		case FloatDataTypeId :
		case IntDataTypeId :
		case BoolDataTypeId :
			if( plug->children().size() < 4 || leafPlug != plug->getChild( 3 ) )
			{
				return setNumericPlugValue( typedChild, value );
			}
			else
			{
				typedChild->setValue( 1 );
				return true;
			}
		default :
			return false;
	}
}

template<typename PlugType>
bool setCompoundNumericPlugValue( PlugType *plug, const Data *value )
{
	bool success = true;
	for( size_t i = 0, eI = plug->children().size(); i < eI; ++i )
	{
		ValuePlug *c = plug->template getChild<ValuePlug>( i );
		success &= setCompoundNumericPlugValue( plug, c, value);
	}
	return success;
}

template<typename PlugType, typename ValueType>
bool setBoxChildPlugValue( const PlugType *plug, typename PlugType::ChildType::ChildType *child, const ValueType &value )
{
	if( child->parent() == plug->minPlug() )
	{
		return setCompoundNumericChildPlugValue( plug->minPlug(), child, value.min );
	}
	else
	{
		return setCompoundNumericChildPlugValue( plug->maxPlug(), child, value.max );
	}
}

template<typename PlugType>
bool setBoxPlugValue( const PlugType *plug, Gaffer::ValuePlug *leafPlug, const Data *value )
{
	auto typedPlug = runTimeCast<typename PlugType::ChildType::ChildType>( leafPlug );
	switch( value->typeId() )
	{
		case Box3fDataTypeId :
			return setBoxChildPlugValue( plug, typedPlug, static_cast<const Box3fData *>( value )->readable() );
		case Box2fDataTypeId :
			return setBoxChildPlugValue( plug, typedPlug, static_cast<const Box2fData *>( value )->readable() );
		case Box3iDataTypeId :
			return setBoxChildPlugValue( plug, typedPlug, static_cast<const Box3iData *>( value )->readable() );
		case Box2iDataTypeId :
			return setBoxChildPlugValue( plug, typedPlug, static_cast<const Box2iData *>( value )->readable() );
		default :
			return false;
	}
}

template<typename PlugType>
bool setBoxPlugValue( PlugType *plug, const Data *value )
{
	bool success = true;
	for( size_t i = 0, eI = plug->children().size(); i < eI; ++i )
	{
		typename PlugType::ChildType *c = plug->template getChild<typename PlugType::ChildType>( i );
		for( size_t j = 0, eJ = c->children().size(); j < eJ; ++j )
		{
			ValuePlug *gc = c->template getChild<ValuePlug>( j );
			success &= setBoxPlugValue( plug, gc, value);
		}
	}
	return success;
}

bool canSetNumericPlugValue( const Data *value )
{
	if( !value )
	{
		return true;  // Data type not specified, so it could be a match
	}

	switch( value->typeId() )
	{
		case FloatDataTypeId :
		case IntDataTypeId :
		case BoolDataTypeId :
			return true;
		default :
			return false;
	}
}

template<typename PlugType>
bool canSetTypedDataPlugValue( const Data *value )
{
	if( !value )
	{
		return true;  // Data type not specified, so it could be a match
	}

	if( runTimeCast<const typename PlugType::ValueType>( value ) )
	{
		return true;
	}
	return false;
}

bool canSetCompoundNumericPlugValue( const Data *value )
{
	if( !value )
	{
		return true;  // Data type not specified, so it could be a match
	}

	switch( value->typeId() )
	{
		case Color4fDataTypeId :
		case Color3fDataTypeId :
		case V3fDataTypeId :
		case V2fDataTypeId :
		case V3iDataTypeId :
		case V2iDataTypeId :
		case FloatDataTypeId :
		case IntDataTypeId :
		case BoolDataTypeId :
			return true;
		default :
			return false;
	}
}

bool canSetBoxPlugValue( const Data *value )
{
	if( !value )
	{
		return true;  // Data type not specified, so it could be a match
	}

	switch( value->typeId() )
	{
		case Box3fDataTypeId :
		case Box2fDataTypeId :
		case Box3iDataTypeId :
		case Box2iDataTypeId :
			return true;
		default :
			return false;
	}
}

}  // namespace

namespace Gaffer
{

namespace PlugAlgo
{

bool canSetValueFromData( const ValuePlug *plug, const IECore::Data *value )
{
	switch( static_cast<Gaffer::TypeId>( plug->typeId() ) )
	{
		case Gaffer::BoolPlugTypeId:
		case Gaffer::FloatPlugTypeId:
		case Gaffer::IntPlugTypeId:
			return canSetNumericPlugValue( value );
		case Gaffer::BoolVectorDataPlugTypeId:
			return canSetTypedDataPlugValue<BoolVectorDataPlug>( value );
		case Gaffer::FloatVectorDataPlugTypeId:
			return canSetTypedDataPlugValue<FloatVectorDataPlug>( value );
		case Gaffer::IntVectorDataPlugTypeId:
			return canSetTypedDataPlugValue<IntVectorDataPlug>( value );
		case Gaffer::StringPlugTypeId:
			if( !value )
			{
				return true;  // Data type not specified, so it could be a match
			}
			switch( value->typeId() )
			{
				case IECore::StringDataTypeId:
				case IECore::InternedStringDataTypeId:
					return true;
				default:
					return false;
			}
		case Gaffer::StringVectorDataPlugTypeId:
			return canSetTypedDataPlugValue<StringVectorDataPlug>( value );
		case Gaffer::InternedStringVectorDataPlugTypeId:
			return canSetTypedDataPlugValue<InternedStringVectorDataPlug>( value );
		case Gaffer::Color3fPlugTypeId:
		case Gaffer::Color4fPlugTypeId:
		case Gaffer::V3fPlugTypeId:
		case Gaffer::V3iPlugTypeId:
		case Gaffer::V2fPlugTypeId:
		case Gaffer::V2iPlugTypeId:
			return canSetCompoundNumericPlugValue( value );
		case Gaffer::Color3fVectorDataPlugTypeId:
			return canSetTypedDataPlugValue<Color3fVectorDataPlug>( value );
		case Gaffer::V3fVectorDataPlugTypeId:
			return canSetTypedDataPlugValue<V3fVectorDataPlug>( value );
		case Gaffer::V3iVectorDataPlugTypeId:
			return canSetTypedDataPlugValue<V3iVectorDataPlug>( value );
		case Gaffer::V2fVectorDataPlugTypeId:
			return canSetTypedDataPlugValue<V2fVectorDataPlug>( value );
		case Gaffer::V2iVectorDataPlugTypeId:
			return canSetTypedDataPlugValue<V2iVectorDataPlug>( value );
		case Gaffer::Box3fPlugTypeId:
		case Gaffer::Box3iPlugTypeId:
		case Gaffer::Box2fPlugTypeId:
		case Gaffer::Box2iPlugTypeId:
			return canSetBoxPlugValue( value );
		default:
			return false;
	}

	return false;
}

bool setValueFromData( ValuePlug *plug, const IECore::Data *value )
{
	assert( plug != nullptr );
	assert( value != nullptr );

	switch( static_cast<Gaffer::TypeId>( plug->typeId() ) )
	{
		case Gaffer::BoolPlugTypeId:
			return setNumericPlugValue( static_cast<BoolPlug *>( plug ), value );
		case Gaffer::FloatPlugTypeId:
			return setNumericPlugValue( static_cast<FloatPlug *>( plug ), value );
		case Gaffer::IntPlugTypeId:
			return setNumericPlugValue( static_cast<IntPlug *>( plug ), value );
		case Gaffer::BoolVectorDataPlugTypeId:
			return setTypedDataPlugValue( static_cast<BoolVectorDataPlug *>( plug ), value );
		case Gaffer::FloatVectorDataPlugTypeId:
			return setTypedDataPlugValue( static_cast<FloatVectorDataPlug *>( plug ), value );
		case Gaffer::IntVectorDataPlugTypeId:
			return setTypedDataPlugValue( static_cast<IntVectorDataPlug *>( plug ), value );
		case Gaffer::StringPlugTypeId:
			switch( value->typeId() )
			{
				case IECore::StringDataTypeId:
					static_cast<StringPlug *>( plug )->setValue( static_cast<const StringData *>( value )->readable() );
					return true;
				case IECore::InternedStringDataTypeId:
					static_cast< StringPlug *>( plug )->setValue( static_cast<const InternedStringData *>( value )->readable().value() );
					return true;
				default:
					return false;
			}
		case Gaffer::StringVectorDataPlugTypeId:
			return setTypedDataPlugValue( static_cast<StringVectorDataPlug *>( plug ), value );
		case Gaffer::InternedStringVectorDataPlugTypeId:
			return setTypedDataPlugValue( static_cast<InternedStringVectorDataPlug *>( plug ), value );
		case Gaffer::Color3fPlugTypeId:
			return setCompoundNumericPlugValue( static_cast<Color3fPlug *>( plug ), value );
		case Gaffer::Color4fPlugTypeId:
			return setCompoundNumericPlugValue( static_cast<Color4fPlug *>( plug ), value );
		case Gaffer::V3fPlugTypeId:
			return setCompoundNumericPlugValue( static_cast<V3fPlug *>( plug ), value );
		case Gaffer::V3iPlugTypeId:
			return setCompoundNumericPlugValue( static_cast<V3iPlug *>( plug ), value );
		case Gaffer::V2fPlugTypeId:
			return setCompoundNumericPlugValue( static_cast<V2fPlug *>( plug ), value );
		case Gaffer::V2iPlugTypeId:
			return setCompoundNumericPlugValue( static_cast<V2iPlug *>( plug ), value );
		case Gaffer::V3fVectorDataPlugTypeId:
			return setTypedDataPlugValue( static_cast<V3fVectorDataPlug *>( plug ), value );
		case Gaffer::V3iVectorDataPlugTypeId:
			return setTypedDataPlugValue( static_cast<V3iVectorDataPlug *>( plug ), value );
		case Gaffer::V2fVectorDataPlugTypeId:
			return setTypedDataPlugValue( static_cast<V2fVectorDataPlug *>( plug ), value );
		case Gaffer::V2iVectorDataPlugTypeId:
			return setTypedDataPlugValue( static_cast<V2iVectorDataPlug *>( plug ), value );
		case Gaffer::Color3fVectorDataPlugTypeId:
			return setTypedDataPlugValue( static_cast<Color3fVectorDataPlug *>( plug ), value );
		case Gaffer::Box3fPlugTypeId:
			return setBoxPlugValue( static_cast<Box3fPlug *>( plug ), value );
		case Gaffer::Box3iPlugTypeId:
			return setBoxPlugValue( static_cast<Box3iPlug *>( plug ), value );
		case Gaffer::Box2fPlugTypeId:
			return setBoxPlugValue( static_cast<Box2fPlug *>( plug ), value );
		case Gaffer::Box2iPlugTypeId:
			return setBoxPlugValue( static_cast<Box2iPlug *>( plug ), value );
		default:
			return false;
	}
}

bool setValueFromData( const ValuePlug *plug, ValuePlug *leafPlug, const IECore::Data *value )
{
	assert( plug != nullptr );
	assert( leafPlug != nullptr );
	assert( value != nullptr );

	if( plug != leafPlug )
	{
		if( !plug->isAncestorOf( leafPlug ) )
		{
			throw IECore::Exception(
				boost::str(
					boost::format(
						"PlugAlgo::setValueFromData : Attempt to set plug \"%s\""
						"to a non-descendent leaf plug \"%s\""
					) % plug->getName().c_str() % leafPlug->getName().c_str()
				)
			);
		}
		if( leafPlug->children().size() != 0 )
		{
			throw IECore::Exception(
				boost::str(
					boost::format(
						"PlugAlgo::setValueFromData : Plug \"%s\" is not a leaf plug"
					) % leafPlug->getName().c_str()
				)
			);
		}

		switch( static_cast<Gaffer::TypeId>( plug->typeId() ) )
		{
			case Gaffer::Color3fPlugTypeId:
				return setCompoundNumericPlugValue( static_cast<const Color3fPlug *>( plug ), leafPlug, value );
			case Gaffer::Color4fPlugTypeId:
				return setCompoundNumericPlugValue( static_cast<const Color4fPlug *>( plug ), leafPlug, value );
			case Gaffer::V3fPlugTypeId:
				return setCompoundNumericPlugValue( static_cast<const V3fPlug *>( plug ), leafPlug, value );
			case Gaffer::V3iPlugTypeId:
				return setCompoundNumericPlugValue( static_cast<const V3iPlug *>( plug ), leafPlug, value );
			case Gaffer::V2fPlugTypeId:
				return setCompoundNumericPlugValue( static_cast<const V2fPlug *>( plug ), leafPlug, value );
			case Gaffer::V2iPlugTypeId:
				return setCompoundNumericPlugValue( static_cast<const V2iPlug *>( plug ), leafPlug, value );
			case Gaffer::Box3fPlugTypeId:
				return setBoxPlugValue( static_cast<const Box3fPlug *>( plug ), leafPlug, value );
			case Gaffer::Box3iPlugTypeId:
				return setBoxPlugValue( static_cast<const Box3iPlug *>( plug ), leafPlug, value );
			case Gaffer::Box2fPlugTypeId:
				return setBoxPlugValue( static_cast<const Box2fPlug *>( plug ), leafPlug, value );
			case Gaffer::Box2iPlugTypeId:
				return setBoxPlugValue( static_cast<const Box2iPlug *>( plug ), leafPlug, value );
			default:
				return false;
		}
	}

	return setValueFromData( leafPlug, value );

}

}  // namespace PlugAlgo

}  // namespace Gaffer


//////////////////////////////////////////////////////////////////////////
// Promotion
//////////////////////////////////////////////////////////////////////////

namespace
{

Node *externalNode( Plug *plug )
{
	Node *node = plug->node();
	return node ? node->parent<Node>() : nullptr;
}

const Node *externalNode( const Plug *plug )
{
	const Node *node = plug->node();
	return node ? node->parent<Node>() : nullptr;
}

bool validatePromotability( const Plug *plug, const Plug *parent, bool throwExceptions, bool childPlug = false )
{
	if( !plug )
	{
		if( !throwExceptions )
		{
			return false;
		}
		else
		{
			throw IECore::Exception(  "Cannot promote null plug" );
		}
	}

	if( PlugAlgo::isPromoted( plug ) )
	{
		if( !throwExceptions )
		{
			return false;
		}
		else
		{
			throw IECore::Exception(
				boost::str(
					boost::format( "Cannot promote plug \"%s\" as it is already promoted." ) % plug->fullName()
				)
			);
		}
	}

	if( plug->direction() == Plug::In )
	{
		// The plug must be serialisable, as we need its input to be saved,
		// but we only need to check this for the topmost plug and not for
		// children, because a setInput() call for a parent plug will also
		// restore child inputs.
		if( !childPlug && !plug->getFlags( Plug::Serialisable ) )
		{
			if( !throwExceptions )
			{
				return false;
			}
			else
			{
				throw IECore::Exception(
					boost::str(
						boost::format( "Cannot promote plug \"%s\" as it is not serialisable." ) % plug->fullName()
					)
				);
			}
		}

		if( !plug->getFlags( Plug::AcceptsInputs ) )
		{
			if( !throwExceptions )
			{
				return false;
			}
			else
			{
				throw IECore::Exception(
					boost::str(
						boost::format( "Cannot promote plug \"%s\" as it does not accept inputs." ) % plug->fullName()
					)
				);
			}
		}

		if( plug->getInput() )
		{
			if( !throwExceptions )
			{
				return false;
			}
			else
			{
				throw IECore::Exception(
					boost::str(
						boost::format( "Cannot promote plug \"%s\" as it already has an input." ) % plug->fullName()
					)
				);
			}
		}
	}

	if( !childPlug )
	{
		const Node *node = externalNode( plug );
		if( !node )
		{
			if( !throwExceptions )
			{
				return false;
			}
			else
			{
				throw IECore::Exception(
					boost::str(
						boost::format( "Cannot promote plug \"%s\" as there is no external node." ) % plug->fullName()
					)
				);
			}
		}

		if( parent && parent->node() != node )
		{
			if( !throwExceptions )
			{
				return false;
			}
			else
			{
				throw IECore::Exception(
					boost::str(
						boost::format( "Cannot promote plug \"%s\" because parent \"%s\" is not a descendant of \"%s\"." ) %
							plug->fullName() % parent % node
					)
				);
			}
		}
	}

	// Check all the children of this plug too
	for( Plug::RecursiveIterator it( plug ); !it.done(); ++it )
	{
		if( !validatePromotability( it->get(), parent, throwExceptions, /* childPlug = */ true ) )
		{
			return false;
		}
	}

	return true;
}

std::string promotedName( const Plug *plug )
{
	std::string result = plug->relativeName( plug->node() );
	boost::replace_all( result, ".", "_" );
	return result;
}

void applyDynamicFlag( Plug *plug )
{
	plug->setFlags( Plug::Dynamic, true );

	// Flags are not automatically propagated to the children of compound plugs,
	// so we need to do that ourselves. We don't want to propagate them to the
	// children of plug types which create the children themselves during
	// construction though, hence the typeId checks for the base classes
	// which add no children during construction. I'm not sure this approach is
	// necessarily the best - the alternative would be to set everything dynamic
	// unconditionally and then implement Serialiser::childNeedsConstruction()
	// for types like CompoundNumericPlug that create children in their constructors.
	// Or, even better, abolish the Dynamic flag entirely and deal with everything
	// via serialisers.
	const Gaffer::TypeId compoundTypes[] = { PlugTypeId, ValuePlugTypeId, ArrayPlugTypeId };
	const Gaffer::TypeId *compoundTypesEnd = compoundTypes + 3;
	if( find( compoundTypes, compoundTypesEnd, (Gaffer::TypeId)plug->typeId() ) != compoundTypesEnd )
	{
		for( Plug::RecursiveIterator it( plug ); !it.done(); ++it )
		{
			(*it)->setFlags( Plug::Dynamic, true );
			if( find( compoundTypes, compoundTypesEnd, (Gaffer::TypeId)(*it)->typeId() ) == compoundTypesEnd )
			{
				it.prune();
			}
		}
	}
}

void setFrom( Plug *dst, const Plug *src )
{
	assert( dst->typeId() == src->typeId() );
	if( ValuePlug *dstValuePlug = IECore::runTimeCast<ValuePlug>( dst ) )
	{
		dstValuePlug->setFrom( static_cast<const ValuePlug *>( src ) );
	}
	else
	{
		for( Plug::Iterator it( dst ); !it.done(); ++it )
		{
			Plug *dstChild = it->get();
			const Plug *srcChild = src->getChild<Plug>( dstChild->getName() );
			assert( srcChild );
			setFrom( dstChild, srcChild );
		}
	}
}

} // namespace

namespace Gaffer
{

namespace PlugAlgo
{

bool canPromote( const Plug *plug, const Plug *parent )
{
	return validatePromotability( plug, parent, /* throwExceptions = */ false );
}

Plug *promote( Plug *plug, Plug *parent, const StringAlgo::MatchPattern &excludeMetadata )
{
	return promoteWithName( plug, promotedName( plug ), parent, excludeMetadata );
}

Plug *promoteWithName( Plug *plug, const InternedString &name, Plug *parent, const StringAlgo::MatchPattern &excludeMetadata )
{
	validatePromotability( plug, parent, /* throwExceptions = */ true );

	PlugPtr externalPlug = plug->createCounterpart( name, plug->direction() );
	if( externalPlug->direction() == Plug::In )
	{
		setFrom( externalPlug.get(), plug );
	}

	Node *externalNode = ::externalNode( plug );
	const bool dynamic = runTimeCast<Box>( externalNode ) || parent == externalNode->userPlug();

	MetadataAlgo::copyIf(
		plug, externalPlug.get(),
		[&excludeMetadata]( const GraphComponent *from, const GraphComponent *to, InternedString name ) {
			if( StringAlgo::matchMultiple( name.string(), excludeMetadata ) )
			{
				/// \todo Remove `excludeMetadata` and rely on registered exclusions only. An obstacle
				/// to doing this is making it easy to exclude `layout:*` without lots and lots of
				/// individual exclusions.
				return false;
			}
			return MetadataAlgo::isPromotable( from, to, name );
		},
		// We use `persistent = dynamic` so that `promoteWithName()` can be used in
		// constructors for custom nodes, to promote a plug from an internal
		// network. In this case, we don't want the metadata to be serialised with
		// the node, as it will be recreated upon construction anyway.
		/* persistent = */ dynamic
	);

	if( dynamic )
	{
		applyDynamicFlag( externalPlug.get() );
		externalPlug->setFlags( Plug::Serialisable, true );
	}

	if( parent )
	{
		parent->addChild( externalPlug );
	}
	else
	{
		externalNode->addChild( externalPlug );
	}

	if( externalPlug->direction() == Plug::In )
	{
		plug->setInput( externalPlug );
	}
	else
	{
		externalPlug->setInput( plug );
	}

	return externalPlug.get();
}

bool isPromoted( const Plug *plug )
{
	if( !plug )
	{
		return false;
	}

	const Node *node = plug->node();
	if( !node )
	{
		return false;
	}

	const Node *enclosingNode = node->parent<Node>();
	if( !enclosingNode )
	{
		return false;
	}

	if( plug->direction() == Plug::In )
	{
		const Plug *input = plug->getInput();
		return input && input->node() == enclosingNode;
	}
	else
	{
		for( Plug::OutputContainer::const_iterator it = plug->outputs().begin(), eIt = plug->outputs().end(); it != eIt; ++it )
		{
			if( (*it)->node() == enclosingNode )
			{
				return true;
			}
		}
		return false;
	}
}

void unpromote( Plug *plug )
{
	if( !isPromoted( plug ) )
	{
		if( plug )
		{
			throw IECore::Exception(
				boost::str(
					boost::format( "Cannot unpromote plug \"%s\" as it has not been promoted." ) % plug->fullName()
				)
			);
		}
		else
		{
			throw IECore::Exception( "Cannot unpromote null plug" );
		}
	}

	Node *externalNode = ::externalNode( plug );
	Plug *externalPlug = nullptr;
	if( plug->direction() == Plug::In )
	{
		externalPlug = plug->getInput();
		plug->setInput( nullptr );
	}
	else
	{
		for( Plug::OutputContainer::const_iterator it = plug->outputs().begin(), eIt = plug->outputs().end(); it != eIt; ++it )
		{
			if( (*it)->node() == externalNode )
			{
				externalPlug = *it;
				break;
			}
		}
		assert( externalPlug ); // should be true because we checked isPromoted()
		externalPlug->setInput( nullptr );
	}

	// Remove the top level external plug , but only if
	// all the children are unused too in the case of a compound plug.
	bool remove = true;
	Plug *plugToRemove = externalPlug;
	while( plugToRemove->parent<Plug>() && plugToRemove->parent<Plug>() != externalNode->userPlug() )
	{
		plugToRemove = plugToRemove->parent<Plug>();
		for( Plug::Iterator it( plugToRemove ); !it.done(); ++it )
		{
			if(
				( (*it)->direction() == Plug::In && (*it)->outputs().size() ) ||
				( (*it)->direction() == Plug::Out && (*it)->getInput() )
			)
			{
				remove = false;
				break;
			}
		}
	}
	if( remove )
	{
		plugToRemove->parent()->removeChild( plugToRemove );
	}
}

} // namespace PlugAlgo

} // namespace Gaffer
