//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014-2016, John Haddon. All rights reserved.
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

#include "GafferSceneUI/TransformTool.h"

#include "GafferSceneUI/SceneView.h"
#include "GafferSceneUI/ContextAlgo.h"

#include "GafferScene/AimConstraint.h"
#include "GafferScene/EditScopeAlgo.h"
#include "GafferScene/Group.h"
#include "GafferScene/ObjectSource.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/SceneReader.h"
#include "GafferScene/Transform.h"

#include "Gaffer/Animation.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Spreadsheet.h"

#include "IECore/AngleConversion.h"

#include "OpenEXR/ImathMatrixAlgo.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind.hpp"
#include "boost/unordered_map.hpp"

#include <memory>
#include <unordered_set>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

M44f signOnlyScaling( const M44f &m )
{
	V3f scale;
	V3f shear;
	V3f rotate;
	V3f translate;

	extractSHRT( m, scale, shear, rotate, translate );

	M44f result;

	result.translate( translate );
	result.rotate( rotate );
	result.shear( shear );
	result.scale( V3f( Imath::sign( scale.x ), Imath::sign( scale.y ), Imath::sign( scale.z ) ) );

	return result;
}

// Similar to `plug->source()`, but able to traverse through
// Spreadsheet outputs to find the appropriate input row.
V3fPlug *spreadsheetAwareSource( V3fPlug *plug, std::string &failureReason )
{
	plug = plug->source<V3fPlug>();
	if( !plug )
	{
		// Source is not a V3fPlug. Not much we can do about that.
		failureReason = "Plug input is not a V3fPlug";
		return nullptr;
	}

	auto *spreadsheet = runTimeCast<Spreadsheet>( plug->node() );
	if( !spreadsheet )
	{
		return plug;
	}

	if( !spreadsheet->outPlug()->isAncestorOf( plug ) )
	{
		return plug;
	}

	plug = static_cast<V3fPlug *>( spreadsheet->activeInPlug( plug ) );
	if( plug->ancestor<Spreadsheet::RowPlug>() == spreadsheet->rowsPlug()->defaultRow() )
	{
		// Default spreadsheet row. Editing this could affect any number
		// of unrelated objects, so don't allow that.
		failureReason = "Cannot edit default spreadsheet row";
		return nullptr;
	}

	return plug->source<V3fPlug>();
}

GraphComponent *editTargetOrNull( const TransformTool::Selection &selection )
{
	return selection.editable() ? selection.editTarget() : nullptr;
}

class HandlesGadget : public Gadget
{

	public :

		HandlesGadget( const std::string &name="HandlesGadget" )
			:	Gadget( name )
		{
		}

	protected :

		void renderLayer( Layer layer, const Style *style, RenderReason reason ) const override
		{
			if( layer != Layer::MidFront )
			{
				return;
			}

			// Clear the depth buffer so that the handles render
			// over the top of the SceneGadget. Otherwise they are
			// unusable when the object is larger than the handles.
			/// \todo Can we really justify this approach? Does it
			/// play well with new Gadgets we'll add over time? If
			/// so, then we should probably move the depth clearing
			/// to `Gadget::render()`, in between each layer. If
			/// not we'll need to come up with something else, perhaps
			/// going back to punching a hole in the depth buffer using
			/// `glDepthFunc( GL_GREATER )`. Or maybe an option to
			/// render gadgets in an offscreen buffer before compositing
			/// them over the current framebuffer?
			glClearDepth( 1.0f );
			glClear( GL_DEPTH_BUFFER_BIT );
			glEnable( GL_DEPTH_TEST );

		}

		unsigned layerMask() const override
		{
			return (unsigned)Layer::MidFront;
		}

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// TransformTool::Selection
//////////////////////////////////////////////////////////////////////////

/// \todo Work out how to avoid baking graph component names into message
/// strings. We decided to put up with the stale name bugs here as the benefit
/// of better informing user outweighs the (hopefully less frequent) times
/// that the message is out of date.

TransformTool::Selection::Selection()
	:	m_editable( false )
{
}

TransformTool::Selection::Selection(
	const GafferScene::ConstScenePlugPtr scene,
	const GafferScene::ScenePlug::ScenePath &path,
	const Gaffer::ConstContextPtr &context,
	const Gaffer::EditScopePtr &editScope
)
	:	m_scene( scene ), m_path( path ), m_context( context ), m_editable( false ), m_editScope( editScope ), m_aimConstraint( false )
{
	Context::Scope scopedContext( context.get() );
	if( path.empty() )
	{
		m_warning = "Cannot edit root transform";
		return;
	}
	else if( !scene->exists( path ) )
	{
		m_warning = "Location does not exist";
		return;
	}

	// We disallow editing of any locations that have zero scale at any point in the
	// hierarchy. This causes untold trouble in all sorts of places.
	// We use this somewhat long winded detection approach to ensure we'll hit the same
	// failure cases as we would do later on using imath with the same matrices.
	const M44f fullTransform = scene->fullTransform( path );
	V3f unusedScale;
	if( !extractScaling( fullTransform, unusedScale, false ) )
	{
		m_warning = "Location has zero scale";
		return;
	}

	bool editScopeFound = false;
	while( m_path.size() )
	{
		SceneAlgo::History::Ptr history = SceneAlgo::history( scene->transformPlug(), m_path );
		initWalk( history.get(), editScopeFound );
		if( editable() )
		{
			break;
		}
		m_path.pop_back();
	}

	if( !editable() && m_path.size() != path.size() )
	{
		// Attempts to edit a parent path failed. Reset to
		// the original path so we don't confuse client code.
		m_path = path;
	}

	if( editScope && !editScopeFound )
	{
		m_warning = "The target EditScope \"" + displayName( editScope.get() ) + "\" is not in the scene history";
		m_editable = false;
		return;
	}

	if( m_path.size() != path.size() )
	{
		std::string pathString;
		GafferScene::ScenePlug::pathToString( m_path, pathString );
		m_warning = "Editing parent location \"" + pathString + "\"";
	}
}

void TransformTool::Selection::initFromHistory( const GafferScene::SceneAlgo::History *history )
{
	m_upstreamScene = history->scene;
	m_upstreamPath = history->context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	m_upstreamContext = history->context;
}

void TransformTool::Selection::initFromSceneNode( const GafferScene::SceneAlgo::History *history )
{
	// Check for SceneNode and return if there isn't one or it is disabled.

	const SceneNode *node = runTimeCast<const SceneNode>( history->scene->node() );
	if( !node )
	{
		return;
	}

	Context::Scope scopedContext( history->context.get() );
	if( !node->enabledPlug()->getValue() )
	{
		return;
	}

	// Check for AimConstraints. These must be accounted for in `sceneToTransformSpace()`.

	if( auto constraint = runTimeCast<const AimConstraint>( node ) )
	{
		if(
			history->scene == constraint->outPlug() &&
			( constraint->filterPlug()->match( constraint->inPlug() ) & PathMatcher::ExactMatch )
		)
		{
			m_aimConstraint = true;
			return;
		}
	}

	// Determine if node edits the transform at this location.

	TransformPlug *transformPlug = nullptr;
	if( const ObjectSource *objectSource = runTimeCast<const ObjectSource>( node ) )
	{
		if( history->scene == objectSource->outPlug() )
		{
			transformPlug = const_cast<TransformPlug *>( objectSource->transformPlug() );
			m_transformSpace = M44f();
		}
	}
	else if( const Group *group = runTimeCast<const Group>( node ) )
	{
		const ScenePlug::ScenePath &path = history->context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
		if( history->scene == group->outPlug() && path.size() == 1 )
		{
			transformPlug = const_cast<TransformPlug *>( group->transformPlug() );
			m_transformSpace = M44f();
		}
	}
	else if( const GafferScene::Transform *transform = runTimeCast<const GafferScene::Transform>( node ) )
	{
		if(
			history->scene == transform->outPlug() &&
			( transform->filterPlug()->match( transform->inPlug() ) & PathMatcher::ExactMatch )
		)
		{
			transformPlug = const_cast<TransformPlug *>( transform->transformPlug() );
			ScenePlug::ScenePath spacePath = history->context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
			switch( (GafferScene::Transform::Space)transform->spacePlug()->getValue() )
			{
				case GafferScene::Transform::Local :
					m_transformSpace = transform->inPlug()->fullTransform( spacePath );
					break;
				case GafferScene::Transform::Parent :
				case GafferScene::Transform::ResetLocal :
					spacePath.pop_back();
					// We pull from `outPlug()` rather than `inPlug()` because the Transform
					// node may also be editing the parent transform.
					m_transformSpace = transform->outPlug()->fullTransform( spacePath );
					break;
				case GafferScene::Transform::World :
				case GafferScene::Transform::ResetWorld :
					m_transformSpace = M44f();
					break;
			}
		}
	}
	else if( const GafferScene::SceneReader *sceneReader = runTimeCast<const GafferScene::SceneReader>( node ) )
	{
		const ScenePlug::ScenePath &path = history->context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
		if( history->scene == sceneReader->outPlug() && path.size() == 1 )
		{
			transformPlug = const_cast<TransformPlug *>( sceneReader->transformPlug() );
			m_transformSpace = M44f();
		}
	}

	if( !transformPlug )
	{
		return;
	}

	// We found the TransformPlug and the upstream scene which authors the transform.
	// Recording this will terminate the search in `initWalk()`.

	initFromHistory( history );

	// Now figure out if we're allowed to edit the transform, and set ourselves up
	// for editing if we are.

	TransformEdit transformEdit(
		spreadsheetAwareSource( transformPlug->translatePlug(), m_warning ),
		spreadsheetAwareSource( transformPlug->rotatePlug(), m_warning ),
		spreadsheetAwareSource( transformPlug->scalePlug(), m_warning ),
		spreadsheetAwareSource( transformPlug->pivotPlug(), m_warning )
	);

	if( !transformEdit.translate || !transformEdit.rotate || !transformEdit.scale || !transformEdit.pivot )
	{
		// `spreadsheetAwareSource()` will have assigned to `m_warning` already.
		return;
	}

	const auto readOnlyAncestors = {
		MetadataAlgo::readOnlyReason( transformEdit.translate.get() ),
		MetadataAlgo::readOnlyReason( transformEdit.rotate.get() ),
		MetadataAlgo::readOnlyReason( transformEdit.scale.get() ),
		MetadataAlgo::readOnlyReason( transformEdit.pivot.get() ),
	};

	for( auto graphComponent : readOnlyAncestors )
	{
		// Unlike normal read-only nodes, the user won't be able to simply
		// unlock a reference node, so we disable editing.
		if( const Node *node = runTimeCast<const Node>( graphComponent ) )
		{
			if( Gaffer::MetadataAlgo::getChildNodesAreReadOnly( node ) )
			{
				m_warning = "Transform is locked as it is inside \"" + displayName( node ) + "\" which disallows edits to its children";
				return;
			}
		}

		if( graphComponent )
		{
			m_warning = "\"" + displayName( graphComponent ) + "\" is locked";
			break;
		}
	}

	m_editable = true;
	m_transformEdit = transformEdit;
}

void TransformTool::Selection::initFromEditScope( const GafferScene::SceneAlgo::History *history )
{
	initFromHistory( history );

	Context::Scope scopedContext( m_upstreamContext.get() );

	if( !m_editScope->enabledPlug()->getValue() )
	{
		m_warning = "The target EditScope \"" + displayName( m_editScope.get() ) + "\" is disabled";
		return;
	}

	if( const GraphComponent *readOnlyComponent = EditScopeAlgo::transformEditReadOnlyReason( m_editScope.get(), m_upstreamPath ) )
	{
		m_warning = "\"" + displayName( readOnlyComponent ) + "\" is locked";
		return;
	}

	m_editable = true;

	m_transformEdit = EditScopeAlgo::acquireTransformEdit( m_editScope.get(), m_upstreamPath, /* createIfNeccesary = */ false );

	ScenePlug::ScenePath spacePath = m_upstreamPath;
	spacePath.pop_back();
	m_transformSpace = m_upstreamScene->fullTransform( spacePath );
}

void TransformTool::Selection::initWalk( const GafferScene::SceneAlgo::History *history, bool &editScopeFound, const GafferScene::SceneAlgo::History *editScopeOutHistory )
{
	// Walk the history looking for a suitable node to edit.
	// Transform tools only support editing the last node to author the targets
	// transform (otherwise manipulators may be incorrectly placed or the
	// transform overwritten).

	Node *node = history->scene->node();

	if( !m_upstreamScene )
	{
		// First, check for a supported node in this history entry
		initFromSceneNode( history );

		// If we found a node to edit here and the user has requested a
		// specific scope, check if the edit is in it.
		if( m_upstreamScene && m_editScope )
		{
			editScopeFound = m_upstreamScene->ancestor<EditScope>() == m_editScope;
		}
	}

	// If the user has requested an edit scope, and we've not found it yet,
	// check this entry.  We do this regardless of whether we already have an
	// edit so we can differentiate between a missing edit scope and one that
	// is overridden downstream.
	if( m_editScope && !editScopeFound )
	{
		EditScope *editScope = runTimeCast<EditScope>( node );

		if( editScope && editScope == m_editScope )
		{
			if( m_upstreamScene )
			{
				// If we're here with an existing edit, then it means it is
				// downstream of the requested scope.
				editScopeFound = true;

				m_warning = "The target EditScope \"" + displayName( m_editScope.get() ) + "\" is overridden downstream by \"" + displayName( m_upstreamScene->node() ) + "\"";
				m_editable = false;
			}
			else if( history->scene == editScope->outPlug() )
			{
				// We only consider using an EditScope to author new edits on
				// the way in (from the Node Graph perspective). This allows nodes
				// inside to take precedence, however we need to use the
				// history from the scopes output, so keep track of it for the
				// rest of the walk.
				editScopeOutHistory = history;
			}
			else if( history->scene == editScope->inPlug() )
			{
				editScopeFound = true;

				if( editScopeOutHistory )
				{
					initFromEditScope( editScopeOutHistory );
				}
				else
				{
					// This can happen if the viewed node is inside the chosen EditScope
					m_warning = "The output of the target EditScope \"" + displayName( m_editScope.get() ) + "\" is not in the scene history";
					m_editable = false;
				}
			}
		}
	}

	if( initRequirementsSatisfied( editScopeFound ) )
	{
		return;
	}

	for( const auto &p : history->predecessors )
	{
		initWalk( p.get(), editScopeFound, editScopeOutHistory );

		if( initRequirementsSatisfied( editScopeFound ) )
		{
			return;
		}
	}

	// If we get to here, we've exhausted all upstream history, without finding
	// the input to the chosen scope. This can happen if the object is created
	// inside a nested edit scope - as we can't use the creation node as it is
	// in another scope. The requested scope is still valid though.
	if( editScopeOutHistory && history->scene == editScopeOutHistory->scene )
	{
		editScopeFound = true;
		initFromEditScope( editScopeOutHistory );
	}
}

bool TransformTool::Selection::initRequirementsSatisfied( bool editScopeFound )
{
	// If we don't have an EditScope specified, having a node to edit is enough.
	// If we do, we need to make sure we have found it.
	return ( m_upstreamScene && !m_editScope ) || ( m_editScope && editScopeFound );
}

const GafferScene::ScenePlug *TransformTool::Selection::scene() const
{
	return m_scene.get();
}

const GafferScene::ScenePlug::ScenePath &TransformTool::Selection::path() const
{
	return m_path;
}

const Gaffer::Context *TransformTool::Selection::context() const
{
	return m_context.get();
}

const GafferScene::ScenePlug *TransformTool::Selection::upstreamScene() const
{
	return m_upstreamScene.get();
}

const GafferScene::ScenePlug::ScenePath &TransformTool::Selection::upstreamPath() const
{
	return m_upstreamPath;
}

const Gaffer::Context *TransformTool::Selection::upstreamContext() const
{
	return m_upstreamContext.get();
}

bool TransformTool::Selection::editable() const
{
	return m_editable;
}

const std::string &TransformTool::Selection::warning() const
{
	return m_warning;
}

std::optional<TransformTool::Selection::TransformEdit> TransformTool::Selection::acquireTransformEdit( bool createIfNecessary ) const
{
	throwIfNotEditable();
	if( !m_transformEdit && createIfNecessary )
	{
		assert( m_editScope );
		V3f translate, rotate, scale, pivot;
		transform( translate, rotate, scale, pivot );

		m_transformEdit = EditScopeAlgo::acquireTransformEdit( m_editScope.get(), upstreamPath() );
		m_transformEdit->translate->setValue( translate );
		m_transformEdit->rotate->setValue( rotate );
		m_transformEdit->scale->setValue( scale );
		m_transformEdit->pivot->setValue( pivot );
	}
	return m_transformEdit;
}

const EditScope *TransformTool::Selection::editScope() const
{
	return m_editScope.get();
}

Gaffer::GraphComponent *TransformTool::Selection::editTarget() const
{
	throwIfNotEditable();
	if( m_editScope && !m_transformEdit )
	{
		return m_editScope.get();
	}
	else
	{
		assert( m_transformEdit );
		if( auto a = m_transformEdit->translate->ancestor<TransformPlug>() )
		{
			return a;
		}
		else if( auto a = m_transformEdit->translate->ancestor<Spreadsheet::RowPlug>() )
		{
			return a;
		}
		else
		{
			return m_transformEdit->translate->node();
		}
	}
}

const Imath::M44f &TransformTool::Selection::transformSpace() const
{
	throwIfNotEditable();
	return m_transformSpace;
}

void TransformTool::Selection::throwIfNotEditable() const
{
	if( !editable() )
	{
		throw IECore::Exception( "Selection is not editable" );
	}
}

Imath::M44f TransformTool::Selection::transform( Imath::V3f &translate, Imath::V3f &rotate, Imath::V3f &scale, Imath::V3f &pivot ) const
{
	throwIfNotEditable();

	Context::Scope upstreamScope( upstreamContext() );

	if( m_transformEdit )
	{
		translate = m_transformEdit->translate->getValue();
		rotate = m_transformEdit->rotate->getValue();
		scale = m_transformEdit->scale->getValue();
		pivot = m_transformEdit->pivot->getValue();
		return m_transformEdit->matrix();
	}
	else
	{
		// We're targeting an EditScope but haven't created the transform
		// plug yet (and don't want to until the user asks). Figure out the
		// values we'll use when we do create that plug.
		const M44f m = m_upstreamScene->transformPlug()->getValue();
		V3f shear;
		extractSHRT( m, scale, shear, rotate, translate );
		M44f result;
		result.translate( translate );
		result.rotate( rotate );
		result.scale( scale );
		pivot = V3f( 0 );
		rotate = IECore::radiansToDegrees( rotate );
		return result;
	}
}

Imath::M44f TransformTool::Selection::sceneToTransformSpace() const
{
	throwIfNotEditable();

	// The scenes produced by `scene()` and `upstreamScene()` may
	// be completely different :
	//
	// - The hierarchies may be different, often due to something like
	//   a Group node inserted between the two.
	// - The parent transforms of `path()` and `upstreamPath()` may
	//   be different, either due to a Group or an intermediate edit
	//   to the parent location.
	//
	// To account for this we align the two scenes by finding the
	// difference between the full transforms of `path()` and
	// `upstreamPath()`.
	//
	// This is made trickier by the presence of AimConstraints
	// between `upstreamScene()` and `scene()`. These overwrite
	// the local rotation from upstream, meaning we no longer have
	// a direct correspondence between the upstream and downstream
	// spaces. In this event we omit the local matrix entirely by
	// aligning the parent transforms instead.
	//
	// \todo I suspect the truth of the situation is more nuanced
	// than this and the correct approach depends on the type of
	// constraint and its order of composition with the edits we make
	// to the upstream transform. We are fortunate to be able to ignore
	// PointConstraints for now because we only transform direction vectors
	// with `sceneToTransformSpace()`. I'm sure there is a more principled
	// approach than the blunt instrument used here.

	M44f downstreamMatrix;
	{
		Context::Scope scopedContext( context() );
		if( !m_aimConstraint )
		{
			downstreamMatrix = scene()->fullTransform( path() );
		}
		else if( path().size() )
		{
			ScenePlug::ScenePath parentPath = path(); parentPath.pop_back();
			downstreamMatrix = scene()->fullTransform( parentPath );
		}
	}

	M44f upstreamMatrix;
	{
		Context::Scope scopedContext( upstreamContext() );
		if( !m_aimConstraint )
		{
			upstreamMatrix = upstreamScene()->fullTransform( upstreamPath() );
		}
		else if( upstreamPath().size() )
		{
			ScenePlug::ScenePath upstreamParentPath = upstreamPath(); upstreamParentPath.pop_back();
			upstreamMatrix = upstreamScene()->fullTransform( upstreamParentPath );
		}
	}

	return downstreamMatrix.inverse() * upstreamMatrix * transformSpace().inverse();
}

Imath::M44f TransformTool::Selection::transformToLocalSpace() const
{
	throwIfNotEditable();

	M44f downstreamMatrix;
	{
		Context::Scope scopedContext( context() );
		downstreamMatrix = scene()->fullTransform( path() );
	}

	M44f upstreamMatrix;
	{
		Context::Scope scopedContext( upstreamContext() );
		upstreamMatrix = upstreamScene()->fullTransform( upstreamPath() );
	}

	return transformSpace() * upstreamMatrix.inverse() * downstreamMatrix;
}

Imath::M44f TransformTool::Selection::orientedTransform( Orientation orientation ) const
{
	throwIfNotEditable();

	Context::Scope scopedContext( context() );

	// Get a matrix with the orientation we want

	M44f result;
	{
		switch( orientation )
		{
			case Local :
				result = scene()->fullTransform( path() );
				break;
			case Parent :
				if( path().size() )
				{
					const ScenePlug::ScenePath parentPath( path().begin(), path().end() - 1 );
					result = scene()->fullTransform( parentPath );
				}
				break;
			case World :
				result = M44f();
				break;
		}
	}

	result = signOnlyScaling( result );

	// And reset the translation to put it where the pivot is

	V3f translate, rotate, scale, pivot;
	transform( translate, rotate, scale, pivot );

	const V3f transformSpacePivot = pivot + translate;
	const V3f downstreamWorldPivot = transformSpacePivot * transformToLocalSpace();

	result[3][0] = downstreamWorldPivot[0];
	result[3][1] = downstreamWorldPivot[1];
	result[3][2] = downstreamWorldPivot[2];

	return result;
}

std::string TransformTool::Selection::displayName( const GraphComponent *component )
{
	return component->relativeName( component->ancestor<ScriptNode>() );
}

//////////////////////////////////////////////////////////////////////////
// TransformTool
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( TransformTool );

size_t TransformTool::g_firstPlugIndex = 0;

TransformTool::TransformTool( SceneView *view, const std::string &name )
	:	SelectionTool( view, name ),
		m_handles( new HandlesGadget() ),
		m_handlesDirty( true ),
		m_selectionDirty( true ),
		m_priorityPathsDirty( true ),
		m_dragging( false ),
		m_mergeGroupId( 0 )
{
	view->viewportGadget()->addChild( m_handles );
	m_handles->setVisible( false );

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ScenePlug( "__scene", Plug::In ) );
	addChild( new FloatPlug( "size", Plug::In, 1.0f, 0.0f ) );

	scenePlug()->setInput( view->inPlug<ScenePlug>() );

	view->viewportGadget()->keyPressSignal().connect( boost::bind( &TransformTool::keyPress, this, ::_2 ) );
	plugDirtiedSignal().connect( boost::bind( &TransformTool::plugDirtied, this, ::_1 ) );
	view->plugDirtiedSignal().connect( boost::bind( &TransformTool::plugDirtied, this, ::_1 ) );

	connectToViewContext();
	view->contextChangedSignal().connect( boost::bind( &TransformTool::connectToViewContext, this ) );

	Metadata::plugValueChangedSignal().connect( boost::bind( &TransformTool::metadataChanged, this, ::_3 ) );
	Metadata::nodeValueChangedSignal().connect( boost::bind( &TransformTool::metadataChanged, this, ::_2 ) );
}

TransformTool::~TransformTool()
{
}

const std::vector<TransformTool::Selection> &TransformTool::selection() const
{
	updateSelection();
	return m_selection;
}

bool TransformTool::selectionEditable() const
{
	const auto &s = selection();
	if( s.empty() )
	{
		return false;
	}
	for( const auto &e : s )
	{
		if( !e.editable() )
		{
			return false;
		}
	}
	return true;
}

TransformTool::SelectionChangedSignal &TransformTool::selectionChangedSignal()
{
	return m_selectionChangedSignal;
}

Imath::M44f TransformTool::handlesTransform()
{
	updateSelection();
	if( !selectionEditable() )
	{
		throw IECore::Exception( "Selection not editable" );
	}

	if( m_handlesDirty )
	{
		updateHandles( sizePlug()->getValue() * 75 );
		m_handlesDirty = false;
	}

	return handles()->getTransform();
}

GafferScene::ScenePlug *TransformTool::scenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const GafferScene::ScenePlug *TransformTool::scenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::FloatPlug *TransformTool::sizePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::FloatPlug *TransformTool::sizePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

GafferUI::Gadget *TransformTool::handles()
{
	return m_handles.get();
}

const GafferUI::Gadget *TransformTool::handles() const
{
	return m_handles.get();
}

bool TransformTool::affectsHandles( const Gaffer::Plug *input ) const
{
	return input == sizePlug();
}

void TransformTool::connectToViewContext()
{
	m_contextChangedConnection = view()->getContext()->changedSignal().connect( boost::bind( &TransformTool::contextChanged, this, ::_2 ) );
}

void TransformTool::contextChanged( const IECore::InternedString &name )
{
	if(
		ContextAlgo::affectsSelectedPaths( name ) ||
		ContextAlgo::affectsLastSelectedPath( name ) ||
		!boost::starts_with( name.string(), "ui:" )
	)
	{
		m_selectionDirty = true;
		selectionChangedSignal()( *this );
		m_handlesDirty = true;
		m_priorityPathsDirty = true;
	}
}

void TransformTool::plugDirtied( const Gaffer::Plug *plug )
{
	// Note : This method is called not only when plugs
	// belonging to the TransformTool are dirtied, but
	// _also_ when plugs belonging to the View are dirtied.

	if(
		plug == activePlug() ||
		plug == scenePlug()->childNamesPlug() ||
		plug == scenePlug()->transformPlug() ||
		// The `ancestor()` check protects us from accessing an
		// already-destructed View in the case that the View is
		// destroyed before the Tool.
		/// \todo It'd be good to have a more robust solution to
		/// this, perhaps with Tools being owned by Views so that
		/// the validity of `Tool::m_view` can be managed. Also
		/// see comments in `__toolPlugSet()` in Viewer.py.
		( plug->ancestor<View>() && plug == view()->editScopePlug() )
	)
	{
		m_selectionDirty = true;
		if( !m_dragging )
		{
			// See associated comment in `updateSelection()`, and
			// `dragEnd()` where we emit to complete the
			// deferral started here.
			selectionChangedSignal()( *this );
		}
		m_handlesDirty = true;
		m_priorityPathsDirty = true;
	}
	else if( plug == sizePlug() )
	{
		m_handlesDirty = true;
		view()->viewportGadget()->renderRequestSignal()(
			view()->viewportGadget()
		);
	}

	if( affectsHandles( plug ) )
	{
		m_handlesDirty = true;
	}

	if( plug == activePlug() )
	{
		if( activePlug()->getValue() )
		{
			m_preRenderConnection = view()->viewportGadget()->preRenderSignal().connect( boost::bind( &TransformTool::preRender, this ) );
		}
		else
		{
			m_preRenderConnection.disconnect();
			m_handles->setVisible( false );
			SceneGadget *sceneGadget = static_cast<SceneGadget *>( view()->viewportGadget()->getPrimaryChild() );
			sceneGadget->setPriorityPaths( IECore::PathMatcher() );
		}
	}
}

void TransformTool::metadataChanged( IECore::InternedString key )
{
	if( !MetadataAlgo::readOnlyAffectedByChange( key ) )
	{
		return;
	}

	// We could spend a little time here to figure out if the metadata
	// change definitely applies to `selection().transformPlug`, but that
	// would involve computing our selection, which might trigger a compute.
	// Our general rule is to delay all computes until `preRender()`
	// so that a hidden Viewer has no overhead, so we just assume the worst
	// for now and do a more accurate analysis in `updateHandles()`.

	if( !m_selectionDirty )
	{
		m_selectionDirty = true;
		selectionChangedSignal()( *this );
	}

	if( !m_handlesDirty )
	{
		m_handlesDirty = true;
		view()->viewportGadget()->renderRequestSignal()(
			view()->viewportGadget()
		);
	}
}

void TransformTool::updateSelection() const
{
	if( !m_selectionDirty )
	{
		return;
	}

	if( m_dragging )
	{
		// In theory, an expression or some such could change the effective
		// transform plug while we're dragging (for instance, by driving the
		// enabled status of a downstream transform using the translate value
		// we're editing). But we ignore that on the grounds that it's unlikely,
		// and also that it would be very confusing for the selection to be
		// changed mid-drag.
		return;
	}

	// Clear the selection.
	m_selection.clear();
	m_selectionDirty = false;

	// If we're not active, then there's
	// no need to do anything.
	if( !activePlug()->getValue() )
	{
		return;
	}

	// If there's no input scene, then there's no need to
	// do anything. Our `scenePlug()` receives its input
	// from the View's input, but that doesn't count.
	const ScenePlug *scene = scenePlug()->getInput<ScenePlug>();
	scene = scene ? scene->getInput<ScenePlug>() : scene;
	if( !scene )
	{
		return;
	}

	// Otherwise we need to populate our selection from
	// the scene selection.

	const PathMatcher selectedPaths = ContextAlgo::getSelectedPaths( view()->getContext() );
	if( selectedPaths.isEmpty() )
	{
		return;
	}

	ScenePlug::ScenePath lastSelectedPath = ContextAlgo::getLastSelectedPath( view()->getContext() );
	assert( selectedPaths.match( lastSelectedPath ) & IECore::PathMatcher::ExactMatch );

	for( PathMatcher::Iterator it = selectedPaths.begin(), eIt = selectedPaths.end(); it != eIt; ++it )
	{
		Selection selection( scene, *it, view()->getContext(), const_cast<EditScope *>( view()->editScope() ) );
		m_selection.push_back( selection );
		if( *it == lastSelectedPath )
		{
			lastSelectedPath = selection.path();
		}
	}

	// Multiple selected paths may have transforms originating from
	// the same node, in which case we need to remove duplicates from
	// `m_selection`. We also need to make sure that the selection for
	// `lastSelectedPath` appears last, and isn't removed by the
	// deduplication.

	// Sort by `editTarget()`, ensuring `lastSelectedPath` comes first
	// in its group (so it survives deduplication).

	std::sort(
		m_selection.begin(), m_selection.end(),
		[&lastSelectedPath]( const Selection &a, const Selection &b )
		{
			const auto ta = editTargetOrNull( a );
			const auto tb = editTargetOrNull( b );
			if( ta < tb )
			{
				return true;
			}
			else if( tb < ta )
			{
				return false;
			}
			return ( a.path() != lastSelectedPath ) < ( b.path() != lastSelectedPath );
		}
	);

	// Deduplicate by `editTarget()`, being careful to avoid removing
	// items in EditScopes where the plug hasn't been created yet.

	auto last = std::unique(
		m_selection.begin(), m_selection.end(),
		[]( const Selection &a, const Selection &b )
		{
			const auto ta = editTargetOrNull( a );
			const auto tb = editTargetOrNull( b );
			return
				ta && tb &&
				ta != a.editScope() &&
				tb != b.editScope() &&
				ta == tb
			;
		}
	);
	m_selection.erase( last, m_selection.end() );

	// Move `lastSelectedPath` to the end

	auto lastSelectedIt = std::find_if(
		m_selection.begin(), m_selection.end(),
		[&lastSelectedPath]( const Selection &x )
		{
			return x.path() == lastSelectedPath;
		}
	);

	if( lastSelectedIt != m_selection.end() )
	{
		std::swap( m_selection.back(), *lastSelectedIt );
	}
	else
	{
		// We shouldn't get here, because ContextAlgo guarantees that lastSelectedPath is
		// contained in selectedPaths, and we've preserved lastSelectedPath through our
		// uniquefication process. But we could conceivably get here if an extension has
		// edited "ui:scene:selectedPaths" directly instead of using ContextAlgo,
		// in which case we emit a warning instead of crashing.
		IECore::msg( IECore::Msg::Warning, "TransformTool::updateSelection", "Last selected path not included in selection" );
	}
}

void TransformTool::preRender()
{
	if( !m_dragging )
	{
		updateSelection();
		if( m_priorityPathsDirty )
		{
			m_priorityPathsDirty = false;
			SceneGadget *sceneGadget = static_cast<SceneGadget *>( view()->viewportGadget()->getPrimaryChild() );
			if( selection().size() )
			{
				sceneGadget->setPriorityPaths( ContextAlgo::getSelectedPaths( view()->getContext() ) );
			}
			else
			{
				sceneGadget->setPriorityPaths( IECore::PathMatcher() );
			}
		}
	}

	if( !selectionEditable() )
	{
		m_handles->setVisible( false );
		return;
	}

	m_handles->setVisible( true );

	if( m_handlesDirty )
	{
		updateHandles( sizePlug()->getValue() * 75 );
		m_handlesDirty = false;
	}
}

void TransformTool::dragBegin()
{
	m_dragging = true;
}

void TransformTool::dragEnd()
{
	m_dragging = false;
	m_mergeGroupId++;
	selectionChangedSignal()( *this );
}

std::string TransformTool::undoMergeGroup() const
{
	return boost::str( boost::format( "TransformTool%1%%2%" ) % this % m_mergeGroupId );
}

bool TransformTool::keyPress( const GafferUI::KeyEvent &event )
{
	if( !activePlug()->getValue() )
	{
		return false;
	}

	if( event.key == "S" && !event.modifiers )
	{
		if( !selectionEditable() )
		{
			return false;
		}

		UndoScope undoScope( selection().back().editTarget()->ancestor<ScriptNode>() );
		for( const auto &s : selection() )
		{
			Context::Scope contextScope( s.context() );
			const auto edit = s.acquireTransformEdit();
			for( const auto &vectorPlug : { edit->translate, edit->rotate, edit->scale, edit->pivot } )
			{
				for( const auto &plug : FloatPlug::Range( *vectorPlug ) )
				{
					if( Animation::canAnimate( plug.get() ) )
					{
						const float value = plug->getValue();
						Animation::CurvePlug* const curve = Animation::acquire( plug.get() );
						curve->insertKey( s.context()->getTime(), value );
					}
				}
			}
		}
		return true;
	}
	else if( event.key == "Plus" || event.key == "Equal" )
	{
		sizePlug()->setValue( sizePlug()->getValue() + 0.2 );
	}
	else if( event.key == "Minus" || event.key == "Underscore" )
	{
		sizePlug()->setValue( max( sizePlug()->getValue() - 0.2, 0.2 ) );
	}

	return false;
}

bool TransformTool::canSetValueOrAddKey( const Gaffer::FloatPlug *plug )
{
	if( Animation::isAnimated( plug ) )
	{
		return !MetadataAlgo::readOnly( plug->source() );
	}

	return plug->settable() && !MetadataAlgo::readOnly( plug );
}

void TransformTool::setValueOrAddKey( Gaffer::FloatPlug *plug, float time, float value )
{
	if( Animation::isAnimated( plug ) )
	{
		Animation::CurvePlug *curve = Animation::acquire( plug );
		curve->insertKey( time, value );
	}
	else
	{
		plug->setValue( value );
	}
}
