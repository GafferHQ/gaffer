//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/ShaderTweaks.h"

#include "GafferScene/TweakPlug.h"

#include "GafferUI/Nodule.h"
#include "GafferUI/NoduleLayout.h"
#include "GafferUI/PlugAdder.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/UndoScope.h"

#include "boost/bind/bind.hpp"

using namespace std;
using namespace boost::placeholders;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;

namespace
{

IECore::InternedString g_visibleKey( "noduleLayout:visible" );
IECore::InternedString g_noduleTypeKey( "nodule:type" );

class TweakPlugAdder : public PlugAdder
{

	public :

		TweakPlugAdder( PlugPtr plugsParent )
			:	m_plugsParent( plugsParent )
		{
			plugsParent->node()->plugSetSignal().connect( boost::bind( &TweakPlugAdder::plugSet, this, ::_1 ) );
			plugsParent->node()->plugInputChangedSignal().connect( boost::bind( &TweakPlugAdder::plugInputChanged, this, ::_1 ) );
			plugsParent->childAddedSignal().connect( boost::bind( &TweakPlugAdder::childAdded, this ) );
			plugsParent->childRemovedSignal().connect( boost::bind( &TweakPlugAdder::childRemoved, this ) );
			Metadata::plugValueChangedSignal( plugsParent->node() ).connect(
				boost::bind( &TweakPlugAdder::plugMetadataChanged, this, ::_1, ::_2 )
			);
			buttonReleaseSignal().connect( boost::bind( &TweakPlugAdder::buttonRelease, this, ::_2 ) );

			updateVisibility();
		}

	protected :

		bool canCreateConnection( const Plug *endpoint ) const override
		{
			vector<Plug *> plugs = showablePlugs( endpoint );
			return !plugs.empty();
		}

		void createConnection( Plug *endpoint ) override
		{
			vector<Plug *> plugs = showablePlugs( endpoint );
			Plug *plug = plugMenuSignal()( "Connect To", plugs );
			if( !plug )
			{
				return;
			}

			Metadata::registerValue( plug, g_visibleKey, new IECore::BoolData( true ) );
			static_cast<TweakPlug *>( plug )->valuePlug()->setInput( endpoint );
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

			UndoScope undoScope( m_plugsParent->ancestor<ScriptNode>() );
			Metadata::registerValue( plug, g_visibleKey, new IECore::BoolData( true ) );
			return true;
		}

		vector<Plug *> showablePlugs( const Plug *input = nullptr ) const
		{
			vector<Plug *> result;

			for( TweakPlug::Iterator it( m_plugsParent.get() ); !it.done(); ++it )
			{
				TweakPlug *tweakPlug = it->get();
				if( input )
				{
					if( input->direction() != Plug::Out || !tweakPlug->valuePlug()->acceptsInput( input ) )
					{
						continue;
					}
				}
				IECore::ConstBoolDataPtr visible = Metadata::value<IECore::BoolData>( tweakPlug, g_visibleKey );
				if( !visible || visible->readable() )
				{
					continue;
				}

				ValuePlug *valuePlug = tweakPlug->valuePlug();
				if( !valuePlug )
				{
					// It's possible that the TweakPlug is in an invalid state
					// when we're getting called here. Ignore the plug if that's
					// the case.
					continue;
				}

				if( MetadataAlgo::readOnly( valuePlug ) )
				{
					continue;
				}

				if( !tweakPlug->modePlug()->getInput() )
				{
					if( tweakPlug->modePlug()->getValue() != TweakPlug::Replace )
					{
						continue;
					}
				}

				result.push_back( tweakPlug );
			}

			return result;
		}

		void updateVisibility()
		{
			setVisible( !showablePlugs().empty() );
		}

		void plugSet( const Gaffer::Plug *plug )
		{
			if( auto tweakPlug = plug->parent<TweakPlug>() )
			{
				if( plug == tweakPlug->modePlug() )
				{
					updateVisibility();
				}
			}
		}

		void plugInputChanged( const Gaffer::Plug *plug )
		{
			if( auto tweakPlug = plug->parent<TweakPlug>() )
			{
				if( plug == tweakPlug->modePlug() )
				{
					updateVisibility();
				}
			}
		}

		void childAdded()
		{
			updateVisibility();
		}

		void childRemoved()
		{
			updateVisibility();
		}

		void plugMetadataChanged( const Gaffer::Plug *plug, IECore::InternedString key )
		{
			if( plug->parent() == m_plugsParent )
			{
				if( key == g_visibleKey || key == g_noduleTypeKey )
				{
					updateVisibility();
				}
			}
		}

		GraphComponentPtr m_plugsParent;

};

struct Registration
{

	Registration()
	{
		NoduleLayout::registerCustomGadget( "GafferSceneUI.ShaderTweaksUI.PlugAdder", &create );
	}

	private :

		static GadgetPtr create( GraphComponentPtr parent )
		{
			return new TweakPlugAdder( boost::static_pointer_cast<Plug>( parent ) );
		}

};

Registration g_registration;

} // namespace
