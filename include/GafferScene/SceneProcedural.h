//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFERSCENE_SCENEPROCEDURAL_H
#define GAFFERSCENE_SCENEPROCEDURAL_H

#include "IECore/Renderer.h"
#include "IECore/Camera.h"
#include "IECore/Light.h"

#include "GafferScene/ScenePlug.h"
#include "GafferScene/PathMatcherData.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Context )
IE_CORE_FORWARDDECLARE( ScriptNode )

} // namespace Gaffer

namespace GafferScene
{

/// The SceneProcedural class passes the output from a ScenePlug to an IECore::Renderer
/// in a tree of nested deferred procedurals. See the python ScriptProcedural for 
/// a procedural which will load a gaffer script and generate geometry from a named
/// node.
class SceneProcedural : public IECore::Renderer::Procedural
{

	public :

		IE_CORE_DECLAREMEMBERPTR( SceneProcedural );

		/// A copy of context is taken.
		SceneProcedural( ConstScenePlugPtr scenePlug, const Gaffer::Context *context, const ScenePlug::ScenePath &scenePath=ScenePlug::ScenePath(), const IECore::PathMatcherData *pathsToExpand=0 );
		virtual ~SceneProcedural();
		
		virtual IECore::MurmurHash hash() const;
		virtual Imath::Box3f bound() const;
		virtual void render( IECore::RendererPtr renderer ) const;
				
	protected :
		
		SceneProcedural( const SceneProcedural &other, const ScenePlug::ScenePath &scenePath );
		
		// This class must hold a reference to the script node, to prevent it from being
		// destroyed mid-render.
		Gaffer::ConstScriptNodePtr m_scriptNode;
		ConstScenePlugPtr m_scenePlug;
		Gaffer::ContextPtr m_context;
		ScenePlug::ScenePath m_scenePath;
		
		IECore::PathMatcherDataPtr m_pathsToExpand;
		
		struct Options
		{
			bool transformBlur;
			bool deformationBlur;
			Imath::V2f shutter;
		};
		
		Options m_options;
		
		struct Attributes
		{
			bool transformBlur;
			unsigned transformBlurSegments;
			bool deformationBlur;
			unsigned deformationBlurSegments;
		};
		
		Attributes m_attributes;
		
	private :
	
		void updateAttributes( bool full );	
		void motionTimes( unsigned segments, std::set<float> &times ) const;
	
		void drawCamera( const IECore::Camera *camera, IECore::Renderer *renderer ) const;
		void drawLight( const IECore::Light *light, IECore::Renderer *renderer ) const;
		
};

IE_CORE_DECLAREPTR( SceneProcedural );

} // namespace GafferScene

#endif // GAFFERSCENE_SCENEPROCEDURAL_H
