//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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

#include "Gaffer/NumericBookmarkSet.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"

#include "IECore/Exception.h"

#include "boost/bind/bind.hpp"

using namespace boost::placeholders;
using namespace IECore;
using namespace Gaffer;

NumericBookmarkSet::NumericBookmarkSet( ScriptNodePtr script, int bookmark )
	: m_bookmark( 0 )
{
	m_script = script;
	Metadata::nodeValueChangedSignal().connect( boost::bind( &NumericBookmarkSet::metadataChanged, this, ::_2, ::_3 ) );
	setBookmark( bookmark );
}

NumericBookmarkSet::~NumericBookmarkSet()
{
}

void NumericBookmarkSet::setBookmark( int bookmark )
{
	if( bookmark < 1 || bookmark > 9 )
	{
		throw IECore::Exception( "Bookmark number must be between 1 and 9 (inclusive)." );
	}

	if( bookmark != m_bookmark )
	{
		m_bookmark = bookmark;
		updateNode();
	}
}

int NumericBookmarkSet::getBookmark() const
{
	return m_bookmark;
}

bool NumericBookmarkSet::contains( const Member *object ) const
{
	return m_node && m_node.get() == object;
}

Set::Member *NumericBookmarkSet::member( size_t index )
{
	return m_node.get();
}

const Set::Member *NumericBookmarkSet::member( size_t index ) const
{
	return m_node.get();
}

size_t NumericBookmarkSet::size() const
{
	return m_node ? 1 : 0;
}

void NumericBookmarkSet::metadataChanged( IECore::InternedString key, Gaffer::Node *node )
{
	if( MetadataAlgo::numericBookmarkAffectedByChange( key ) )
	{
		updateNode();
	}
}

void NumericBookmarkSet::updateNode()
{
	Node *bookmarkedNode = MetadataAlgo::getNumericBookmark( m_script.get(), m_bookmark );

	if( bookmarkedNode != m_node )
	{
		if( m_node )
		{
			NodePtr oldNode = m_node;
			m_node.reset();
			memberRemovedSignal()( this, oldNode.get() );
		}

		m_node = bookmarkedNode;

		if( bookmarkedNode )
		{
			memberAddedSignal()( this, bookmarkedNode );
		}
	}
}
