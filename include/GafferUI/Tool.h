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

#pragma once

#include "GafferUI/Export.h"
#include "GafferUI/TypeIds.h"

#include "Gaffer/Container.h"
#include "Gaffer/Node.h"
#include "Gaffer/TypedPlug.h"

#include <functional>

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( Tool )
IE_CORE_FORWARDDECLARE( View )

/// Base class for adding interactive functionality to Views.
/// Typically this will be used to create manipulators to modify
/// settings on the node graph being viewed, or to provide
/// additional overlays in the View.
///
/// Tool is derived from Node so that plugs may be added to
/// provide tool settings the user can change. The base class
/// itself has a single plug to determine whether or not the
/// tool is currently active - this should be honoured by all
/// implementations.
///
/// Typically a tool implementation will add Gadgets to the
/// viewport for the View it is constructed with, and connect
/// to signals on the Gadgets to provide the interactive
/// functionality desired. The Tool may also need to modify
/// the Gadgets when the input to the View is dirtied, for instance
/// to reflect the new position of an object being manipulated.
/// It is recommended that such updates are performed via
/// ViewportGadget::preRenderSignal(), so that they are
/// performed lazily only when needed.
class GAFFERUI_API Tool : public Gaffer::Node
{

	public :

		explicit Tool( View *view, const std::string &name = defaultName<Tool>() );
		~Tool() override;

		GAFFER_NODE_DECLARE_TYPE( GafferUI::Tool, ToolTypeId, Gaffer::Node );

		View *view();
		const View *view() const;

		/// Plug to define whether or not this tool
		/// is currently active.
		Gaffer::BoolPlug *activePlug();
		const Gaffer::BoolPlug *activePlug() const;

		/// The Tool constructor automatically parents the tool to
		/// the`View::toolsContainer()`. After that, the tool may not be
		/// reparented.
		bool acceptsParent( const GraphComponent *potentialParent ) const override;

		/// @name Factory
		///////////////////////////////////////////////////////////////////
		//@{
		/// Creates a Tool for the specified View.
		static ToolPtr create( const std::string &toolName, View *view );
		using ToolCreator = std::function<ToolPtr ( View * )>;
		/// Registers a function which will return a Tool instance for a
		/// view of a specific type.
		static void registerTool( const std::string &toolName, IECore::TypeId viewType, ToolCreator creator );
		/// Fills toolNames with the names of all tools registered for the view type.
		static void registeredTools( IECore::TypeId viewType, std::vector<std::string> &toolNames );
		//@}

	protected :

		template<typename ToolType, typename ViewType>
		struct ToolDescription
		{
			ToolDescription()
			{
				registerTool( ToolType::staticTypeName(), ViewType::staticTypeId(), creator );
			}

			static ToolPtr creator( View *view )
			{
				ViewType *typedView = IECore::runTimeCast<ViewType>( view );
				if( !typedView )
				{
					throw IECore::Exception( "View has incorrect type" );
				}
				return new ToolType( typedView );
			}
		};

		void parentChanged( GraphComponent *oldParent ) override;

	private :

		static size_t g_firstPlugIndex;

};

using ToolContainer = Gaffer::Container<Gaffer::Node, Tool>;
IE_CORE_DECLAREPTR( ToolContainer );

} // namespace GafferUI
