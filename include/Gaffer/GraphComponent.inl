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

#ifndef GAFFER_GRAPHCOMPONENT_INL
#define GAFFER_GRAPHCOMPONENT_INL

#include "boost/tokenizer.hpp"

namespace Gaffer
{

template<typename T>
T *GraphComponent::getChild( const IECore::InternedString &name )
{
	// preferring the nasty casts over maintaining two nearly identical implementations for getChild.
	return const_cast<T *>( const_cast<const GraphComponent *>( this )->getChild<T>( name ) );
}

template<typename T>
const T *GraphComponent::getChild( const IECore::InternedString &name ) const
{
	for( ChildContainer::const_iterator it=m_children.begin(), eIt=m_children.end(); it!=eIt; it++ )
	{
		if( (*it)->m_name==name )
		{
			return IECore::runTimeCast<const T>( it->get() );
		}
	}
	return nullptr;
}

template<typename T>
inline T *GraphComponent::getChild( size_t index )
{
	return IECore::runTimeCast<T>( m_children[index].get() );
}

template<typename T>
inline const T *GraphComponent::getChild( size_t index ) const
{
	return IECore::runTimeCast<const T>( m_children[index].get() );
}

const GraphComponent::ChildContainer &GraphComponent::children() const
{
	return m_children;
}

template<typename T>
T *GraphComponent::descendant( const std::string &relativePath )
{
	// preferring the nasty casts over maintaining two nearly identical implementations for getChild.
	return const_cast<T *>( const_cast<const GraphComponent *>( this )->descendant<T>( relativePath ) );
}

template<typename T>
const T *GraphComponent::descendant( const std::string &relativePath ) const
{
	if( !relativePath.size() )
	{
		return nullptr;
	}

	typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;

	Tokenizer t( relativePath, boost::char_separator<char>( "." ) );
	const GraphComponent *result = this;
	for( Tokenizer::iterator tIt=t.begin(); tIt!=t.end(); tIt++ )
	{
		const GraphComponent *child = nullptr;
		IECore::InternedString internedName( *tIt );
		for( ChildContainer::const_iterator it=result->m_children.begin(), eIt=result->m_children.end(); it!=eIt; it++ )
		{
			if( (*it)->m_name==internedName )
			{
				child = it->get();
				break;
			}
		}
		if( !child )
		{
			return nullptr;
		}
		result = child;
	}

	return IECore::runTimeCast<const T>( result );
}

template<typename T>
T *GraphComponent::parent()
{
	return IECore::runTimeCast<T>( m_parent );
}

template<typename T>
const T *GraphComponent::parent() const
{
	return IECore::runTimeCast<const T>( m_parent );
}

template<typename T>
T *GraphComponent::ancestor()
{
	return static_cast<T *>( ancestor( T::staticTypeId() ) );
}

template<typename T>
const T *GraphComponent::ancestor() const
{
	return static_cast<const T *>( ancestor( T::staticTypeId() ) );
}

template<typename T>
T *GraphComponent::commonAncestor( const GraphComponent *other )
{
	return static_cast<T *>( commonAncestor( other, T::staticTypeId() ) );
}

template<typename T>
const T *GraphComponent::commonAncestor( const GraphComponent *other ) const
{
	return static_cast<const T *>( commonAncestor( other, T::staticTypeId() ) );
}

template<typename T>
std::string GraphComponent::defaultName()
{
	return unprefixedTypeName( T::staticTypeName() );
}

} // namespace Gaffer

#endif // GAFFER_GRAPHCOMPONENT_INL
