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

#ifndef GAFFERSCENE_SCENECONTEXTPROCESSORBASE_H
#define GAFFERSCENE_SCENECONTEXTPROCESSORBASE_H

#include "GafferScene/SceneProcessor.h"

namespace GafferScene
{

class SceneContextProcessorBase : public SceneProcessor
{

	public :

		SceneContextProcessorBase( const std::string &name=defaultName<SceneContextProcessorBase>() );
		virtual ~SceneContextProcessorBase();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::SceneContextProcessorBase, SceneContextProcessorBaseTypeId, SceneProcessor );
		
	private :
	
		/// The only reason this class exists is so we can stub out these pure virtual functions so they're no longer pure. They
		/// don't need real implementations because the ContextProcessor class does all its work in compute(), meaning they'll never get
		/// called. This isn't an ideal situation, but it lets us put all the logic in ContextProcessor and TimeWarp (and any other classes
		/// we come up with) and use it for different sorts of processing (here scenes, later images etc) without rewriting all the code.
		/// So it's a bit ugly here, but quite pragmatic in terms of code reuse. Other options would be :
		///
		/// a) Have untemplated SceneProcessor and TimeWarp classes, which are instantiated and then have dynamic plugs added to make them
		/// look like a SceneProcessor. This has the downside that we can't do simple searches for all SceneProcessor nodes, because there's
		/// no common base class.
		///
		/// b) Have totally unrelated SceneTimeWarp and ImageTimeWarp classes that don't share code. Seems like a waste of time, particularly
		/// as we add more ContextProcessor subclasses.
		///
		/// c) Have ContextProcessor classes that aren't intended to derive from Node but instead just provide helper functions for
		/// adding plugs and computing a new context. This would also mean more unshared code in the actual SceneTimeWarp and ImageTimeWarp
		/// classes.
		/// 
		/// d) Not define the compute* methods on SceneNode, but that makes the implementations of all the other SceneNode subclasses more painful.
		virtual void hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;

		virtual Imath::Box3f computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual Imath::M44f computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstCompoundObjectPtr computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstObjectPtr computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstInternedStringVectorDataPtr computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstCompoundObjectPtr computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const;

};

} // namespace GafferScene

#endif // GAFFERSCENE_SCENECONTEXTPROCESSORBASE_H
