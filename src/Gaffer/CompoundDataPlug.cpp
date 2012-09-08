//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "Gaffer/TypedPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/CompoundDataPlug.h"

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

Gaffer::CompoundPlug *CompoundDataPlug::addMember( const std::string &name, const IECore::Data *value )
{
	CompoundPlugPtr plug = new CompoundPlug( "member1", direction(), getFlags() );
	StringPlugPtr namePlug = new StringPlug( "name", direction(), "", getFlags() );
	namePlug->setValue( name );
	plug->addChild( namePlug );
	
	/// \todo Support more plug types - perhaps using PlugType.h to simplify the code?
	switch( value->typeId() )
	{
		case FloatDataTypeId :
		{
			FloatPlugPtr valuePlug = new FloatPlug(
				"value",
				direction(),
				0,
				Imath::limits<float>::min(),
				Imath::limits<float>::max(),
				getFlags()
			);
			valuePlug->setValue( static_cast<const FloatData *>( value )->readable() );
			plug->addChild( valuePlug );
			break;
		}
		case IntDataTypeId :
		{
			IntPlugPtr valuePlug = new IntPlug(
				"value",
				direction(),
				0,
				Imath::limits<int>::min(),
				Imath::limits<int>::max(),
				getFlags()
			);
			valuePlug->setValue( static_cast<const IntData *>( value )->readable() );
			plug->addChild( valuePlug );
			break;
		}
		case StringDataTypeId :
		{
			StringPlugPtr valuePlug = new StringPlug(
				"value",
				direction(),
				"",
				getFlags()
			);
			valuePlug->setValue( static_cast<const StringData *>( value )->readable() );
			plug->addChild( valuePlug );
			break;
		}
		case BoolDataTypeId :
		{
			BoolPlugPtr valuePlug = new BoolPlug(
				"value",
				direction(),
				false,
				getFlags()
			);
			valuePlug->setValue( static_cast<const BoolData *>( value )->readable() );
			plug->addChild( valuePlug );
			break;
		}
		case Color3fDataTypeId :
		{
			Color3fPlugPtr valuePlug = new Color3fPlug(
				"value",
				direction(),
				Color3f( 0 ),
				Color3f( Imath::limits<float>::min() ),
				Color3f( Imath::limits<float>::max() ),
				getFlags()
			);
			valuePlug->setValue( static_cast<const Color3fData *>( value )->readable() );
			plug->addChild( valuePlug );
			break;
		}
		default :
			throw IECore::Exception(
				boost::str( boost::format( "Member \"%s\" has unsupported value data type \"%s\"" ) % name % value->typeName() )
			);
	}
	
	addChild( plug );
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
		IECore::DataPtr data = parameterDataAndName( *it, name );
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
		IECore::DataPtr data = parameterDataAndName( *it, name );
		if( data )
		{
			compoundObjectMap[name] = data;
		}
	}
}

IECore::DataPtr CompoundDataPlug::parameterDataAndName( const CompoundPlug *parameterPlug, std::string &name ) const
{	
	name = parameterPlug->getChild<StringPlug>( "name" )->getValue();
	if( !name.size() )
	{
		return 0;
	}
		
	const ValuePlug *valuePlug = parameterPlug->getChild<ValuePlug>( "value" );
	switch( valuePlug->typeId() )
	{
		case FloatPlugTypeId :
			return new FloatData( static_cast<const FloatPlug *>( valuePlug )->getValue() );
			break;
		case IntPlugTypeId :
			return new IntData( static_cast<const IntPlug *>( valuePlug )->getValue() );
			break;
		case StringPlugTypeId :
			return new StringData( static_cast<const StringPlug *>( valuePlug )->getValue() );
			break;
		case BoolPlugTypeId :
			return new BoolData( static_cast<const BoolPlug *>( valuePlug )->getValue() );
			break;
		case Color3fPlugTypeId :
			return new Color3fData( static_cast<const Color3fPlug *>( valuePlug )->getValue() );
			break;	
		default :
			throw IECore::Exception(
				boost::str( boost::format( "Parameter \"%s\" has unsupported value plug type \"%s\"" ) % name % valuePlug->typeName() )
			);
	}		
}

