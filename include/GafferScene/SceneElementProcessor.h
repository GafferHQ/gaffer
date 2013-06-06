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

#ifndef GAFFERSCENE_SCENEELEMENTPROCESSOR_H
#define GAFFERSCENE_SCENEELEMENTPROCESSOR_H

#include "GafferScene/FilteredSceneProcessor.h"

namespace GafferScene
{

/// The SceneElementProcessor class provides a base class for modifying elements of an input
/// scene while leaving the scene hierarchy unchanged.
class SceneElementProcessor : public FilteredSceneProcessor
{

	public :

		SceneElementProcessor( const std::string &name=defaultName<SceneElementProcessor>(), Filter::Result filterDefault = Filter::Match );
		virtual ~SceneElementProcessor();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::SceneElementProcessor, SceneElementProcessorTypeId, FilteredSceneProcessor );
				
		/// Implemented so that each child of inPlug() affects the corresponding child of outPlug()
		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;
				
	protected :

		/// Implemented to call hashProcessedBound() where appropriate.
		virtual void hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		/// Implemented to call hashProcessedTransform() where appropriate.
		virtual void hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		/// Implemented to call hashProcessedAttributes() where appropriate.
		virtual void hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		/// Implemented to call hashProcessedObject() where appropriate.
		virtual void hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		/// Implemented as a pass-through.
		virtual void hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		/// Implemented as a pass-through.
		virtual void hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		
		/// Implemented to call computeProcessedBound() where appropriate.
		virtual Imath::Box3f computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		/// Implemented to call computeProcessedTransform() where appropriate.
		virtual Imath::M44f computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		/// Implemented to call computeProcessedAttributes() where appropriate.
		virtual IECore::ConstCompoundObjectPtr computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		/// Implemented to call computeProcessedObject() where appropriate.
		virtual IECore::ConstObjectPtr computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		/// Implemented as a pass-through.
		virtual IECore::ConstInternedStringVectorDataPtr computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		/// Implemented as a pass-through.
		virtual IECore::ConstCompoundObjectPtr computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const;
		
		/// @name Scene processing methods
		/// These methods should be reimplemented by derived classes to process the input scene - they will be called as
		/// appropriate based on the result of the filter applied to the node. To process a particular
		/// aspect of the scene you must reimplement processesAspect() to return true, reimplement
		/// hashAspect() to append to the hash appropriately (the path will already have been appended),
		/// and finally reimplement the processAspect() function to perform the processing. Note that the implementation
		/// of processesAspect() is expected to return a constant - returning different values for different scene paths
		/// is currently not supported (this is because the bound computation may need to take into account child locations).
		/////////////////////////////////////////////////////////////////////////////////////////////////	
		//@{
		virtual bool processesBound() const;
		virtual void hashProcessedBound( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual Imath::Box3f computeProcessedBound( const ScenePath &path, const Gaffer::Context *context, const Imath::Box3f &inputBound ) const;
		
		virtual bool processesTransform() const;
		virtual void hashProcessedTransform( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual Imath::M44f computeProcessedTransform( const ScenePath &path, const Gaffer::Context *context, const Imath::M44f &inputTransform ) const;

		virtual bool processesAttributes() const;
		virtual void hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstCompoundObjectPtr computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputAttributes ) const;
		
		virtual bool processesObject() const;
		virtual void hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstObjectPtr computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const;
		//@}

	private :
	
		enum BoundMethod
		{
			PassThrough = 0,
			Direct = 1,
			Union = 2
		};
		
		BoundMethod boundMethod() const;
		
		static size_t g_firstPlugIndex;
	
};

} // namespace GafferScene

#endif // GAFFERSCENE_SCENEELEMENTPROCESSOR_H
