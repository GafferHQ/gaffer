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

#pragma once

#include "GafferScene/FilteredSceneProcessor.h"

namespace GafferScene
{

/// \todo Replace with a range of more specific base classes, deprecate and remove.
/// We already have AttributeProcessor, ObjectProcessor and Deformer, and it looks
/// like a TransformProcessor would get us most of the rest of the way.
class GAFFERSCENE_API SceneElementProcessor : public FilteredSceneProcessor
{

	public :

		explicit SceneElementProcessor( const std::string &name=defaultName<SceneElementProcessor>(), IECore::PathMatcher::Result filterDefault = IECore::PathMatcher::EveryMatch );
		~SceneElementProcessor() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::SceneElementProcessor, SceneElementProcessorTypeId, FilteredSceneProcessor );

		/// Implemented so that each child of inPlug() affects the corresponding child of outPlug()
		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		/// Implemented to call hashProcessedBound() where appropriate.
		void hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		/// Implemented to call hashProcessedTransform() where appropriate.
		void hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		/// Implemented to call hashProcessedAttributes() where appropriate.
		void hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		/// Implemented to call hashProcessedObject() where appropriate.
		void hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;

		/// Implemented to call computeProcessedBound() where appropriate.
		Imath::Box3f computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		/// Implemented to call computeProcessedTransform() where appropriate.
		Imath::M44f computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		/// Implemented to call computeProcessedAttributes() where appropriate.
		IECore::ConstCompoundObjectPtr computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		/// Implemented to call computeProcessedObject() where appropriate.
		IECore::ConstObjectPtr computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;

		/// @name Scene processing methods
		/// These methods should be reimplemented by derived classes to process the input scene - they will be called as
		/// appropriate based on the result of the filter applied to the node. To process a particular
		/// aspect of the scene you must reimplement processesAspect() to return true, reimplement
		/// hashAspect() to append to the hash appropriately (the path will already have been appended),
		/// and finally reimplement the processAspect() function to perform the processing. Note that the implementation
		/// of processesAspect() is expected to return a constant - returning different values for different scene paths
		/// is currently not supported (this is because the bound computation may need to take into account child locations).
		/// \todo Review the use of the processes*() methods - see comments in StandardAttributes.cpp.
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

		/// Note that if you implement processesObject() in such a way as to deform the object, you /must/ also
		/// implement processesBound() appropriately.
		virtual bool processesObject() const;
		virtual void hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstObjectPtr computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const;
		//@}

	private :

		enum BoundMethod
		{
			PassThrough = 0,
			Processed = 1,
			Union = 2
		};

		BoundMethod boundMethod( const Gaffer::Context *context ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( SceneElementProcessor )

} // namespace GafferScene
