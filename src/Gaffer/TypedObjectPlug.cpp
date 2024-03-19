//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/TypedObjectPlug.h"

#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedObjectPlugImplementation.h"

#include "boost/algorithm/string/classification.hpp"
#include "boost/algorithm/string/split.hpp"

namespace Gaffer
{

GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::ObjectPlug, ObjectPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::BoolVectorDataPlug, BoolVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::IntVectorDataPlug, IntVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::FloatVectorDataPlug, FloatVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::StringVectorDataPlug, StringVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::InternedStringVectorDataPlug, InternedStringVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::V2iVectorDataPlug, V2iVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::V3iVectorDataPlug, V3iVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::V2fVectorDataPlug, V2fVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::V3fVectorDataPlug, V3fVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::Color3fVectorDataPlug, Color3fVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::Color4fVectorDataPlug, Color4fVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::M44fVectorDataPlug, M44fVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::M33fVectorDataPlug, M33fVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::Box2fVectorDataPlug, Box2fVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::ObjectVectorPlug, ObjectVectorPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::CompoundObjectPlug, CompoundObjectPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::AtomicCompoundDataPlug, AtomicCompoundDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::PathMatcherDataPlug, PathMatcherDataPlugTypeId )

// Specialise CompoundObjectPlug to accept connections from CompoundDataPlug

template<>
bool CompoundObjectPlug::acceptsInput( const Plug *input ) const
{
	if( !ValuePlug::acceptsInput( input ) )
	{
		return false;
	}

	if( input )
	{
		return
			input->isInstanceOf( staticTypeId() ) ||
			input->isInstanceOf( AtomicCompoundDataPlug::staticTypeId() )
		;
	}
	return true;
}

template<>
void CompoundObjectPlug::setFrom( const ValuePlug *other )
{
	switch( static_cast<Gaffer::TypeId>( other->typeId() ) )
	{
		case CompoundObjectPlugTypeId :
			setValue( static_cast<const CompoundObjectPlug *>( other )->getValue() );
			break;
		case AtomicCompoundDataPlugTypeId : {
			IECore::ConstCompoundDataPtr d = static_cast<const AtomicCompoundDataPlug *>( other )->getValue();
			IECore::CompoundObjectPtr o = new IECore::CompoundObject;
			o->members().insert( d->readable().begin(), d->readable().end() );
			setValue( o );
			break;
		}
		default :
			throw IECore::Exception( "Unsupported plug type" );
	}
}

// Specialise StringVectorDataPlug to accept connections from StringPlug

template<>
bool StringVectorDataPlug::acceptsInput( const Plug *input ) const
{
	if( !ValuePlug::acceptsInput( input ) )
	{
		return false;
	}

	if( input )
	{
		return
			input->isInstanceOf( staticTypeId() ) ||
			input->isInstanceOf( StringPlug::staticTypeId() )
		;
	}
	return true;
}

template<>
void StringVectorDataPlug::setFrom( const ValuePlug *other )
{
	if( auto stringVectorPlug = IECore::runTimeCast<const StringVectorDataPlug >( other ) )
	{
		setValue( stringVectorPlug->getValue() );
	}
	else if( auto stringPlug = IECore::runTimeCast<const StringPlug >( other ) )
	{
		IECore::StringVectorDataPtr value = new IECore::StringVectorData;
		std::string s = stringPlug->getValue();
		if( !s.empty() )
		{
			boost::split( value->writable(), s, boost::is_any_of( " " ) );
		}
		setValue( value );
	}
	else
	{
		throw IECore::Exception( "Unsupported plug type" );
	}
}

// explicit instantiation
template class TypedObjectPlug<IECore::Object>;
template class TypedObjectPlug<IECore::BoolVectorData>;
template class TypedObjectPlug<IECore::IntVectorData>;
template class TypedObjectPlug<IECore::FloatVectorData>;
template class TypedObjectPlug<IECore::StringVectorData>;
template class TypedObjectPlug<IECore::InternedStringVectorData>;
template class TypedObjectPlug<IECore::V2iVectorData>;
template class TypedObjectPlug<IECore::V3iVectorData>;
template class TypedObjectPlug<IECore::V2fVectorData>;
template class TypedObjectPlug<IECore::V3fVectorData>;
template class TypedObjectPlug<IECore::Color3fVectorData>;
template class TypedObjectPlug<IECore::Color4fVectorData>;
template class TypedObjectPlug<IECore::M44fVectorData>;
template class TypedObjectPlug<IECore::M33fVectorData>;
template class TypedObjectPlug<IECore::Box2fVectorData>;
template class TypedObjectPlug<IECore::ObjectVector>;
template class TypedObjectPlug<IECore::CompoundObject>;
template class TypedObjectPlug<IECore::CompoundData>;
template class TypedObjectPlug<IECore::PathMatcherData>;

} // namespace Gaffer
