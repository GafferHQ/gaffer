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

#ifndef GAFFERSCENE_SCENEPLUG_H
#define GAFFERSCENE_SCENEPLUG_H

#include "GafferScene/Export.h"
#include "GafferScene/TypeIds.h"

#include "Gaffer/BoxPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/TypedPlug.h"

namespace GafferScene
{

/// The ScenePlug is used to pass scenegraphs between nodes in the gaffer graph. It is a compound
/// type, with subplugs for different aspects of the scene.
class GAFFERSCENE_API ScenePlug : public Gaffer::ValuePlug
{

	public :

		ScenePlug( const std::string &name=defaultName<ScenePlug>(), Direction direction=In, unsigned flags=Default );
		~ScenePlug() override;

		GAFFER_PLUG_DECLARE_TYPE( GafferScene::ScenePlug, ScenePlugTypeId, ValuePlug );

		bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const override;
		Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;
		/// Only accepts ScenePlug inputs.
		bool acceptsInput( const Gaffer::Plug *input ) const override;

		/// Child plugs
		/// ===========
		///
		/// Different properties of the scene are represented by different child
		/// plugs of the ScenePlug.

		/// Location properties
		/// -------------------
		///
		/// These plugs require the `scenePathContextName` variable to
		/// be provided by the current context.
		///
		/// The plug used to pass the bounding box of the current location in
		/// the scene graph. The bounding box is supplied _without_ the
		/// transform applied.
		Gaffer::AtomicBox3fPlug *boundPlug();
		const Gaffer::AtomicBox3fPlug *boundPlug() const;
		/// The plug used to pass the transform for the current location.
		Gaffer::M44fPlug *transformPlug();
		const Gaffer::M44fPlug *transformPlug() const;
		/// The plug used to pass the attribute state for the current location.
		Gaffer::CompoundObjectPlug *attributesPlug();
		const Gaffer::CompoundObjectPlug *attributesPlug() const;
		/// The plug used to pass the object for the current location.
		Gaffer::ObjectPlug *objectPlug();
		const Gaffer::ObjectPlug *objectPlug() const;
		/// The plug used to pass the names of the child locations of the current
		/// location in the scene graph.
		Gaffer::InternedStringVectorDataPlug *childNamesPlug();
		const Gaffer::InternedStringVectorDataPlug *childNamesPlug() const;
		/// Represents the existence of the current location. Value is
		/// `true` if the location exists and `false` otherwise. This is computed
		/// automatically by querying `childNamesPlug()` at all ancestor locations,
		/// but with significantly better performance than is achievable directly.
		Gaffer::BoolPlug *existsPlug();
		const Gaffer::BoolPlug *existsPlug() const;
		/// Provides the union of the bounding boxes of all the children
		/// of the current location, transformed using their respective
		/// transforms.
		Gaffer::AtomicBox3fPlug *childBoundsPlug();
		const Gaffer::AtomicBox3fPlug *childBoundsPlug() const;

		/// Global properties
		/// -----------------
		///
		/// The plug used to pass renderer options including output etc,
		/// represented as a CompoundObject. Note that this is not sensitive
		/// to the "scene:path" context entry.
		Gaffer::CompoundObjectPlug *globalsPlug();
		const Gaffer::CompoundObjectPlug *globalsPlug() const;
		/// The plug used to represent the names of available sets.
		/// Note that this is not sensitive to the "scene:path" context
		/// variable - sets are global to the scene. After retrieving
		/// the available names, individual sets can be retrieved from the
		/// setPlug().
		Gaffer::InternedStringVectorDataPlug *setNamesPlug();
		const Gaffer::InternedStringVectorDataPlug *setNamesPlug() const;
		/// Used to represent an individual set. This is sensitive
		/// to the scene:setName context variable which specifies
		/// which set to compute.
		Gaffer::PathMatcherDataPlug *setPlug();
		const Gaffer::PathMatcherDataPlug *setPlug() const;

		/// Context management
		/// ==================
		///
		/// The child Plugs are expected to be evaluated in the context
		/// of a particular location in the scenegraph, so that the
		/// scenegraph can be evaluated piecemeal, rather than all needing
		/// to exist at once. These members provide utilities for
		/// constructing relevant contexts.

		/// The type used to specify the current scene path in
		/// a Context object.
		typedef std::vector<IECore::InternedString> ScenePath;
		/// The name used to specify the current scene path in a
		/// Context object. You should use this variable instead
		/// of hardcoding strings - it is both less error prone
		/// and quicker than constructing a new InternedString
		/// each time.
		static const IECore::InternedString scenePathContextName;
		/// The name used to specify the name of the set to be
		/// computed in a Context.
		static const IECore::InternedString setNameContextName;

		/// Utility class to scope a temporary copy of a context,
		/// specifying the scene path.
		struct PathScope : public Gaffer::Context::EditableScope
		{
			/// Standard constructors, for modifying context on the current thread.
			PathScope( const Gaffer::Context *context );
			PathScope( const Gaffer::Context *context, const ScenePath &scenePath );

			/// Specialised constructors used to transfer state to TBB tasks. See
			/// ThreadState documentation for more details.
			PathScope( const Gaffer::ThreadState &threadState );
			PathScope( const Gaffer::ThreadState &threadState, const ScenePath &scenePath );

			void setPath( const ScenePath &scenePath );

			/// Forward compatibility with Gaffer 0.60
			PathScope( const Gaffer::Context *context, const ScenePath *scenePath );
			PathScope( const Gaffer::ThreadState &threadState, const ScenePath *scenePath );
			void setPath( const ScenePath *scenePath );
		};

		/// Utility class to scope a temporary copy of a context,
		/// specifying the set name.
		struct SetScope : public Gaffer::Context::EditableScope
		{
			/// Standard constructors, for modifying context on the current thread.
			SetScope( const Gaffer::Context *context );
			SetScope( const Gaffer::Context *context, const IECore::InternedString &setName );

			/// Specialised constructors used to transfer state to TBB tasks. See
			/// ThreadState documentation for more details.
			SetScope( const Gaffer::ThreadState &threadState );
			SetScope( const Gaffer::ThreadState &threadState, const IECore::InternedString &setName );

			void setSetName( const IECore::InternedString &setName );

			/// Forward compatibility with Gaffer 0.60
			SetScope( const Gaffer::Context *context, const IECore::InternedString *setName );
			SetScope( const Gaffer::ThreadState &threadState, const IECore::InternedString *setName );
			void setSetName( const IECore::InternedString *setName );
		};

		/// Utility class to scope a temporary copy of a context,
		/// with scene specific variables removed. This can be used
		/// when evaluating plugs which must not be sensitive
		/// to such variables, and can improve performance by
		/// reducing pressure on the hash cache.
		struct GlobalScope : public Gaffer::Context::EditableScope
		{
			/// Standard constructor, for modifying context on the current thread.
			GlobalScope( const Gaffer::Context *context );
			/// Specialised constructor used to transfer state to TBB tasks. See
			/// ThreadState documentation for more details.
			GlobalScope( const Gaffer::ThreadState &threadState );
		};

		/// Convenience accessors
		/// =====================
		///
		/// These functions create temporary Contexts specifying the necessary
		/// variables and then return the result of calling getValue() or hash()
		/// on the appropriate child plug. Note that if you wish to evaluate
		/// multiple plugs in the same context, better performance can be
		/// achieved using the appropriate scope class and calling hash() or
		/// getValue() directly.
		///
		/// > Note : It is a programming error to trigger a compute for a
		/// > location which does not exist. Use the `existsPlug()` and/or
		/// > the `exists()` method to verify existence where necessary.

		/// Returns the bound for the specified location.
		Imath::Box3f bound( const ScenePath &scenePath ) const;
		/// Returns the local transform at the specified scene path.
		Imath::M44f transform( const ScenePath &scenePath ) const;
		/// Returns the absolute (world) transform at the specified scene path.
		Imath::M44f fullTransform( const ScenePath &scenePath ) const;
		/// Returns just the attributes set at the specific scene path.
		IECore::ConstCompoundObjectPtr attributes( const ScenePath &scenePath ) const;
		/// Returns the full set of inherited attributes at the specified scene path.
		IECore::CompoundObjectPtr fullAttributes( const ScenePath &scenePath ) const;
		IECore::ConstObjectPtr object( const ScenePath &scenePath ) const;
		IECore::ConstInternedStringVectorDataPtr childNames( const ScenePath &scenePath ) const;
		/// Returns true if the specified location exists.
		bool exists( const ScenePath &scenePath ) const;
		/// Returns the union of the bounding boxes of all the children
		/// of `scenePath`, transformed using their respective transforms.
		Imath::Box3f childBounds( const ScenePath &scenePath ) const;
		/// Prefer this to bare `globalsPlug()->getValue()` calls when
		/// accessing globals from within a per-location computation. It
		/// uses GlobalScope to remove unnecessary context variables which
		/// could otherwise lead to poor cache performance.
		IECore::ConstCompoundObjectPtr globals() const;
		/// Prefer this to bare `setNamesPlug()->getValue()` calls when
		/// accessing set names from within a per-location computation. It
		/// uses GlobalScope to remove unnecessary context variables which
		/// could otherwise lead to poor cache performance.
		IECore::ConstInternedStringVectorDataPtr setNames() const;
		IECore::ConstPathMatcherDataPtr set( const IECore::InternedString &setName ) const;

		IECore::MurmurHash boundHash( const ScenePath &scenePath ) const;
		IECore::MurmurHash transformHash( const ScenePath &scenePath ) const;
		IECore::MurmurHash fullTransformHash( const ScenePath &scenePath ) const;
		IECore::MurmurHash attributesHash( const ScenePath &scenePath ) const;
		IECore::MurmurHash fullAttributesHash( const ScenePath &scenePath ) const;
		IECore::MurmurHash objectHash( const ScenePath &scenePath ) const;
		IECore::MurmurHash childNamesHash( const ScenePath &scenePath ) const;
		IECore::MurmurHash childBoundsHash( const ScenePath &scenePath ) const;
		/// See comments for `globals()` method.
		IECore::MurmurHash globalsHash() const;
		/// See comments for `setNames()` method.
		IECore::MurmurHash setNamesHash() const;
		IECore::MurmurHash setHash( const IECore::InternedString &setName ) const;

		/// Utility methods
		/// ===============

		/// Utility function to convert a string into a path by splitting on '/'.
		/// \todo Many of the places we use this, it would be preferable if the source data was already
		/// a path. Perhaps a ScenePathPlug could take care of this for us?
		static void stringToPath( const std::string &s, ScenePlug::ScenePath &path );
		static ScenePath stringToPath( const std::string &s );
		static void pathToString( const ScenePlug::ScenePath &path, std::string &s );
		static std::string pathToString( const ScenePlug::ScenePath &path );

		/// Deprecated methods
		/// ==================

		/// \deprecated Use `existsPlug()->getValue()` instead.
		bool exists() const;

	private :

		// Private plug used for the computation of `existsPlug()` by SceneNode.
		Gaffer::InternedStringVectorDataPlug *sortedChildNamesPlug();
		const Gaffer::InternedStringVectorDataPlug *sortedChildNamesPlug() const;
		friend class SceneNode;

};

IE_CORE_DECLAREPTR( ScenePlug );

typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, ScenePlug> > ScenePlugIterator;
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::In, ScenePlug> > InputScenePlugIterator;
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Out, ScenePlug> > OutputScenePlugIterator;

typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, ScenePlug>, Gaffer::PlugPredicate<> > RecursiveScenePlugIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::In, ScenePlug>, Gaffer::PlugPredicate<> > RecursiveInputScenePlugIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Out, ScenePlug>, Gaffer::PlugPredicate<> > RecursiveOutputScenePlugIterator;

} // namespace GafferScene

GAFFERSCENE_API std::ostream &operator << ( std::ostream &o, const GafferScene::ScenePlug::ScenePath &path );

#endif // GAFFERSCENE_SCENEPLUG_H
