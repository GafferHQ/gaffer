//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedPlugImplementation.h"

namespace Gaffer
{

GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::BoolPlug, BoolPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::M33fPlug, M33fPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::M44fPlug, M44fPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::AtomicBox2fPlug, AtomicBox2fPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::AtomicBox3fPlug, AtomicBox3fPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::AtomicBox2iPlug, AtomicBox2iPlugTypeId )

// Specialise BoolPlug to accept connections from NumericPlugs and StringPlugs

template<>
bool BoolPlug::acceptsInput( const Plug *input ) const
{
	if( !ValuePlug::acceptsInput( input ) )
	{
		return false;
	}
	if( input )
	{
		return
			input->isInstanceOf( staticTypeId() ) ||
			input->isInstanceOf( IntPlug::staticTypeId() ) ||
			input->isInstanceOf( FloatPlug::staticTypeId() ) ||
			input->isInstanceOf( StringPlug::staticTypeId() )
		;
	}
	return true;
}

template<>
void BoolPlug::setFrom( const ValuePlug *other )
{
	switch( static_cast<Gaffer::TypeId>(other->typeId()) )
	{
		case BoolPlugTypeId :
			setValue( static_cast<const BoolPlug *>( other )->getValue() );
			break;
		case FloatPlugTypeId :
			setValue( static_cast<const FloatPlug *>( other )->getValue() );
			break;
		case IntPlugTypeId :
			setValue( static_cast<const IntPlug *>( other )->getValue() );
			break;
		case StringPlugTypeId :
			setValue( static_cast<const StringPlug *>( other )->getValue().size() );
			break;
		default :
			throw IECore::Exception( "Unsupported plug type" );
	}
}

// explicit instantiation
template class TypedPlug<bool>;
template class TypedPlug<Imath::M33f>;
template class TypedPlug<Imath::M44f>;
template class TypedPlug<Imath::Box2f>;
template class TypedPlug<Imath::Box3f>;
template class TypedPlug<Imath::Box2i>;

} // namespace Gaffer
