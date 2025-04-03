//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/ImageSampler.h"

#include "GafferImageUI/ImageView.h"
#include "GafferImageUI/ImageGadget.h"

#include "GafferSceneUI/Export.h"
#include "GafferSceneUI/TypeIds.h"

#include "GafferScene/RenderManifest.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/ScenePlug.h"

#include "GafferUI/DragDropEvent.h"
#include "GafferUI/Tool.h"

namespace GafferSceneUI
{

class GAFFERSCENEUI_API ImageSelectionTool : public GafferUI::Tool
{

	public :

		explicit ImageSelectionTool( GafferUI::View *view, const std::string &name = defaultName<ImageSelectionTool>() );

		~ImageSelectionTool() override;

		std::string status() const;

		using StatusChangedSignal = Gaffer::Signals::Signal<void (ImageSelectionTool &)>;
		StatusChangedSignal &statusChangedSignal();

		GAFFER_NODE_DECLARE_TYPE( GafferSceneUI::ImageSelectionTool, ImageSelectionToolTypeId, GafferUI::Tool );

	private :

		IE_CORE_FORWARDDECLARE( Rectangle );

		// We connect view->inPlug() as the input to this, so
		// we'll get notified via plugDirtiedSignal() when the
		// image changes.
		GafferImage::ImagePlug *imagePlug();
		const GafferImage::ImagePlug *imagePlug() const;

		GafferImageUI::ImageGadget *imageGadget();

		void setStatus( const std::string &message, bool error );
		void setErrorMessage( const std::string &message );

		void plugDirtied( const Gaffer::Plug *plug );

		IECore::PathMatcher pathsForIds( const std::vector<uint32_t> &ids, std::string &message );
		std::vector<uint32_t> idsForPaths( const IECore::PathMatcher &paths, std::string &message );

		uint32_t sampleId( const Imath::V2f &pixel );

		void selectedPathsChanged();

		void updateSelection();

		void updateRenderManifest( std::string &message );

		void preRender();

		bool keyPress( const GafferUI::KeyEvent &event );
		bool buttonPress( const GafferUI::ButtonEvent &event );
		bool mouseMove( const GafferUI::ButtonEvent &event );
		bool leaveSignal( const GafferUI::ButtonEvent &event );

		GafferImage::ImageSamplerPtr m_imageSampler;

		const GafferScene::RenderManifest *m_renderManifest;
		GafferScene::RenderManifest m_renderManifestStorage;
		std::string m_sideCarManifestPath;
		std::filesystem::file_time_type m_sideCarManifestModTime;
		bool m_sideCarManifestModTimeDirty;

		std::string m_status;
		StatusChangedSignal m_statusChangedSignal;

		bool m_selectionDirty = true;

		static size_t g_firstPlugIndex;
		static ToolDescription<ImageSelectionTool, GafferImageUI::ImageView> g_imageToolDescription;

};

IE_CORE_DECLAREPTR( ImageSelectionTool )

} // namespace GafferSceneUI
