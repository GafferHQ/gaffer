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

#pragma once

#include "Gaffer/ScriptNode.h"
#include "Gaffer/Set.h"
#include "Gaffer/TypeIds.h"

namespace Gaffer
{

/// The NumericBookmarkSet provides a Set implementation that adjusts its membership such that
/// it always contains the node associated with a specified numeric bookmark (@see MetadataAlgo.h).
class GAFFER_API NumericBookmarkSet : public Gaffer::Set
{

	public :

		NumericBookmarkSet( Gaffer::ScriptNodePtr script, int bookmark );
		~NumericBookmarkSet() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::NumericBookmarkSet, NumericBookmarkSetTypeId, Gaffer::Set );

		void setBookmark( int bookmark );
		int getBookmark() const;

		/// @name Set interface
		////////////////////////////////////////////////////////////////////
		//@{
		bool contains( const Member *object ) const override;
		Member *member( size_t index ) override;
		const Member *member( size_t index ) const override;
		size_t size() const override;
		//@}

	private :

		Gaffer::ScriptNodePtr m_script;
		int m_bookmark;

		Gaffer::NodePtr m_node;
		void updateNode();

		void metadataChanged( IECore::InternedString key, Gaffer::Node *node );
};

IE_CORE_DECLAREPTR( NumericBookmarkSet );

} // namespace Gaffer
