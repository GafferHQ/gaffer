//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

#include "IECore/RefCounted.h"

#include "Session.h"

namespace IECoreRenderMan
{

/// A reference-counted Riley Id, allowing an Id to be shared between multiple
/// clients. When the last client drops ownership, the Riley entity corresponding
/// to the Id is deleted.
template<typename T>
class RefCountedId : public IECore::RefCounted
{

	public :

		RefCountedId( T id, const Session *session )
			:	m_session( session ), m_id( id )
		{

		}

		~RefCountedId() override
		{
			if( m_session->renderType != IECoreScenePreview::Renderer::Interactive )
			{
				return;
			}

			if constexpr( std::is_same_v<T, riley::MaterialId> )
			{
				m_session->riley->DeleteMaterial( m_id );
			}
			else if constexpr( std::is_same_v<T, riley::DisplacementId> )
			{
				m_session->riley->DeleteDisplacement( m_id );
			}
			// Deliberately not checking type for the last case, so that we get
			// a compilation error if compiled for types we haven't added a
			// delete for.
			else
			{
				m_session->riley->DeleteGeometryPrototype( m_id );
			}
		}

		const T &id() const { return m_id; }

	private :

		const Session *m_session;
		T m_id;

};

} // namespace IECoreRenderMan
