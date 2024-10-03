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

#include "GafferUI/Tool.h"
#include "GafferUI/ViewportGadget.h"

#include "Gaffer/Node.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"

#include "boost/regex.hpp"

#include <functional>
#include <unordered_map>

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Context )
IE_CORE_FORWARDDECLARE( EditScope )

} // namespace Gaffer

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( ContextTracker )
IE_CORE_FORWARDDECLARE( View )

} // namespace GafferUI

namespace GafferUIModule
{

// Forward declarations for friendship
void bindView();
Gaffer::NodePtr getPreprocessor( GafferUI::View &v );

}

namespace GafferUI
{

/// The View classes provide the content for the Viewer, which is implemented in the
/// GafferUI python module. The View presents whatever is connected into inPlug(),
/// and may provide further settings via additional plugs.
class GAFFERUI_API View : public Gaffer::Node
{

	public :

		~View() override;

		GAFFER_NODE_DECLARE_TYPE( GafferUI::View, ViewTypeId, Gaffer::Node );

		/// The contents for the view are provided by the input to this plug.
		/// The view can be switched by connecting a new input - this is how
		/// the Viewer controls what will be displayed by the view.
		template<typename T=Gaffer::Plug>
		T *inPlug();
		template<typename T=Gaffer::Plug>
		const T *inPlug() const;

		/// Returns the ScriptNode this view was created for.
		Gaffer::ScriptNode *scriptNode();
		const Gaffer::ScriptNode *scriptNode() const;

		/// The current EditScope for the view is specified by connecting
		/// an `EditScope::outPlug()` into this plug.
		Gaffer::Plug *editScopePlug();
		const Gaffer::Plug *editScopePlug() const;
		/// The `editScope()` method is a convenience that returns the connected
		/// EditScope node, or null if nothing is connected.
		Gaffer::EditScope *editScope();
		const Gaffer::EditScope *editScope() const;

		/// The Context in which the View should operate.
		const Gaffer::Context *context() const;
		/// Signal emitted when the result of `context()` has changed.
		UnarySignal &contextChangedSignal();

		/// Subclasses are responsible for presenting their content in this viewport.
		ViewportGadget *viewportGadget();
		const ViewportGadget *viewportGadget() const;

		/// All Tools connected to this View. Use `Tool::registeredTools()` to
		/// query the available tools and `Tool::create()` to add a tool.
		ToolContainer *tools();
		const ToolContainer *tools() const;

		class DisplayTransform;

		/// @name Factory
		///////////////////////////////////////////////////////////////////
		//@{
		/// Creates a View for the specified plug.
		static ViewPtr create( Gaffer::PlugPtr input );
		using ViewCreator = std::function<ViewPtr ( Gaffer::ScriptNodePtr )>;
		/// Registers a function which will return a View instance for a
		/// plug of a specific type.
		static void registerView( IECore::TypeId plugType, ViewCreator creator );
		/// Registers a function which returns a View instance for plugs with specific names
		/// on nodes of a specific type. Views registered in this manner take precedence over
		/// those registered by plug type only.
		static void registerView( const IECore::TypeId nodeType, const std::string &plugPathRegex, ViewCreator creator );
		//@}

	protected :

		/// The input plug is added to the View to form inPlug() - the derived
		/// class should construct a plug of a suitable type and pass it
		/// to the View constructor. For instance, the SceneView will pass
		/// a ScenePlug so that only scenes may be viewed.
		View( const std::string &name, Gaffer::ScriptNodePtr scriptNode, Gaffer::PlugPtr input );

		/// The View may want to perform preprocessing of the input before
		/// displaying it, for instance by applying a LUT to an image. This
		/// can be achieved by setting a preprocess node which is connected
		/// internally to the view. A preprocessor must have an "in" plug
		/// which will get it's input from inPlug(), and an "out" plug
		/// which will be returned by preprocessedInPlug().
		/// \todo Having just one preprocessor is pretty limiting. If we
		/// allowed chains of preprocessors, and made the API public, then
		/// we could make Views in a more modular manner, adding components
		/// (each with their own preprocessors) to build up the view.
		void setPreprocessor( Gaffer::NodePtr preprocessor );
		/// Returns the node used for preprocessing, or 0 if no such
		/// node has been specified (or if it is not of type T).
		template<typename T=Gaffer::Node>
		T *getPreprocessor();
		template<typename T=Gaffer::Node>
		const T *getPreprocessor() const;
		/// Returns the "out" plug of the preprocessor, or inPlug() if
		/// no preprocessor has been specified. This is the plug which
		/// should be used when computing the contents to display.
		template<typename T=Gaffer::Plug>
		T *preprocessedInPlug();

		template<class T>
		struct ViewDescription
		{
			ViewDescription( IECore::TypeId plugType );
			ViewDescription( IECore::TypeId nodeType, const std::string &plugPathRegex );
		};

		bool acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const override;

	private :

		void contextTrackerChanged();
		void toolsChildAdded( Gaffer::GraphComponent *child );
		void toolPlugSet( Gaffer::Plug *plug );

		const Gaffer::ScriptNodePtr m_scriptNode;

		using ToolPlugSetMap = std::unordered_map<Tool *, Gaffer::Signals::ScopedConnection>;
		ToolPlugSetMap m_toolPlugSetConnections;

		ViewportGadgetPtr m_viewportGadget;
		ContextTrackerPtr m_contextTracker;
		Gaffer::ConstContextPtr m_context;
		UnarySignal m_contextChangedSignal;

		using CreatorMap = std::map<IECore::TypeId, ViewCreator>;
		static CreatorMap &creators();

		using RegexAndCreator = std::pair<boost::regex, ViewCreator>;
		using RegexAndCreatorVector = std::vector<RegexAndCreator>;
		using NamedCreatorMap = std::map<IECore::TypeId, RegexAndCreatorVector>;
		static NamedCreatorMap &namedCreators();

		static size_t g_firstPlugIndex;

		friend void GafferUIModule::bindView();
		friend Gaffer::NodePtr GafferUIModule::getPreprocessor( View & );

};

/// Optional component that can be added to any view, adding plugs to manage
/// a display transform applied to `Layer::Main`.
class GAFFERUI_API View::DisplayTransform : public Gaffer::Node
{

	public :

		/// The new DisplayTransform will be owned by `view`.
		DisplayTransform( View *view );
		~DisplayTransform() override;

		GAFFER_NODE_DECLARE_TYPE( GafferUI::View::DisplayTransform, ViewDisplayTransformTypeId, Gaffer::Node );

		/// Function that returns an OpenGL shader that applies a display
		/// transform. In addition to the shader parameters required by `ViewportGadget::setPostProcessShader()`,
		/// the shader should also have the following parameters :
		///
		/// - `bool absoluteValue` : Flips negative values to positive (useful when viewing a difference value).
		/// - `bool clipping` : Marks regions outside `0 - 1`.
		/// - `color multiply` : Applies a multiplier before the color transform.
		/// - `float power` : Applies `pow( c, power )` _after_ the color transform.
		/// - `int soloChannel` : Set to 0-3 to pick channels RGBA, or -2 for luminance.
		///   Default -1 uses all channels as a color.
		using DisplayTransformCreator = std::function<IECoreGL::Shader::SetupPtr ()>;

		static void registerDisplayTransform( const std::string &name, DisplayTransformCreator creator );
		static void deregisterDisplayTransform( const std::string &name );
		static std::vector<std::string> registeredDisplayTransforms();

	private :

		View *view();
		Gaffer::StringPlug *namePlug();
		Gaffer::IntPlug *soloChannelPlug();
		Gaffer::BoolPlug *clippingPlug();
		Gaffer::FloatPlug *exposurePlug();
		Gaffer::FloatPlug *gammaPlug();
		Gaffer::BoolPlug *absolutePlug();

		void contextChanged();
		void registrationChanged( const std::string &name );
		void plugDirtied( const Gaffer::Plug *plug );
		void preRender();
		bool keyPress( const KeyEvent &event );

		IECoreGL::Shader::SetupPtr m_shader;
		IECore::MurmurHash m_shaderContextHash;
		bool m_shaderDirty;
		bool m_parametersDirty;

		static size_t g_firstPlugIndex;

};

} // namespace GafferUI

#include "GafferUI/View.inl"
