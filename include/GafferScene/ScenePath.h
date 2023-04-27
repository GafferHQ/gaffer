//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Path.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Context )
IE_CORE_FORWARDDECLARE( Plug )
IE_CORE_FORWARDDECLARE( Node )

} // namespace Gaffer

namespace GafferScene
{

IE_CORE_FORWARDDECLARE( ScenePlug )

class GAFFERSCENE_API ScenePath : public Gaffer::Path
{

	public :

		explicit ScenePath( ScenePlugPtr scene, Gaffer::ContextPtr context, Gaffer::PathFilterPtr filter = nullptr );
		ScenePath( ScenePlugPtr scene, Gaffer::ContextPtr context, const std::string &path, Gaffer::PathFilterPtr filter = nullptr );
		ScenePath( ScenePlugPtr scene, Gaffer::ContextPtr context, const Names &names, const IECore::InternedString &root = "/", Gaffer::PathFilterPtr filter = nullptr );

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::ScenePath, ScenePathTypeId, Gaffer::Path );

		~ScenePath() override;

		void setScene( ScenePlugPtr scene );
		ScenePlug *getScene();
		const ScenePlug *getScene() const;

		void setContext( Gaffer::ContextPtr context );
		Gaffer::Context *getContext();
		const Gaffer::Context *getContext() const;

		bool isValid( const IECore::Canceller *canceller = nullptr ) const override;
		bool isLeaf( const IECore::Canceller *canceller = nullptr ) const override;
		Gaffer::PathPtr copy() const override;

		const Gaffer::Plug *cancellationSubject() const override;

		static Gaffer::PathFilterPtr createStandardFilter( const std::vector<std::string> &setNames = std::vector<std::string>(), const std::string &setsLabel = "" );

	protected :

		void doChildren( std::vector<Gaffer::PathPtr> &children, const IECore::Canceller *canceller ) const override;
		void pathChangedSignalCreated() override;

	private :

		void contextChanged( const IECore::InternedString &key );
		void plugDirtied( Gaffer::Plug *plug );

		Gaffer::NodePtr m_node;
		ScenePlugPtr m_scene;
		Gaffer::ContextPtr m_context;
		Gaffer::Signals::ScopedConnection m_plugDirtiedConnection;
		Gaffer::Signals::ScopedConnection m_contextChangedConnection;

};

IE_CORE_DECLAREPTR( ScenePath )

} // namespace GafferScene
