//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/UndoContext.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"

#include "GafferUI/Nodule.h"
#include "GafferUI/PlugAdder.h"

#include "GafferScene/Shader.h"

#include "GafferSceneUI/Private/ShaderNodeGadget.h"

using namespace std;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI::Private;

//////////////////////////////////////////////////////////////////////////
// ShaderPlugAdder
//////////////////////////////////////////////////////////////////////////

namespace
{

IECore::InternedString g_visibleKey( "noduleLayout:visible" );
IECore::InternedString g_noduleTypeKey( "nodule:type" );

class ShaderPlugAdder : public PlugAdder
{

	public :

		ShaderPlugAdder( ShaderPtr shader, StandardNodeGadget::Edge edge )
			: PlugAdder( edge ), m_shader( shader )
		{
			shader->parametersPlug()->childAddedSignal().connect( boost::bind( &ShaderPlugAdder::childAdded, this ) );
			shader->parametersPlug()->childRemovedSignal().connect( boost::bind( &ShaderPlugAdder::childRemoved, this ) );
			Metadata::plugValueChangedSignal().connect( boost::bind( &ShaderPlugAdder::plugMetadataChanged, this, ::_1, ::_2, ::_3, ::_4 ) );

			buttonReleaseSignal().connect( boost::bind( &ShaderPlugAdder::buttonRelease, this, ::_2 ) );

			updateVisibility();
		}

	protected :

		bool acceptsPlug( const Plug *plug ) const
		{
			vector<Plug *> plugs = showablePlugs( plug );
			return !plugs.empty();
		}

		void addPlug( Plug *connectionEndPoint )
		{
			vector<Plug *> plugs = showablePlugs( connectionEndPoint );
			Plug *plug = plugMenuSignal()( "Connect To", plugs );
			if( !plug )
			{
				return;
			}

			UndoContext undoContext( m_shader->scriptNode() );

			Metadata::registerValue( plug, g_visibleKey, new IECore::BoolData( true ) );
			plug->setInput( connectionEndPoint );
		}

	private :

		bool buttonRelease( const ButtonEvent &event )
		{
			vector<Plug *> plugs = showablePlugs();
			Plug *plug = plugMenuSignal()( "Show Parameter", plugs );
			if( !plug )
			{
				return false;
			}

			UndoContext undoContext( m_shader->scriptNode() );
			Metadata::registerValue( plug, g_visibleKey, new IECore::BoolData( true ) );
			return true;
		}

		vector<Plug *> showablePlugs( const Plug *input = NULL ) const
		{
			vector<Plug *> result;

			for( PlugIterator it( m_shader->parametersPlug() ); !it.done(); ++it )
			{
				Plug *plug = it->get();
				if( !plug->getFlags( Plug::AcceptsInputs ) )
				{
					continue;
				}
				if( input && !plug->acceptsInput( input ) )
				{
					continue;
				}
				if( IECore::ConstStringDataPtr noduleType = Metadata::value<IECore::StringData>( plug, g_noduleTypeKey ) )
				{
					if( noduleType->readable() == "" )
					{
						continue;
					}
				}
				IECore::ConstBoolDataPtr visible = Metadata::value<IECore::BoolData>( plug, g_visibleKey );
				if( !visible || visible->readable() )
				{
					continue;
				}
				if( readOnly( plug ) )
				{
					continue;
				}
				result.push_back( it->get() );
			}

			return result;
		}

		void updateVisibility()
		{
			setVisible( !showablePlugs().empty() );
		}

		void childAdded()
		{
			updateVisibility();
		}

		void childRemoved()
		{
			updateVisibility();
		}

		void plugMetadataChanged( IECore::TypeId nodeTypeId, const Gaffer::MatchPattern &plugPath, IECore::InternedString key, const Gaffer::Plug *plug )
		{
			if( childAffectedByChange( m_shader->parametersPlug(), nodeTypeId, plugPath, plug ) )
			{
				if( key == g_visibleKey || key == g_noduleTypeKey )
				{
					updateVisibility();
				}
			}
		}

		ShaderPtr m_shader;

};


} // namespace

//////////////////////////////////////////////////////////////////////////
// ShaderNodeGadget
//////////////////////////////////////////////////////////////////////////

StandardNodeGadget::NodeGadgetTypeDescription<ShaderNodeGadget> ShaderNodeGadget::g_nodeGadgetTypeDescription( Shader::staticTypeId() );

ShaderNodeGadget::ShaderNodeGadget( Gaffer::NodePtr node )
	:	StandardNodeGadget( node )
{
	ShaderPtr shader = IECore::runTimeCast<Shader>( node );
	if( !shader )
	{
		throw IECore::Exception( "ShaderNodeGadget requires a Shader" );
	}

	setEdgeGadget( LeftEdge, new ShaderPlugAdder( shader, LeftEdge ) );
}

ShaderNodeGadget::~ShaderNodeGadget()
{
}
