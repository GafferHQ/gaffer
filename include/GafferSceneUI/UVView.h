//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, John Haddon. All rights reserved.
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

#include "GafferSceneUI/Export.h"
#include "GafferSceneUI/TypeIds.h"

#include "GafferScene/ScenePlug.h"

#include "GafferImageUI/ImageGadget.h"

#include "GafferUI/View.h"

#include "Gaffer/BackgroundTask.h"
#include "Gaffer/StringPlug.h"

#include <unordered_set>
#include <unordered_map>

namespace GafferSceneUI
{

class SceneGadget;

class GAFFERSCENEUI_API UVView : public GafferUI::View
{

	public :

		explicit UVView( Gaffer::ScriptNodePtr scriptNode );
		~UVView() override;

		GAFFER_NODE_DECLARE_TYPE( GafferSceneUI::UVView, UVViewTypeId, View );

		Gaffer::StringPlug *uvSetPlug();
		const Gaffer::StringPlug *uvSetPlug() const;

		Gaffer::StringPlug *textureFileNamePlug();
		const Gaffer::StringPlug *textureFileNamePlug() const;

		Gaffer::StringPlug *displayTransformPlug();
		const Gaffer::StringPlug *displayTransformPlug() const;

		void setPaused( bool paused );
		bool getPaused() const;

		enum State
		{
			Paused,
			Running,
			Complete
		};

		State state() const;

		using UVViewSignal = Gaffer::Signals::Signal<void (UVView *)>;
		UVViewSignal &stateChangedSignal();

	private :

		Gaffer::CompoundObjectPlug *texturesPlug();
		const Gaffer::CompoundObjectPlug *texturesPlug() const;

		class UVScene;
		UVScene *uvScene();
		const UVScene *uvScene() const;

		SceneGadget *sceneGadget();
		const SceneGadget *sceneGadget() const;

		GafferUI::Gadget *textureGadgets();
		const GafferUI::Gadget *textureGadgets() const;

		void contextChanged();
		void plugDirtied( const Gaffer::Plug *plug );
		void preRender();
		void visibilityChanged();
		void selectedPathsChanged();
		void updateTextureGadgets( const IECore::ConstCompoundObjectPtr &textures );
		void gadgetStateChanged( const GafferUI::Gadget *gadget, bool running );

		UVViewSignal m_stateChangedSignal;
		std::unordered_set<const GafferUI::Gadget *> m_runningGadgets;

		bool m_textureGadgetsDirty;
		std::unique_ptr<Gaffer::BackgroundTask> m_texturesTask;

		bool m_framed;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( UVView )

} // namespace GafferUI
