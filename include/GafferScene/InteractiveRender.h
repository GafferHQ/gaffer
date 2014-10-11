//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERSCENE_INTERACTIVERENDER_H
#define GAFFERSCENE_INTERACTIVERENDER_H

#include "IECore/Renderer.h"

#include "Gaffer/Node.h"

#include "GafferScene/ScenePlug.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Context )

} // namespace Gaffer

namespace GafferScene
{

/// Base class for nodes which perform renders embedded in the main gaffer process,
/// and which can be updated automatically and rerendered as the user tweaks the scene.
class InteractiveRender : public Gaffer::Node
{

	public :

		InteractiveRender( const std::string &name=defaultName<InteractiveRender>() );
		virtual ~InteractiveRender();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::InteractiveRender, InteractiveRenderTypeId, Gaffer::Node );

		enum State
		{
			Stopped,
			Running,
			Paused
		};

		/// The scene to be rendered.
		ScenePlug *inPlug();
		const ScenePlug *inPlug() const;

		/// A direct pass-through of the input scene.
		ScenePlug *outPlug();
		const ScenePlug *outPlug() const;

		Gaffer::IntPlug *statePlug();
		const Gaffer::IntPlug *statePlug() const;

		Gaffer::BoolPlug *updateLightsPlug();
		const Gaffer::BoolPlug *updateLightsPlug() const;

		Gaffer::BoolPlug *updateAttributesPlug();
		const Gaffer::BoolPlug *updateAttributesPlug() const;

		Gaffer::BoolPlug *updateCameraPlug();
		const Gaffer::BoolPlug *updateCameraPlug() const;

		Gaffer::BoolPlug *updateCoordinateSystemsPlug();
		const Gaffer::BoolPlug *updateCoordinateSystemsPlug() const;

		/// The Context in which the InteractiveRender should operate.
		Gaffer::Context *getContext();
		const Gaffer::Context *getContext() const;
		void setContext( Gaffer::ContextPtr context );

	protected :

		/// Must be implemented by derived classes to return the renderer that will be used.
		virtual IECore::RendererPtr createRenderer() const = 0;

	private :

		void plugDirtied( const Gaffer::Plug *plug );
		void parentChanged( Gaffer::GraphComponent *child, Gaffer::GraphComponent *oldParent );

		void update();
		void updateLights();
		void updateAttributes();
		void updateAttributesWalk( const ScenePlug::ScenePath &path );
		void updateCamera();
		void updateCoordinateSystems();

		void outputLightsInternal( const IECore::CompoundObject *globals, bool editing );

		typedef std::set<std::string> LightHandles;

		IECore::RendererPtr m_renderer;
		ConstScenePlugPtr m_scene;
		State m_state;
		LightHandles m_lightHandles;
		bool m_lightsDirty;
		bool m_attributesDirty;
		bool m_cameraDirty;
		bool m_coordinateSystemsDirty;

		Gaffer::ContextPtr m_context;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( InteractiveRender );

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<InteractiveRender> > InteractiveRenderIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<InteractiveRender> > RecursiveInteractiveRenderIterator;

} // namespace GafferScene

#endif // GAFFERSCENE_INTERACTIVERENDER_H
