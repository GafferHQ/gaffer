//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Export.h"
#include "GafferScene/TypeIds.h"

#include "Gaffer/PathFilter.h"
#include "Gaffer/Plug.h"

namespace GafferScene
{

IE_CORE_FORWARDDECLARE( Filter )

/// Filters a ScenePath using a GafferScene::Filter node.
class GAFFERSCENE_API SceneFilterPathFilter : public Gaffer::PathFilter
{

	public :

		explicit SceneFilterPathFilter( FilterPtr sceneFilter, IECore::CompoundDataPtr userData = nullptr );
		~SceneFilterPathFilter() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::SceneFilterPathFilter, SceneFilterPathFilterTypeId, Gaffer::PathFilter );

	protected :

		void doFilter( std::vector<Gaffer::PathPtr> &paths, const IECore::Canceller *canceller ) const override;

	private :

		void plugDirtied( const Gaffer::Plug *plug );

		struct Remove;

		FilterPtr m_sceneFilter;
		Gaffer::Signals::ScopedConnection m_plugDirtiedConnection;

};

IE_CORE_DECLAREPTR( SceneFilterPathFilter )

} // namespace GafferScene
