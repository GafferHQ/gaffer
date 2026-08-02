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

#pragma once

#include "GafferImageUI/ImageView.h"

#include "GafferSceneUI/Export.h"
#include "GafferSceneUI/TypeIds.h"

#include "GafferScene/SceneAlgo.h"
#include "GafferScene/ScenePlug.h"

#include "GafferUI/DragDropEvent.h"
#include "GafferUI/Tool.h"

namespace GafferSceneUI
{

IE_CORE_FORWARDDECLARE( SceneView )

class GAFFERSCENEUI_API OFXInteractTool : public GafferUI::Tool
{

	public :

		explicit OFXInteractTool( GafferUI::View *view, const std::string &name = defaultName<OFXInteractTool>() );

		~OFXInteractTool() override;

		std::string status() const;
		Gaffer::Box2fPlug *plug();
		Gaffer::BoolPlug *enabledPlug();

		using StatusChangedSignal = Gaffer::Signals::Signal<void (OFXInteractTool &)>;
		StatusChangedSignal &statusChangedSignal();

		GAFFER_NODE_DECLARE_TYPE( GafferSceneUI::OFXInteractTool, OFXInteractToolTypeId, GafferUI::Tool );

	private :

		IE_CORE_FORWARDDECLARE( Rectangle );

		// We connect view->inPlug() as the input to this, so
		// we'll get notified via plugDirtiedSignal() when the
		// scene changes.
		GafferScene::ScenePlug *scenePlug();
		const GafferScene::ScenePlug *scenePlug() const;
		GafferImage::ImagePlug *imagePlug();
		const GafferImage::ImagePlug *imagePlug() const;

		// We hold separate state here as the tool requires data from several
		// sources, that have their own invalidation life cycles.
		void setOverlayMessage( const std::string &message );
		void setErrorMessage( const std::string &message );

		void setOverlayVisible( bool visible );
		bool getOverlayVisible() const;

		void viewportChanged();
		void plugDirtied( const Gaffer::Plug *plug );
		void metadataChanged( IECore::InternedString key );
		void overlayRectangleChanged( unsigned reason );

		void preRender();

		Imath::Box2f resolutionGate() const;

		bool keyPress( const GafferUI::KeyEvent &event );

		Gaffer::Signals::ScopedConnection m_overlayRectangleChangedConnection;

		std::string m_overlayMessage;
		std::string m_errorMessage;
		StatusChangedSignal m_statusChangedSignal;

		Gaffer::BoolPlugPtr m_ofxInteractEnabledPlug; // may be null, even when m_cropWindowPlug is not
		Gaffer::Signals::ScopedConnection m_ofxInteractPlugDirtiedConnection;

		bool m_overlayDirty;
		RectanglePtr m_overlay;

		static size_t g_firstPlugIndex;
		static ToolDescription<OFXInteractTool, SceneView> g_sceneToolDescription;
		static ToolDescription<OFXInteractTool, GafferImageUI::ImageView> g_imageToolDescription;

};

IE_CORE_DECLAREPTR( OFXInteractTool )

} // namespace GafferSceneUI
