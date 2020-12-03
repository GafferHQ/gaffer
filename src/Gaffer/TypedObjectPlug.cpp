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

#include "Gaffer/Node.h"
#include "Gaffer/TypedObjectPlug.inl"

namespace Gaffer
{

GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::ObjectPlug, ObjectPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::BoolVectorDataPlug, BoolVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::IntVectorDataPlug, IntVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::FloatVectorDataPlug, FloatVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::StringVectorDataPlug, StringVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::InternedStringVectorDataPlug, InternedStringVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::V2iVectorDataPlug, V2iVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::V3fVectorDataPlug, V3fVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::Color3fVectorDataPlug, Color3fVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::M44fVectorDataPlug, M44fVectorDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::ObjectVectorPlug, ObjectVectorPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::CompoundObjectPlug, CompoundObjectPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::AtomicCompoundDataPlug, AtomicCompoundDataPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::PathMatcherDataPlug, PathMatcherDataPlugTypeId )

// Specialise AtomicCompoundDataPlug to provide forward compatibility for connections
// from `Attributes.extraAttributes` in Gaffer 0.59.

const IECore::InternedString g_extraAttributes( "extraAttributes" );

bool supportCompoundObjectInput( const AtomicCompoundDataPlug *plug )
{
	if( plug->getName() != g_extraAttributes )
	{
		return false;
	}

	const Node *node = plug->node();
	if( !node )
	{
		return false;
	}

	return node->isInstanceOf( "GafferScene::Attributes" );
}

template<>
bool AtomicCompoundDataPlug::acceptsInput( const Plug *input ) const
{
	if( !ValuePlug::acceptsInput( input ) )
	{
		return false;
	}

	if( input )
	{
		return
			input->isInstanceOf( staticTypeId() ) ||
			( input->isInstanceOf( CompoundObjectPlug::staticTypeId() ) && supportCompoundObjectInput( this ) )
		;
	}
	return true;
}

template<>
void AtomicCompoundDataPlug::setFrom( const ValuePlug *other )
{
	switch( static_cast<Gaffer::TypeId>( other->typeId() ) )
	{
		case AtomicCompoundDataPlugTypeId :
			setValue( static_cast<const AtomicCompoundDataPlug *>( other )->getValue() );
			break;
		case CompoundObjectPlugTypeId : {
			if( supportCompoundObjectInput( this ) )
			{
				IECore::ConstCompoundObjectPtr o = static_cast<const CompoundObjectPlug *>( other )->getValue();
				IECore::CompoundDataPtr d = new IECore::CompoundData;
				for( const auto &e : o->members() )
				{
					if( auto *ed = IECore::runTimeCast<IECore::Data>( e.second.get() ) )
					{
						d->writable()[e.first] = ed;
					}
					else
					{
						throw IECore::Exception( "Unsupported object type" );
					}
				}
				setValue( d );
				break;
			}
		}
		default :
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
template class TypedObjectPlug<IECore::V3fVectorData>;
template class TypedObjectPlug<IECore::Color3fVectorData>;
template class TypedObjectPlug<IECore::M44fVectorData>;
template class TypedObjectPlug<IECore::ObjectVector>;
template class TypedObjectPlug<IECore::CompoundObject>;
template class TypedObjectPlug<IECore::CompoundData>;
template class TypedObjectPlug<IECore::PathMatcherData>;

} // namespace Gaffer
