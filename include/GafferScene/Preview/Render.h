//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERSCENE_PREVIEW_RENDER_H
#define GAFFERSCENE_PREVIEW_RENDER_H

#include "Gaffer/StringPlug.h"
#include "Gaffer/NumericPlug.h"

#include "GafferDispatch/TaskNode.h"
#include "GafferScene/TypeIds.h"

namespace GafferScene
{

IE_CORE_FORWARDDECLARE( ScenePlug )

namespace Preview
{

class Render : public GafferDispatch::TaskNode
{

	public :

		Render( const std::string &name=defaultName<Render>() );
		virtual ~Render();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::Preview::Render, GafferScene::RenderTypeId, GafferDispatch::TaskNode );

		enum Mode
		{
			RenderMode = 0,
			SceneDescriptionMode = 1
		};

		ScenePlug *inPlug();
		const ScenePlug *inPlug() const;

		Gaffer::StringPlug *rendererPlug();
		const Gaffer::StringPlug *rendererPlug() const;

		Gaffer::IntPlug *modePlug();
		const Gaffer::IntPlug *modePlug() const;

		Gaffer::StringPlug *fileNamePlug();
		const Gaffer::StringPlug *fileNamePlug() const;

		ScenePlug *outPlug();
		const ScenePlug *outPlug() const;

		virtual IECore::MurmurHash hash( const Gaffer::Context *context ) const;
		virtual void execute() const;

	protected :

		// Constructor for derived classes which wish to hardcode the renderer type. Perhaps
		// at some point we won't even have derived classes, but instead will always use the
		// base class? At the moment the main purpose of the derived classes is to force the
		// loading of the module which registers the required renderer type.
		Render( const IECore::InternedString &rendererType, const std::string &name );

	private :

		void construct( const IECore::InternedString &rendererType = IECore::InternedString() );

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Render );

} // namespace Preview

} // namespace GafferScene

#endif // GAFFERSCENE_PREVIEW_RENDER_H
