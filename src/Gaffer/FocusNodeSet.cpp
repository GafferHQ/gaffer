//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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

#include "Gaffer/FocusNodeSet.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"

#include "IECore/Exception.h"

#include "boost/bind.hpp"

using namespace IECore;
using namespace Gaffer;


FocusNodeSet::FocusNodeSet( ScriptNodePtr script )
{
	m_script = script;
	Metadata::nodeValueChangedSignal().connect( boost::bind( &FocusNodeSet::metadataChanged, this, ::_2, ::_3 ) );
	updateNode();
}

FocusNodeSet::~FocusNodeSet()
{
}

bool FocusNodeSet::contains( const Member *object ) const
{
	return m_node && m_node.get() == object;
}

Set::Member *FocusNodeSet::member( size_t index )
{
	return m_node.get();
}

const Set::Member *FocusNodeSet::member( size_t index ) const
{
	return m_node.get();
}

size_t FocusNodeSet::size() const
{
	return m_node ? 1 : 0;
}

void FocusNodeSet::metadataChanged( IECore::InternedString key, Gaffer::Node *node )
{
	if( MetadataAlgo::focusNodeAffectedByChange( key ) )
	{
		updateNode();
	}
}

void FocusNodeSet::updateNode()
{
	Node *focusNode = MetadataAlgo::getFocusNode( m_script.get() );

	if( focusNode != m_node )
	{
		if( m_node )
		{
			NodePtr oldNode = m_node;
			m_node.reset();
			memberRemovedSignal()( this, oldNode.get() );
		}

		m_node = focusNode;

		if( focusNode )
		{
			memberAddedSignal()( this, focusNode );
		}
	}
}
