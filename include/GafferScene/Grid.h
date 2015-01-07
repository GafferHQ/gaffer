//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, John Haddon. All rights reserved.
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

#ifndef GAFFERSCENE_GRID_H
#define GAFFERSCENE_GRID_H

#include "Gaffer/TransformPlug.h"

#include "GafferScene/SceneNode.h"

namespace GafferScene
{

class Grid : public SceneNode
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::Grid, GridTypeId, SceneNode );

		Grid( const std::string &name=defaultName<Grid>() );
		virtual ~Grid();

		Gaffer::StringPlug *namePlug();
		const Gaffer::StringPlug *namePlug() const;

		Gaffer::TransformPlug *transformPlug();
		const Gaffer::TransformPlug *transformPlug() const;

		Gaffer::V2fPlug *dimensionsPlug();
		const Gaffer::V2fPlug *dimensionsPlug() const;

		Gaffer::FloatPlug *spacingPlug();
		const Gaffer::FloatPlug *spacingPlug() const;

		Gaffer::Color3fPlug *gridColorPlug();
		const Gaffer::Color3fPlug *gridColorPlug() const;

		Gaffer::Color3fPlug *centerColorPlug();
		const Gaffer::Color3fPlug *centerColorPlug() const;

		Gaffer::Color3fPlug *borderColorPlug();
		const Gaffer::Color3fPlug *borderColorPlug() const;

		Gaffer::FloatPlug *gridPixelWidthPlug();
		const Gaffer::FloatPlug *gridPixelWidthPlug() const;

		Gaffer::FloatPlug *centerPixelWidthPlug();
		const Gaffer::FloatPlug *centerPixelWidthPlug() const;

		Gaffer::FloatPlug *borderPixelWidthPlug();
		const Gaffer::FloatPlug *borderPixelWidthPlug() const;

		virtual void affects( const Gaffer::Plug *input, Gaffer::DependencyNode::AffectedPlugsContainer &outputs ) const;

	protected :

		virtual void hashBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashTransform( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashObject( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashChildNames( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;

		virtual Imath::Box3f computeBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual Imath::M44f computeTransform( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstCompoundObjectPtr computeAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstObjectPtr computeObject( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstInternedStringVectorDataPtr computeChildNames( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstCompoundObjectPtr computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Grid );

} // namespace GafferScene

#endif // GAFFERSCENE_GRID_H
