//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012-2013, John Haddon. All rights reserved.
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

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"
#include "boost/tokenizer.hpp"

#include "IECore/ParameterisedProcedural.h"
#include "IECore/VectorTypedData.h"

#include "Gaffer/Context.h"
#include "Gaffer/BlockedConnection.h"

#include "GafferScene/SceneProcedural.h"
#include "GafferScene/PathMatcherData.h"
#include "GafferScene/StandardOptions.h"

#include "GafferSceneUI/SceneView.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// Implementation of a ParameterisedProcedural wrapping a SceneProcedural.
// We need this to allow us to use the RenderableGadget for doing our
// display.
/// \todo Build our own scene representation.
//////////////////////////////////////////////////////////////////////////

class WrappingProcedural : public IECore::ParameterisedProcedural
{

	public :

		WrappingProcedural( SceneProceduralPtr sceneProcedural )
			:	ParameterisedProcedural( "" ), m_sceneProcedural( sceneProcedural )
		{
		}

	protected :
	
		virtual Imath::Box3f doBound( ConstCompoundObjectPtr args ) const
		{
			return m_sceneProcedural->bound();
		}

		virtual void doRender( RendererPtr renderer, ConstCompoundObjectPtr args ) const
		{
			m_sceneProcedural->render( renderer );
		}

	private :
	
		SceneProceduralPtr m_sceneProcedural;

};

IE_CORE_DECLAREPTR( WrappingProcedural );

//////////////////////////////////////////////////////////////////////////
// SceneView implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( SceneView );

SceneView::ViewDescription<SceneView> SceneView::g_viewDescription( GafferScene::ScenePlug::staticTypeId() );

SceneView::SceneView()
	:	View3D( defaultName<SceneView>(), new GafferScene::ScenePlug() ),
		m_renderableGadget( new RenderableGadget )
{
	viewportGadget()->setChild( m_renderableGadget );

	m_selectionChangedConnection = m_renderableGadget->selectionChangedSignal().connect( boost::bind( &SceneView::selectionChanged, this, ::_1 ) );
	viewportGadget()->keyPressSignal().connect( boost::bind( &SceneView::keyPress, this, ::_1, ::_2 ) );
	
	// add a preprocessor which removes motion blur, because the opengl
	// renderer doesn't support it.
	
	StandardOptionsPtr standardOptions = new StandardOptions();
	standardOptions->optionsPlug()->getChild<CompoundPlug>( "transformBlur" )->getChild<BoolPlug>( "enabled" )->setValue( true );
	standardOptions->optionsPlug()->getChild<CompoundPlug>( "transformBlur" )->getChild<BoolPlug>( "value" )->setValue( false );
	standardOptions->optionsPlug()->getChild<CompoundPlug>( "deformationBlur" )->getChild<BoolPlug>( "enabled" )->setValue( true );
	standardOptions->optionsPlug()->getChild<CompoundPlug>( "deformationBlur" )->getChild<BoolPlug>( "value" )->setValue( false );
	
	setPreprocessor( standardOptions );
}

SceneView::~SceneView()
{
}

void SceneView::contextChanged( const IECore::InternedString &name )
{
	if( name.value() == "ui:scene:selectedPaths" )
	{
		// if only the selection has changed then we can just update the selection
		// on our existing scene representation.
		const StringVectorData *sc = getContext()->get<StringVectorData>( "ui:scene:selectedPaths" );
		RenderableGadget::Selection sr;
		sr.insert( sc->readable().begin(), sc->readable().end() );

		BlockedConnection blockedConnection( m_selectionChangedConnection );
		m_renderableGadget->setSelection( sr );
		return;
	}
	
	if(
		name.value().compare( 0, 3, "ui:" ) == 0 &&
		name.value() != "ui:scene:expandedPaths"
	)
	{
		// if it's just a ui context entry that has changed, and it doesn't
		// affect our expansion, then early out.
		return;
	}
	
	// the context change might affect the scene itself, so we must
	// schedule an update.
	updateRequestSignal()( this );
}

void SceneView::update()
{
	SceneProceduralPtr p = new SceneProcedural( preprocessedInPlug<ScenePlug>(), getContext(), ScenePlug::ScenePath(), expandedPaths() );
	WrappingProceduralPtr wp = new WrappingProcedural( p );
	
	bool hadRenderable = m_renderableGadget->getRenderable();
	m_renderableGadget->setRenderable( wp );
	if( !hadRenderable )
	{
		viewportGadget()->frame( m_renderableGadget->bound() );
	}
}

Imath::Box3f SceneView::framingBound() const
{
	Imath::Box3f b = m_renderableGadget->selectionBound();
	if( !b.isEmpty() )
	{
		return b;
	}
	return View3D::framingBound();
}

void SceneView::selectionChanged( GafferUI::RenderableGadgetPtr renderableGadget )
{
	BlockedConnection blockedConnection( contextChangedConnection() );
	transferSelectionToContext();
}

bool SceneView::keyPress( GafferUI::GadgetPtr gadget, const GafferUI::KeyEvent &event )
{
	if( event.key == "Down" )
	{
		expandSelection();
		return true;
	}
	else if( event.key == "Up" )
	{
		collapseSelection();	
		return true;
	}
	
	return false;
}

void SceneView::expandSelection()
{
	RenderableGadget::Selection &selection = m_renderableGadget->getSelection();
	
	vector<string> pathsToSelect;
	vector<const string *> pathsToDeselect;
	IECore::PathMatcherData *expandedData = expandedPaths();
	PathMatcher &expanded = expandedData->writable();
	
	bool needUpdate = false;
	for( RenderableGadget::Selection::const_iterator it = selection.begin(), eIt = selection.end(); it != eIt; it++ )
	{
		if( expanded.addPath( *it ) )
		{
			needUpdate = true;
			
			/// \todo Maybe if RenderableGadget used PathMatcher for specifying selection, and
			/// we had a nice means of getting ScenePaths out of PathMatcher, we wouldn't need
			/// to do all this string manipulation.
			typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;
			Tokenizer pathTokenizer( *it, boost::char_separator<char>( "/" ) );	
			ScenePlug::ScenePath path;
			for( Tokenizer::const_iterator pIt = pathTokenizer.begin(), pEIt = pathTokenizer.end(); pIt != pEIt; pIt++ )
			{
				path.push_back( *pIt );
			}
			
			ConstInternedStringVectorDataPtr childNamesData = preprocessedInPlug<ScenePlug>()->childNames( path );
			const vector<InternedString> &childNames = childNamesData->readable();
			if( childNames.size() )
			{
				pathsToDeselect.push_back( &(*it) );
				for( vector<InternedString>::const_iterator cIt = childNames.begin(), ceIt = childNames.end(); cIt != ceIt; cIt++ )
				{
					if( *(*it).rbegin() != '/' )
					{
						pathsToSelect.push_back( *it + "/" + cIt->string() );
					}
					else
					{
						pathsToSelect.push_back( *it + cIt->string() );
					}
				}
			}
		}
	}
	
	for( vector<string>::const_iterator it = pathsToSelect.begin(), eIt = pathsToSelect.end(); it != eIt; it++ )
	{
		selection.insert( *it );
	}
	for( vector<const string *>::const_iterator it = pathsToDeselect.begin(), eIt = pathsToDeselect.end(); it != eIt; it++ )
	{
		selection.erase( **it );
	}
	
	if( needUpdate )
	{
		// we were naughty and modified the expanded paths in place (to avoid
		// unecessary copying), so the context doesn't know they've changed.
		// so we emit the changed signal ourselves. this will then trigger update()
		// via contextChanged().
		getContext()->changedSignal()( getContext(), "ui:scene:expandedPaths" );
		// and this will trigger a selection update also via contextChanged().
		transferSelectionToContext();
	}
}

void SceneView::collapseSelection()
{
	RenderableGadget::Selection &selection = m_renderableGadget->getSelection();
	if( !selection.size() )
	{
		return;
	}
	
	set<string> pathsToSelect;
	vector<const string *> pathsToDeselect;
	IECore::PathMatcherData *expandedData = expandedPaths();
	PathMatcher &expanded = expandedData->writable();
	
	for( RenderableGadget::Selection::const_iterator it = selection.begin(), eIt = selection.end(); it != eIt; it++ )
	{
		if( !expanded.removePath( *it ) )
		{
			if( *it == "/" )
			{
				continue;
			}
			pathsToDeselect.push_back( &(*it) );
			std::string parentPath( *it, 0, it->rfind( '/' ) );
			if( parentPath == "" )
			{
				parentPath = "/";
			}
			expanded.removePath( parentPath );
			pathsToSelect.insert( parentPath );
		}
	}
	
	for( set<string>::const_iterator it = pathsToSelect.begin(), eIt = pathsToSelect.end(); it != eIt; it++ )
	{
		selection.insert( *it );
	}
	for( vector<const string *>::const_iterator it = pathsToDeselect.begin(), eIt = pathsToDeselect.end(); it != eIt; it++ )
	{
		selection.erase( **it );
	}

	// see comment in expandSelection().
	getContext()->changedSignal()( getContext(), "ui:scene:expandedPaths" );
	// and this will trigger a selection update also via contextChanged().
	transferSelectionToContext();
}

void SceneView::transferSelectionToContext()
{
	/// \todo If RenderableGadget used PathMatcherData, then we might not need
	/// to copy data here.
	const RenderableGadget::Selection &selection = m_renderableGadget->getSelection();
	StringVectorDataPtr s = new StringVectorData();
	s->writable().insert( s->writable().end(), selection.begin(), selection.end() );
	getContext()->set( "ui:scene:selectedPaths", s.get() );
}

IECore::PathMatcherData *SceneView::expandedPaths()
{
	const IECore::PathMatcherData *m = getContext()->get<IECore::PathMatcherData>( "ui:scene:expandedPaths", 0 );
	if( !m )
	{
		PathMatcherDataPtr rootOnly = new IECore::PathMatcherData;
		rootOnly->writable().addPath( "/" );
		BlockedConnection blockedConnection( contextChangedConnection() );
		getContext()->set( "ui:scene:expandedPaths", rootOnly.get() );
		m = getContext()->get<IECore::PathMatcherData>( "ui:scene:expandedPaths", 0 );
	}
	return const_cast<IECore::PathMatcherData *>( m );
}
