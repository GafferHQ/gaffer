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

#ifndef GAFFER_SCENEPLUG_H
#define GAFFER_SCENEPLUG_H

#include "Gaffer/CompoundPlug.h"
#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/TypedPlug.h"
#include "Gaffer/BoxPlug.h"

#include "GafferScene/TypeIds.h"

namespace GafferScene
{

/// The ScenePlug is used to pass scenegraphs between nodes in the gaffer graph. It is a compound
/// type, with subplugs for different aspects of the scene.
class ScenePlug : public Gaffer::CompoundPlug
{

	public :
			
		ScenePlug( const std::string &name=staticTypeName(), Direction direction=In, unsigned flags=Default );
		virtual ~ScenePlug();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( ScenePlug, ScenePlugTypeId, CompoundPlug );

		virtual bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const;
				
		/// Only accepts ScenePlug inputs.
		virtual bool acceptsInput( const Gaffer::Plug *input ) const;
	
		/// @name Child plugs
		/// Different aspects of the scene are passed through different
		/// child plugs. Plugs are expected to be evaluated in the context
		/// of a particular parent in the scenegraph, so that the
		/// scenegraph can be evaluated piecemeal, rather than all needing
		/// to exist at once. This parent should be specified as a string
		/// context entry named "scene:path" - see below for utility functions
		/// which construct such a context automatically.
		////////////////////////////////////////////////////////////////////
		//@{
		/// The plug used to pass the bounding box of the current node in
		/// the scene graph. The bounding box is supplied /without/ the
		/// transform applied.
		Gaffer::AtomicBox3fPlug *boundPlug();
		const Gaffer::AtomicBox3fPlug *boundPlug() const;
		/// The plug used to pass the transform for the current node.
		Gaffer::M44fPlug *transformPlug();
		const Gaffer::M44fPlug *transformPlug() const;
		/// The plug used to pass the attribute state for the current node.
		/// This is represented as a collection of IECore::StateRenderables.
		Gaffer::CompoundObjectPlug *attributesPlug();
		const Gaffer::CompoundObjectPlug *attributesPlug() const;
		/// The plug used to pass the object for the current node.
		Gaffer::ObjectPlug *objectPlug();
		const Gaffer::ObjectPlug *objectPlug() const;
		/// The plug used to pass the names of the child nodes of the current node
		/// in the scene graph.
		Gaffer::StringVectorDataPlug *childNamesPlug();
		const Gaffer::StringVectorDataPlug *childNamesPlug() const;
		/// The plug used to pass renderer options including displays etc,
		/// represented as an ObjectVector of IECore::PreWorldRenderables.
		/// Note that this is not sensitive to the "scene:path" context
		/// entry.
		Gaffer::ObjectVectorPlug *globalsPlug();
		const Gaffer::ObjectVectorPlug *globalsPlug() const;
		//@}
		
		/// @name Convenience accessors
		/// These functions create temporary Contexts specifying the scenePath
		/// and then return the result of calling getValue() or hash() on the
		/// appropriate child plug.
		////////////////////////////////////////////////////////////////////
		//@{
		Imath::Box3f bound( const std::string &scenePath ) const;
		Imath::M44f transform( const std::string &scenePath ) const;
		IECore::ConstCompoundObjectPtr attributes( const std::string &scenePath ) const;
		IECore::ConstObjectPtr object( const std::string &scenePath ) const;
		IECore::ConstStringVectorDataPtr childNames( const std::string &scenePath ) const;
		
		IECore::MurmurHash boundHash( const std::string &scenePath ) const;
		IECore::MurmurHash transformHash( const std::string &scenePath ) const;
		IECore::MurmurHash attributesHash( const std::string &scenePath ) const;
		IECore::MurmurHash objectHash( const std::string &scenePath ) const;
		IECore::MurmurHash childNamesHash( const std::string &scenePath ) const;		
		//@}
	
};

IE_CORE_DECLAREPTR( ScenePlug );

typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, ScenePlug> > ScenePlugIterator;
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::In, ScenePlug> > InputScenePlugIterator;
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Out, ScenePlug> > OutputScenePlugIterator;

} // namespace GafferScene

#endif // GAFFER_SCENEPLUG_H
