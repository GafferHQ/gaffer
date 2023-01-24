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

#include "GafferUI/View.h"

#include "Gaffer/Context.h"
#include "Gaffer/EditScope.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/Plug.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/StringPlug.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind/bind.hpp"

using namespace boost::placeholders;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

bool exclusive( const Tool *tool )
{
	auto d = Metadata::value<BoolData>( tool, "tool:exclusive" );
	return !d || d->readable();
}

const InternedString g_editScopeName( "editScope" );
const InternedString g_toolsName( "tools" );

} // namespace

//////////////////////////////////////////////////////////////////////////
// View
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( View );

size_t View::g_firstPlugIndex = 0;

View::View( const std::string &name, Gaffer::PlugPtr inPlug )
	:	Node( name ),
		m_viewportGadget( new ViewportGadget )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	setChild( "in", inPlug );
	addChild( new Plug( g_editScopeName ) );
	addChild( new ToolContainer( g_toolsName ) );
	setContext( new Context() );

	tools()->childAddedSignal().connect( boost::bind( &View::toolsChildAdded, this, ::_2 ) );
}

View::~View()
{
	// Clear tools. This causes any connections from plugs on the View to plugs
	// on the Tool to be removed now, while `Tool::view()` is still valid. This
	// avoids exceptions that would otherwise be caused by Tools responding to
	// `plugDirtiedSignal()` _after_ they've been removed from the View.
	tools()->clearChildren();
}

Gaffer::Plug *View::editScopePlug()
{
	/// \todo Fix ImageView so it doesn't reorder plugs, and then
	/// perform lookups with indices rather than names. See comment
	/// in `ImageView::insertConverter()`.
	return getChild<Plug>( g_editScopeName );
}

const Gaffer::Plug *View::editScopePlug() const
{
	return getChild<Plug>( g_editScopeName );
}

ToolContainer *View::tools()
{
	return getChild<ToolContainer>( g_toolsName );
}

const ToolContainer *View::tools() const
{
	return getChild<ToolContainer>( g_toolsName );
}

Gaffer::EditScope *View::editScope()
{
	Plug *p = editScopePlug()->getInput();
	return p ? p->parent<EditScope>() : nullptr;
}

const Gaffer::EditScope *View::editScope() const
{
	const Plug *p = editScopePlug()->getInput();
	return p ? p->parent<EditScope>() : nullptr;
}

Gaffer::Context *View::getContext()
{
	return m_context.get();
}

const Gaffer::Context *View::getContext() const
{
	return m_context.get();
}

void View::setContext( Gaffer::ContextPtr context )
{
	if( context == m_context )
	{
		return;
	}
	m_context = context;
	m_contextChangedConnection = m_context->changedSignal().connect( boost::bind( &View::contextChanged, this, ::_2 ) );
	contextChangedSignal()( this );
}

View::UnarySignal &View::contextChangedSignal()
{
	return m_contextChangedSignal;
}

ViewportGadget *View::viewportGadget()
{
	return m_viewportGadget.get();
}

const ViewportGadget *View::viewportGadget() const
{
	return m_viewportGadget.get();
}

void View::setPreprocessor( Gaffer::NodePtr preprocessor )
{
	setChild( "__preprocessor", preprocessor );
	preprocessor->getChild<Plug>( "in" )->setInput( inPlug() );
}

void View::contextChanged( const IECore::InternedString &name )
{
}

Signals::Connection &View::contextChangedConnection()
{
	return m_contextChangedConnection;
}

View::CreatorMap &View::creators()
{
	static CreatorMap m;
	return m;
}

View::NamedCreatorMap &View::namedCreators()
{
	static NamedCreatorMap m;
	return m;
}

ViewPtr View::create( Gaffer::PlugPtr plug )
{
	const Gaffer::Node *node = plug->node();
	if( node )
	{
		std::string plugPath = plug->relativeName( node );
		const NamedCreatorMap &m = namedCreators();
		IECore::TypeId t = node->typeId();
		while( t!=IECore::InvalidTypeId )
		{
			NamedCreatorMap::const_iterator it = m.find( t );
			if( it!=m.end() )
			{
				for( RegexAndCreatorVector::const_reverse_iterator nIt = it->second.rbegin(); nIt!=it->second.rend(); nIt++ )
				{
					if( boost::regex_match( plugPath, nIt->first ) )
					{
						return nIt->second( plug );
					}
				}
			}
			t = IECore::RunTimeTyped::baseTypeId( t );
		}
	}

	CreatorMap &m = creators();
	IECore::TypeId t = plug->typeId();
	while( t!=IECore::InvalidTypeId )
	{
		CreatorMap::const_iterator it = m.find( t );
		if( it!=m.end() )
		{
			return it->second( plug );
		}
		t = IECore::RunTimeTyped::baseTypeId( t );
	}

	return nullptr;
}

void View::registerView( IECore::TypeId plugType, ViewCreator creator )
{
	creators()[plugType] = creator;
}

void View::registerView( const IECore::TypeId nodeType, const std::string &plugPath, ViewCreator creator )
{
	namedCreators()[nodeType].push_back( RegexAndCreator( boost::regex( plugPath ), creator ) );
}

void View::toolsChildAdded( Gaffer::GraphComponent *child ) const
{
	auto tool = static_cast<Tool *>( child ); // Type guaranteed by `ToolContainer::acceptsChild()`
	tool->plugSetSignal().connect( boost::bind( &View::toolPlugSet, this, ::_1 ) );
}

void View::toolPlugSet( Gaffer::Plug *plug ) const
{
	auto tool = plug->ancestor<Tool>();
	if( plug != tool->activePlug() )
	{
		return;
	}

	if( !tool->activePlug()->getValue() || !exclusive( tool ) )
	{
		return;
	}

	for( auto &t : Tool::Range( *tools() ) )
	{
		if( t != tool && exclusive( t.get() ) )
		{
			t->activePlug()->setValue( false );
		}
	}
}

//////////////////////////////////////////////////////////////////////////
// DisplayTransform
//////////////////////////////////////////////////////////////////////////

namespace
{

using DisplayTransformCreatorMap = std::map<std::string, View::DisplayTransform::DisplayTransformCreator>;

DisplayTransformCreatorMap &displayTransformCreators()
{
	// Deliberately "leaking" map, as it may contain Python functors which
	// cannot be destroyed during program exit (because Python will have been
	// shut down first).
	static auto g_creators = new DisplayTransformCreatorMap;
	return *g_creators;
}

using RegistrationChangedSignal = Gaffer::Signals::Signal<void ( const std::string & )>;

RegistrationChangedSignal &registrationChangedSignal()
{
	static RegistrationChangedSignal g_signal;
	return g_signal;
}

const IECore::InternedString g_frame( "frame" );

} // namespace

size_t View::DisplayTransform::g_firstPlugIndex = 0;

View::DisplayTransform::DisplayTransform( View *view )
	:	m_shaderDirty( true ), m_parametersDirty( true )
{
	// Our settings are represented as plugs parented to us.

	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new Gaffer::StringPlug( "name" ) );
	addChild(
		new IntPlug(
			"soloChannel",
			Plug::In,
			/* defaultValue = */ -1,
			/* minValue = */ -2,
			/* maxValue = */ 3
		)
	);
	addChild( new BoolPlug( "clipping" ) );
	addChild( new FloatPlug( "exposure", Plug::In, 0.0f ) );
	addChild( new FloatPlug( "gamma", Plug::In, 1.0f, /* minValue = */ 0.0f ) );
	addChild( new BoolPlug( "absolute" ) );

	// The plugs are promoted on to the View so that they are
	// exposed to users.

	view->setChild( "__displayTransform", this );

	PlugPtr promoted = new Plug();
	view->setChild( "displayTransform", promoted );

	for( size_t i = g_firstPlugIndex; i < children().size(); ++i )
	{
		PlugAlgo::promote( getChild<Plug>( i ), promoted.get() );
	}

	// Connections needed to update the viewport shader.

	registrationChangedSignal().connect(
		boost::bind( &DisplayTransform::registrationChanged, this, ::_1 )
	);

	plugDirtiedSignal().connect(
		boost::bind( &DisplayTransform::plugDirtied, this, ::_1 )
	);

	view->viewportGadget()->preRenderSignal().connect(
		boost::bind( &DisplayTransform::preRender, this )
	);

	view->viewportGadget()->keyPressSignal().connect(
		boost::bind( &DisplayTransform::keyPress, this, ::_2 )
	);

	view->contextChangedSignal().connect(
		boost::bind( &DisplayTransform::connectToViewContext, this )
	);
	connectToViewContext();

}

View::DisplayTransform::DisplayTransform::~DisplayTransform()
{
}

View *View::DisplayTransform::view()
{
	return parent<View>();
}

Gaffer::StringPlug *View::DisplayTransform::namePlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *View::DisplayTransform::soloChannelPlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *View::DisplayTransform::clippingPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 2 );
}

Gaffer::FloatPlug *View::DisplayTransform::exposurePlug()
{
	return getChild<Gaffer::FloatPlug>( g_firstPlugIndex + 3 );
}

Gaffer::FloatPlug *View::DisplayTransform::gammaPlug()
{
	return getChild<Gaffer::FloatPlug>( g_firstPlugIndex + 4 );
}

Gaffer::BoolPlug *View::DisplayTransform::absolutePlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 5 );
}

void View::DisplayTransform::connectToViewContext()
{
	m_contextChangedConnection = view()->getContext()->changedSignal().connect( boost::bind( &View::DisplayTransform::contextChanged, this, ::_2 ) );
}

void View::DisplayTransform::contextChanged( const IECore::InternedString &name )
{
	// DisplayTransformCreators may be context-sensitive, so we need to
	// call them again. But we can at least avoid the overhead for common
	// changes which shouldn't affect them.
	if( name != g_frame && !boost::starts_with( name.string(), "ui:" ) )
	{
		m_shaderDirty = true;
		view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
	}
}

void View::DisplayTransform::registrationChanged( const std::string &name )
{
	if( name == namePlug()->getValue() )
	{
		m_shaderDirty = true;
		view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
	}
}

void View::DisplayTransform::plugDirtied( const Gaffer::Plug *plug )
{
	if( plug == namePlug() )
	{
		m_shaderDirty = true;
		view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
	}
	else if(
		plug == soloChannelPlug() ||
		plug == clippingPlug() ||
		plug == exposurePlug() ||
		plug == gammaPlug() ||
		plug == absolutePlug()
	)
	{
		m_parametersDirty = true;
		view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
	}
}

void View::DisplayTransform::preRender()
{
	if( m_shaderDirty )
	{
		m_shader = nullptr;
		const std::string name = namePlug()->getValue();
		if( !name.empty() )
		{
			auto it = displayTransformCreators().find( name );
			if( it != displayTransformCreators().end() )
			{
				Context::Scope scope( view()->getContext() );
				m_shader = it->second();
			}
			else
			{
				IECore::msg(
					IECore::Msg::Warning, "View::DisplayTransform",
					boost::format( "Transform \"%1%\" not registered" ) % name
				);
			}
		}

		view()->viewportGadget()->setPostProcessShader( Gadget::Layer::Main, m_shader );
		m_shaderDirty = false;
		m_parametersDirty = true;
	}

	if( m_shader && m_parametersDirty )
	{
		m_shader->addUniformParameter( "clipping", new BoolData( clippingPlug()->getValue() ) );
		const float m = pow( 2.0f, exposurePlug()->getValue() );
		m_shader->addUniformParameter( "multiply", new Color3fData( Imath::Color3f( m ) ) );
		const float gamma = gammaPlug()->getValue();
		const float p = gamma > 0.0 ? 1.0f / gamma : 1.0f;
		m_shader->addUniformParameter( "power", new Color3fData( Imath::Color3f( p ) ) );
		m_shader->addUniformParameter( "soloChannel", new IntData( soloChannelPlug()->getValue() ) );
		m_shader->addUniformParameter( "absoluteValue", new BoolData( absolutePlug()->getValue() ) );
		m_parametersDirty = false;
	}
}

bool View::DisplayTransform::keyPress( const KeyEvent &event )
{
	ConstBoolDataPtr soloChannelShortCuts = Gaffer::Metadata::value<BoolData>(
		soloChannelPlug()->source(), "view:displayTransform:useShortcuts"
	);

	if( !event.modifiers && ( !soloChannelShortCuts || soloChannelShortCuts->readable() ) )
	{
		const char *rgbal[5] = { "R", "G", "B", "A", "L" };
		for( int i = 0; i < 5; ++i )
		{
			if( event.key == rgbal[i] )
			{
				int soloChannel = i < 4 ? i : -2;
				soloChannelPlug()->source<IntPlug>()->setValue(
					soloChannelPlug()->getValue() == soloChannel ? -1 : soloChannel
				);
				return true;
			}
		}
	}

	return false;
}

void View::DisplayTransform::registerDisplayTransform( const std::string &name, DisplayTransformCreator creator )
{
	displayTransformCreators()[name] = creator;
	registrationChangedSignal()( name );
}

std::vector<std::string> View::DisplayTransform::registeredDisplayTransforms()
{
	std::vector<std::string> result;
	for( auto &d : displayTransformCreators() )
	{
		result.push_back( d.first );
	}
	return result;
}
