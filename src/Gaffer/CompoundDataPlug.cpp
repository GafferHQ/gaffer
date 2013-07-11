//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

#include "IECore/SplineData.h"

#include "Gaffer/TypedPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/CompoundDataPlug.h"
#include "Gaffer/SplinePlug.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( CompoundDataPlug )

CompoundDataPlug::CompoundDataPlug( const std::string &name, Direction direction, unsigned flags )
	:	CompoundPlug( name, direction, flags )
{
}

CompoundDataPlug::~CompoundDataPlug()
{
}

bool CompoundDataPlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	if( !CompoundPlug::acceptsChild( potentialChild ) )
	{
		return false;
	}
	
	return potentialChild->isInstanceOf( CompoundPlug::staticTypeId() );
}

PlugPtr CompoundDataPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	CompoundDataPlugPtr result = new CompoundDataPlug( name, direction, getFlags() );
	for( PlugIterator it( this ); it != it.end(); it++ )
	{
		result->addChild( (*it)->createCounterpart( (*it)->getName(), direction ) );
	}
	return result;
}

Gaffer::CompoundPlug *CompoundDataPlug::addMember( const std::string &name, const IECore::Data *value, const std::string &plugName, unsigned plugFlags )
{	
	return addMember( name, createPlugFromData( "value", direction(), plugFlags, value ), plugName );
}

Gaffer::CompoundPlug *CompoundDataPlug::addMember( const std::string &name, ValuePlug *valuePlug, const std::string &plugName )
{
	CompoundPlugPtr plug = new CompoundPlug( plugName, direction(), valuePlug->getFlags() );
	
	StringPlugPtr namePlug = new StringPlug( "name", direction(), "", valuePlug->getFlags() );
	namePlug->setValue( name );
	plug->addChild( namePlug );
	
	plug->setChild( "value", valuePlug );
	
	addChild( plug );
	return plug;

}
		
Gaffer::CompoundPlug *CompoundDataPlug::addOptionalMember( const std::string &name, const IECore::Data *value, const std::string &plugName, unsigned plugFlags, bool enabled )
{
	CompoundPlug *plug = addMember( name, value, plugName, plugFlags );
	BoolPlugPtr e = new BoolPlug( "enabled", direction(), enabled, plugFlags );
	plug->addChild( e );
	return plug;
}

Gaffer::CompoundPlug *CompoundDataPlug::addOptionalMember( const std::string &name, ValuePlug *valuePlug, const std::string &plugName, bool enabled )
{
	CompoundPlug *plug = addMember( name, valuePlug, plugName );
	BoolPlugPtr e = new BoolPlug( "enabled", direction(), enabled, valuePlug->getFlags() );
	plug->addChild( e );
	return plug;
}

void CompoundDataPlug::addMembers( const IECore::CompoundData *parameters )
{
	for( CompoundDataMap::const_iterator it = parameters->readable().begin(); it!=parameters->readable().end(); it++ )
	{
		addMember( it->first, it->second );
	}
}

void CompoundDataPlug::fillCompoundData( IECore::CompoundDataMap &compoundDataMap ) const
{
	std::string name;
	for( CompoundPlugIterator it( this ); it != it.end(); it++ )
	{
		IECore::DataPtr data = memberDataAndName( *it, name );
		if( data )
		{
			compoundDataMap[name] = data;
		}
	}
}

void CompoundDataPlug::fillCompoundObject( IECore::CompoundObject::ObjectMap &compoundObjectMap ) const
{
	std::string name;
	for( CompoundPlugIterator it( this ); it != it.end(); it++ )
	{
		IECore::DataPtr data = memberDataAndName( *it, name );
		if( data )
		{
			compoundObjectMap[name] = data;
		}
	}
}

IECore::DataPtr CompoundDataPlug::memberDataAndName( const CompoundPlug *parameterPlug, std::string &name ) const
{	
	if( parameterPlug->children().size() == 3 )
	{
		if( !parameterPlug->getChild<BoolPlug>( 2 )->getValue() )
		{
			return 0;
		}
	}

	name = parameterPlug->getChild<StringPlug>( 0 )->getValue();
	if( !name.size() )
	{
		return 0;
	}
		
	const ValuePlug *valuePlug = parameterPlug->getChild<ValuePlug>( 1 );
	return extractDataFromPlug( valuePlug );
}

ValuePlugPtr CompoundDataPlug::createPlugFromData( const std::string &name, Plug::Direction direction, unsigned flags, const IECore::Data *value )
{
	switch( value->typeId() )
	{
		case FloatDataTypeId :
		{
			FloatPlugPtr valuePlug = new FloatPlug(
				name,
				direction,
				0,
				Imath::limits<float>::min(),
				Imath::limits<float>::max(),
				flags
			);
			valuePlug->setValue( static_cast<const FloatData *>( value )->readable() );
			return valuePlug;
		}
		case IntDataTypeId :
		{
			IntPlugPtr valuePlug = new IntPlug(
				name,
				direction,
				0,
				Imath::limits<int>::min(),
				Imath::limits<int>::max(),
				flags
			);
			valuePlug->setValue( static_cast<const IntData *>( value )->readable() );
			return valuePlug;
		}
		case StringDataTypeId :
		{
			StringPlugPtr valuePlug = new StringPlug(
				name,
				direction,
				"",
				flags
			);
			valuePlug->setValue( static_cast<const StringData *>( value )->readable() );
			return valuePlug;
		}
		case BoolDataTypeId :
		{
			BoolPlugPtr valuePlug = new BoolPlug(
				name,
				direction,
				false,
				flags
			);
			valuePlug->setValue( static_cast<const BoolData *>( value )->readable() );
			return valuePlug;
		}
		case V2iDataTypeId :
		{
			return compoundNumericValuePlug( name, direction, flags, static_cast<const V2iData *>( value ) );
		}
		case V3iDataTypeId :
		{
			return compoundNumericValuePlug( name, direction, flags, static_cast<const V3iData *>( value ) );
		}
		case V2fDataTypeId :
		{
			return compoundNumericValuePlug( name, direction, flags, static_cast<const V2fData *>( value ) );
		}
		case V3fDataTypeId :
		{
			return compoundNumericValuePlug( name, direction, flags, static_cast<const V3fData *>( value ) );
		}
		case Color3fDataTypeId :
		{
			return compoundNumericValuePlug( name, direction, flags, static_cast<const Color3fData *>( value ) );
		}
		case Color4fDataTypeId :
		{
			return compoundNumericValuePlug( name, direction, flags, static_cast<const Color4fData *>( value ) );
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
		case V3fVectorDataTypeId :
		{
			return typedObjectValuePlug( name, direction, flags, static_cast<const V3fVectorData *>( value ) );
		}
		case Color3fVectorDataTypeId :
		{
			return typedObjectValuePlug( name, direction, flags, static_cast<const Color3fVectorData *>( value ) );
		}
		default :
			throw IECore::Exception(
				boost::str( boost::format( "Data for \"%s\" has unsupported value data type \"%s\"" ) % name % value->typeName() )
			);
	}
}

template<typename T>
ValuePlugPtr CompoundDataPlug::compoundNumericValuePlug( const std::string &name, Plug::Direction direction, unsigned flags, const T *value )
{
	typedef typename T::ValueType ValueType;
	typedef typename ValueType::BaseType BaseType;
	typedef CompoundNumericPlug<ValueType> PlugType;
	
	typename PlugType::Ptr result = new PlugType(
		name,
		direction,
		ValueType( 0 ),
		ValueType( Imath::limits<BaseType>::min() ),
		ValueType( Imath::limits<BaseType>::max() ),
		flags
	);
	
	result->setValue( value->readable() );
	return result;
}

template<typename T>
ValuePlugPtr CompoundDataPlug::typedObjectValuePlug( const std::string &name, Plug::Direction direction, unsigned flags, const T *value )
{
	typename TypedObjectPlug<T>::Ptr result = new TypedObjectPlug<T>(
		name,
		direction,
		new T(),
		flags	
	);
	result->setValue( value );
	return result;
}

IECore::DataPtr CompoundDataPlug::extractDataFromPlug( const ValuePlug *plug )
{
	switch( plug->typeId() )
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
			return new V2iData( static_cast<const V2iPlug *>( plug )->getValue() );
		case V3iPlugTypeId :
			return new V3iData( static_cast<const V3iPlug *>( plug )->getValue() );
		case V2fPlugTypeId :
			return new V2fData( static_cast<const V2fPlug *>( plug )->getValue() );
		case V3fPlugTypeId :
			return new V3fData( static_cast<const V3fPlug *>( plug )->getValue() );
		case Color3fPlugTypeId :
			return new Color3fData( static_cast<const Color3fPlug *>( plug )->getValue() );
		case Color4fPlugTypeId :
			return new Color4fData( static_cast<const Color4fPlug *>( plug )->getValue() );
		case FloatVectorDataPlugTypeId :
			return static_cast<const FloatVectorDataPlug *>( plug )->getValue()->copy();
		case IntVectorDataPlugTypeId :
			return static_cast<const IntVectorDataPlug *>( plug )->getValue()->copy();
		case StringVectorDataPlugTypeId :
			return static_cast<const StringVectorDataPlug *>( plug )->getValue()->copy();
		case V3fVectorDataPlugTypeId :
			return static_cast<const V3fVectorDataPlug *>( plug )->getValue()->copy();		
		case Color3fVectorDataPlugTypeId :
			return static_cast<const Color3fVectorDataPlug *>( plug )->getValue()->copy();
		case SplineffPlugTypeId :
			return new SplineffData( static_cast<const SplineffPlug *>( plug )->getValue() );
		case SplinefColor3fPlugTypeId :
			return new SplinefColor3fData( static_cast<const SplinefColor3fPlug *>( plug )->getValue() );	
		default :
			throw IECore::Exception(
				boost::str( boost::format( "Plug \"%s\" has unsupported type \"%s\"" ) % plug->getName().string() % plug->typeName() )
			);
	}		

}

