//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERSCENEUI_CROPWINDOWTOOL_H
#define GAFFERSCENEUI_CROPWINDOWTOOL_H

#include "GafferSceneUI/Export.h"
#include "GafferSceneUI/TypeIds.h"

#include "GafferScene/SceneAlgo.h"
#include "GafferScene/ScenePlug.h"

#include "GafferUI/DragDropEvent.h"
#include "GafferUI/Tool.h"

#include "Gaffer/CompoundDataPlug.h"

namespace GafferSceneUI
{

IE_CORE_FORWARDDECLARE( SceneView )

class GAFFERSCENEUI_API CropWindowTool : public GafferUI::Tool
{

	public :

		CropWindowTool( SceneView *view, const std::string &name = defaultName<CropWindowTool>() );

		~CropWindowTool() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferSceneUI::CropWindowTool, CropWindowToolTypeId, GafferUI::Tool );

	private :

		IE_CORE_FORWARDDECLARE( Rectangle );

		// We connect view->inPlug() as the input to this, so
		// we'll get notified via plugDirtiedSignal() when the
		// scene changes.
		GafferScene::ScenePlug *scenePlug();
		const GafferScene::ScenePlug *scenePlug() const;

		void viewportChanged();
		void plugDirtied( const Gaffer::Plug *plug );
		void metadataChanged( IECore::InternedString key );
		void overlayRectangleChanged( unsigned reason );

		void preRender();

		void findCropWindowPlug();
		bool findCropWindowPlug( const GafferScene::SceneAlgo::History *history, bool enabledOnly  );
		bool findCropWindowPlugFromNode( GafferScene::ScenePlug *scene, bool enabledOnly  );

		boost::signals::scoped_connection m_overlayRectangleChangedConnection;

		bool m_needCropWindowPlugSearch;
		Gaffer::Box2fPlugPtr m_cropWindowPlug;
		Gaffer::BoolPlugPtr m_cropWindowEnabledPlug; // may be null, even when m_cropWindowPlug is not
		boost::signals::scoped_connection m_cropWindowPlugDirtiedConnection;

		bool m_overlayDirty;
		RectanglePtr m_overlay;

		static size_t g_firstPlugIndex;
		static ToolDescription<CropWindowTool, SceneView> g_toolDescription;

};

} // namespace GafferSceneUI

#endif // GAFFERSCENEUI_CROPWINDOWTOOL_H
