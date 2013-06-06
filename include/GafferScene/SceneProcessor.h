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

#ifndef GAFFERSCENE_SCENEPROCESSOR_H
#define GAFFERSCENE_SCENEPROCESSOR_H

#include "GafferScene/SceneNode.h"

namespace GafferScene
{

/// The SceneProcessor class provides a base class for nodes which will take a scene input
/// and modify it in some way. See the SceneElementProcessor and the SceneHierarchyProcessor
/// for more useful base classes for scene processing.
class SceneProcessor : public SceneNode
{

	public :

		SceneProcessor( const std::string &name=defaultName<SceneProcessor>() );
		virtual ~SceneProcessor();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::SceneProcessor, SceneProcessorTypeId, SceneNode );
		
		/// Scene elements enter the node through inPlug() and are output in processed form on SceneNode::outPlug().
		/// If the node is disabled via enabledPlug(), then the inPlug() is automatically passed through directly
		/// to the outPlug().
		ScenePlug *inPlug();
		const ScenePlug *inPlug() const;
		
		virtual Gaffer::Plug *correspondingInput( const Gaffer::Plug *output );
		virtual const Gaffer::Plug *correspondingInput( const Gaffer::Plug *output ) const;

	protected :

		/// Reimplemented from SceneNode to pass through the inPlug() hashes when the node is disabled.
		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		/// Reimplemented from SceneNode to pass through the inPlug() computations when the node is disabled.
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;
	
	private :
	
		static size_t g_firstPlugIndex;
		
};

} // namespace GafferScene

#endif // GAFFERSCENE_SCENEPROCESSOR_H
