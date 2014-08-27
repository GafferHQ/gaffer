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

#ifndef GAFFERSCENE_SCENEMIXINBASE_H
#define GAFFERSCENE_SCENEMIXINBASE_H

#include "GafferScene/SceneProcessor.h"

namespace GafferScene
{

/// The Gaffer module defines templated generic classes such as TimeWarp and Switch which are capable
/// of operating with any sort of input and output plug. This functionality can then be
/// mixed in to SceneProcessor via way of the SceneMixinBase class, which is used as the base
/// class for instantiations of the generic classes. Other modules may define equivalent MixinBase
/// classes, allowing us to reuse generic code for the creation of a great many unique node types.
///
/// The main reason the SceneMixinBase class exists is to stub out the virtual hash*() and compute*()
/// methods which must be implemented, but which are actually unnecessary because the mixed-in class
/// provides a complete implementation of hash() and compute() that will never call them. This is perhaps
/// a little ugly, but it lets us implement some complex functionality in a way that can be shared and
/// reused across multiple modules, providing nodes familiar to the user in each module they use. Other
/// options would be :
///
/// - Have untemplated generic classes, which are instantiated and then have dynamic plugs added to make them
/// look like a SceneProcessor. This has the downside that we can't do simple searches for all SceneProcessor
/// nodes, because there's no common base class.
///
/// - Have totally unrelated SceneTimeWarp and ImageTimeWarp classes that don't share code. Seems like a waste
/// of time, particularly as we add more generic mixin classes and more processing modules.
///
/// - Have mixin classes that aren't intended to derive from Node but instead just provide helper functions for
/// adding plugs and computing. This would also mean more unshared code in the actual SceneTimeWarp and ImageTimeWarp
/// classes.
///
/// - Not define the compute* methods on SceneNode, but that makes the implementations of all the other SceneNode
/// subclasses more painful.
///
/// In short, although there is some template funkiness going on here, this is the most pragmatic way of
/// providing a common set of functionality across the various scene/image/whatever processing modules.
class SceneMixinBase : public SceneProcessor
{

	public :

		SceneMixinBase( const std::string &name=defaultName<SceneMixinBase>() );
		virtual ~SceneMixinBase();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::SceneMixinBase, SceneMixinBaseTypeId, SceneProcessor );

	private :

		/// These stubs should never be called, because the mixed-in class should implement hash() and compute()
		/// totally. If they are called, they throw to highlight the fact that something is amiss.
		virtual void hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;

		/// These stubs should never be called, because the mixed-in class should implement hash() and compute()
		/// totally. If they are called, they throw to highlight the fact that something is amiss.
		virtual Imath::Box3f computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual Imath::M44f computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstCompoundObjectPtr computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstObjectPtr computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstInternedStringVectorDataPtr computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstCompoundObjectPtr computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const;

};

IE_CORE_DECLAREPTR( SceneMixinBase )

} // namespace GafferScene

#endif // GAFFERSCENE_SCENEMIXINBASE_H
