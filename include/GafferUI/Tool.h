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

#ifndef GAFFERUI_TOOL_H
#define GAFFERUI_TOOL_H

#include "Gaffer/Node.h"

#include "GafferUI/TypeIds.h"

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( Tool )
IE_CORE_FORWARDDECLARE( View )

class Tool : public Gaffer::Node
{

	public :

		virtual ~Tool();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::Tool, ToolTypeId, Gaffer::Node );

		/// Plug to define whether or not this tool
		/// is currently active.
		Gaffer::BoolPlug *activePlug();
		const Gaffer::BoolPlug *activePlug() const;

		/// @name Factory
		///////////////////////////////////////////////////////////////////
		//@{
		/// Creates a Tool for the specified View.
		static ToolPtr create( const std::string &toolName, View *view );
		typedef boost::function<ToolPtr ( View * )> ToolCreator;
		/// Registers a function which will return a Tool instance for a
		/// view of a specific type.
		static void registerTool( const std::string &toolName, IECore::TypeId viewType, ToolCreator creator );
		/// Fills toolNames with the names of all tools registered for the view type.
		static void registeredTools( IECore::TypeId viewType, std::vector<std::string> &toolNames );
		//@}

	protected :

		Tool( View *view, const std::string &name = defaultName<Tool>() );

		View *view();
		const View *view() const;

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

	private :

		View *m_view;

		static size_t g_firstPlugIndex;

};

} // namespace GafferUI

#endif // GAFFERUI_TOOL_H
