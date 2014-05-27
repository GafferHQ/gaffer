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
#include "Gaffer/BoxPlug.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// CompoundData::MemberPlug implementation.
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( CompoundDataPlug::MemberPlug );

CompoundDataPlug::MemberPlug::MemberPlug( const std::string &name, Direction direction, unsigned flags )
	:	CompoundPlug( name, direction, flags )
{
}

bool CompoundDataPlug::MemberPlug::acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
{
	if( !CompoundPlug::acceptsChild( potentialChild ) )
	{
		return false;
	}
		
	if(
		potentialChild->isInstanceOf( StringPlug::staticTypeId() ) &&
		potentialChild->getName() == "name" &&
		!getChild<Plug>( "name" )
	)
	{
		return true;
	}
	else if(
		potentialChild->isInstanceOf( ValuePlug::staticTypeId() ) &&
		potentialChild->getName() == "value" &&
		!getChild<Plug>( "value" )
	)
	{
		return true;
	}
	else if(
		potentialChild->isInstanceOf( BoolPlug::staticTypeId() ) &&
		potentialChild->getName() == "enabled" &&
		!getChild<Plug>( "enabled" )
	)
	{
		return true;
	}
	
	return false;
}

PlugPtr CompoundDataPlug::MemberPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	PlugPtr result = new MemberPlug( name, direction, getFlags() );
	for( PlugIterator it( this ); it != it.end(); it++ )
	{
		result->addChild( (*it)->createCounterpart( (*it)->getName(), direction ) );
	}
	return result;
}

//////////////////////////////////////////////////////////////////////////
// CompoundDataPlug implementation
//////////////////////////////////////////////////////////////////////////

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
	
	return potentialChild->isInstanceOf( MemberPlug::staticTypeId() );
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

CompoundDataPlug::MemberPlug *CompoundDataPlug::addMember( const std::string &name, const IECore::Data *defaultValue, const std::string &plugName, unsigned plugFlags )
{	
	return addMember( name, createPlugFromData( "value", direction(), plugFlags, defaultValue ), plugName );
}

CompoundDataPlug::MemberPlug *CompoundDataPlug::addMember( const std::string &name, ValuePlug *valuePlug, const std::string &plugName )
{
	MemberPlugPtr plug = new MemberPlug( plugName, direction(), valuePlug->getFlags() );
	
	StringPlugPtr namePlug = new StringPlug( "name", direction(), "", valuePlug->getFlags() );
	namePlug->setValue( name );
	plug->addChild( namePlug );
	
	valuePlug->setName( "value" );
	plug->addChild( valuePlug );
	
	addChild( plug );
	return plug;
}
		
CompoundDataPlug::MemberPlug *CompoundDataPlug::addOptionalMember( const std::string &name, const IECore::Data *defaultValue, const std::string &plugName, unsigned plugFlags, bool enabled )
{
	MemberPlug *plug = addMember( name, defaultValue, plugName, plugFlags );
	BoolPlugPtr e = new BoolPlug( "enabled", direction(), enabled, plugFlags );
	plug->addChild( e );
	return plug;
}

CompoundDataPlug::MemberPlug *CompoundDataPlug::addOptionalMember( const std::string &name, ValuePlug *valuePlug, const std::string &plugName, bool enabled )
{
	MemberPlug *plug = addMember( name, valuePlug, plugName );
	BoolPlugPtr e = new BoolPlug( "enabled", direction(), enabled, valuePlug->getFlags() );
	plug->addChild( e );
	return plug;
}

void CompoundDataPlug::addMembers( const IECore::CompoundData *parameters, bool useNameAsPlugName )
{
	std::string plugName = "member1";
	for( CompoundDataMap::const_iterator it = parameters->readable().begin(); it!=parameters->readable().end(); it++ )
	{
		if( useNameAsPlugName )
		{
			plugName = it->first;
		}
		addMember( it->first, it->second, plugName );
	}
}

void CompoundDataPlug::fillCompoundData( IECore::CompoundDataMap &compoundDataMap ) const
{
	std::string name;
	for( MemberPlugIterator it( this ); it != it.end(); it++ )
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
	for( MemberPlugIterator it( this ); it != it.end(); it++ )
	{
		IECore::DataPtr data = memberDataAndName( *it, name );
		if( data )
		{
			compoundObjectMap[name] = data;
		}
	}
}

IECore::DataPtr CompoundDataPlug::memberDataAndName( const MemberPlug *parameterPlug, std::string &name ) const
{	
	if( parameterPlug->children().size() == 3 )
	{
		if( !parameterPlug->getChild<BoolPlug>( 2 )->getValue() )
		{
			return 0;
		}
	}

	if( parameterPlug->children().size() < 2 )
	{
		// we can end up here either if someone has very naughtily deleted
		// some plugs, or if we're being called during loading and the
		// child plugs haven't been fully constructed.
		return 0;
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
ValuePlugPtr CompoundDataPlug::boxValuePlug( const std::string &name, Plug::Direction direction, unsigned flags, const T *value )
{
	return new BoxPlug<typename T::ValueType>(
		name,
		direction,
		value->readable(),
		flags
	);
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
		value->readable(),
		ValueType( Imath::limits<BaseType>::min() ),
		ValueType( Imath::limits<BaseType>::max() ),
		flags
	);
	
	return result;
}

template<typename T>
ValuePlugPtr CompoundDataPlug::typedObjectValuePlug( const std::string &name, Plug::Direction direction, unsigned flags, const T *value )
{
	typename TypedObjectPlug<T>::Ptr result = new TypedObjectPlug<T>(
		name,
		direction,
		value,
		flags	
	);

	return result;
}

IECore::DataPtr CompoundDataPlug::extractDataFromPlug( const ValuePlug *plug )
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

