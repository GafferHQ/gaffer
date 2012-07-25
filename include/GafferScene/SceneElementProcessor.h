//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferScene/SceneProcessor.h"

namespace GafferScene
{

/// The SceneElementProcessor class provides a base class for modifying elements of an input
/// scene while leaving the scene hierarchy unchanged.
class SceneElementProcessor : public SceneProcessor
{

	public :

		SceneElementProcessor( const std::string &name=staticTypeName() );
		virtual ~SceneElementProcessor();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( SceneElementProcessor, SceneElementProcessorTypeId, SceneProcessor );
		
		Gaffer::IntPlug *filterPlug();
		const Gaffer::IntPlug *filterPlug() const;
		
		/// Implemented so that each child of inPlug() affects the corresponding child of outPlug()
		virtual void affects( const Gaffer::ValuePlug *input, AffectedPlugsContainer &outputs ) const;
				
	protected :

		/// Implemented to prevent non-Filter nodes being connected to the filter plug.
		virtual bool acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const;
		
		/// Implemented to call processBound().
		virtual Imath::Box3f computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		/// Implemented to call processTransform().
		virtual Imath::M44f computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		/// Implemented to call processAttributes().
		virtual IECore::CompoundObjectPtr computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		/// Implemented to call processObject().
		virtual IECore::ObjectPtr computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		/// Implemented as a pass-through.
		virtual IECore::StringVectorDataPtr computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		/// Implemented as a pass-through.
		virtual IECore::ObjectVectorPtr computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const;
		
		/// May be reimplemented by derived classes to process the input scene. These methods will only be called for paths matching
		/// the filter applied to this node. Note that in the case of processBound(), modifications will automatically be propagated to
		/// parent paths. This comes at some expense, so subclasses that intend to process the bound must implement processesBound() to
		/// return true to enable this behaviour.
		virtual Imath::Box3f processBound( const ScenePath &path, const Gaffer::Context *context, const Imath::Box3f &inputBound ) const;
		/// Defaults to false - if you override processBound, you /must/ reimplement this to return true.
		virtual bool processesBound() const;
		virtual Imath::M44f processTransform( const ScenePath &path, const Gaffer::Context *context, const Imath::M44f &inputTransform ) const;
		virtual IECore::CompoundObjectPtr processAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputAttributes ) const;
		/// Note that if you change the bound of object, you need to reimplement both processBound() and processesBound().
		virtual IECore::ObjectPtr processObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const;
		
};

} // namespace GafferScene

#endif // GAFFERSCENE_SCENEELEMENTPROCESSOR_H
