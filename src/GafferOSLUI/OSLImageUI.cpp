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


#include "GafferOSL/OSLImage.h"
#include "GafferOSL/ClosurePlug.h"

#include "GafferUI/Nodule.h"
#include "GafferUI/NoduleLayout.h"
#include "GafferUI/PlugAdder.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/UndoScope.h"
#include "Gaffer/NameValuePlug.h"
#include "Gaffer/PlugAlgo.h"

#include "IECore/CompoundData.h"

#include "boost/algorithm/string.hpp"
#include "boost/bind/bind.hpp"

using namespace std;
using namespace boost::placeholders;
using namespace Gaffer;
using namespace GafferUI;

namespace
{

std::string cleanupChannelName( std::string s )
{
	boost::erase_all( s, "RGBA" );
	boost::erase_all( s, "RGB" );
	return s;
}

class OSLImagePlugAdder : public PlugAdder
{

	public :

		OSLImagePlugAdder( GraphComponentPtr plugsParent )
			:   m_plugsParent( IECore::runTimeCast<Plug>( plugsParent ) )
		{
			if( ! m_plugsParent )
			{
				throw IECore::Exception( "OSLImageUI::PlugAdder constructor must be passed plug" );
			}
			buttonReleaseSignal().connect( boost::bind( &OSLImagePlugAdder::buttonRelease, this, ::_2 ) );
		}

	protected :

		bool canCreateConnection( const Plug *endpoint ) const override
		{
			IECore::ConstCompoundDataPtr plugAdderOptions = Metadata::value<IECore::CompoundData>( m_plugsParent->node(), "plugAdderOptions" );
			return !availableChannels( plugAdderOptions.get(), endpoint ).empty();
		}

		void createConnection( Plug *endpoint ) override
		{
			IECore::ConstCompoundDataPtr plugAdderOptions = Metadata::value<IECore::CompoundData>( m_plugsParent->node(), "plugAdderOptions" );
			vector<std::string> names = availableChannels( plugAdderOptions.get(), endpoint );

			std::string picked = menuSignal()( "Connect To", names );
			if( !picked.size() )
			{
				return;
			}

			NameValuePlug *newPlug = addPlug( cleanupChannelName( picked ), plugAdderOptions->member<IECore::Data>( picked ) );
			newPlug->valuePlug()->setInput( endpoint );
		}

	private :
		std::set<std::string> usedNames() const
		{
			std::set<std::string> used;
			for( NameValuePlug::Iterator it( m_plugsParent.get() ); !it.done(); ++it )
			{
				// TODO - this method for checking if a plug variesWithContext should probably live in PlugAlgo
				// ( it's based on Switch::variesWithContext )
				PlugPtr sourcePlug = (*it)->namePlug()->source<Gaffer::Plug>();
				bool variesWithContext = sourcePlug->direction() == Plug::Out && IECore::runTimeCast<const ComputeNode>( sourcePlug->node() );
				if( !variesWithContext )
				{
					used.insert( (*it)->namePlug()->getValue() );
				}
			}
			return used;
		}

		NameValuePlug* addPlug( std::string channelName, const IECore::Data *defaultData )
		{
			std::set<std::string> used = usedNames();

			std::string plugName = "channel";
			PlugPtr valuePlug;
			FloatPlugPtr alphaValuePlug;
			if( defaultData )
			{
				const IECore::Color4fData *color4fDefaultData = IECore::runTimeCast<const IECore::Color4fData>( defaultData );
				if( color4fDefaultData )
				{
					const Imath::Color4f &default4 = color4fDefaultData->readable();
					alphaValuePlug = new FloatPlug( "value", Plug::In, default4[3], Imath::limits<float>::min(), Imath::limits<float>::max(), Plug::Flags::Default | Plug::Flags::Dynamic );
					defaultData = new IECore::Color3fData( Imath::Color3f( default4[0], default4[1], default4[2] ) );
				}

				if( used.find( channelName ) != used.end() )
				{
					std::string newName;
					for( int i = 2; ; i++ )
					{
						newName = channelName + std::to_string( i );
						if( used.find( newName ) == used.end() )
						{
							break;
						}
					}
					channelName = newName;
				}
				valuePlug = PlugAlgo::createPlugFromData( "value", Plug::In, Plug::Flags::Default | Plug::Flags::Dynamic, defaultData );
			}
			else
			{
				valuePlug = new GafferOSL::ClosurePlug( "value", Plug::In, Plug::Flags::Default | Plug::Flags::Dynamic );
				plugName = "closure";
				channelName = "";
			}

			UndoScope undoScope( m_plugsParent->ancestor<ScriptNode>() );

			NameValuePlugPtr created = new Gaffer::NameValuePlug( channelName, valuePlug, true, plugName );
			m_plugsParent->addChild( created );
			if( alphaValuePlug )
			{
				std::string alphaChannelName = "A";
				if( channelName.size() )
				{
					alphaChannelName = channelName + ".A";
				}
				m_plugsParent->addChild( new Gaffer::NameValuePlug( alphaChannelName, alphaValuePlug, true, plugName ) );
			}
			return created.get();
		}

		bool buttonRelease( const ButtonEvent &event )
		{
			IECore::ConstCompoundDataPtr plugAdderOptions = Metadata::value<IECore::CompoundData>( m_plugsParent->node(), "plugAdderOptions" );
			vector<std::string> origNames = availableChannels( plugAdderOptions.get() );
			map<std::string, std::string> nameMapping;
			vector<std::string> standardMenuNames;
			vector<std::string> customMenuNames;
			vector<std::string> advancedMenuNames;
			for( auto &n : origNames )
			{
				std::string menuName;
				if( n.substr( 0, 6 ) == "custom" )
				{
					menuName = "Custom/" + n.substr( 6 );
					customMenuNames.push_back( menuName );
				}
				else if( n == "closure" )
				{
					menuName = "Advanced/Closure";
					advancedMenuNames.push_back( menuName );
				}
				else
				{
					menuName = "Standard/" + n;
					standardMenuNames.push_back( menuName );
				}
				nameMapping[ menuName ] = n;
			}

			vector<std::string> menuNames;
			menuNames.insert( menuNames.end(), standardMenuNames.begin(), standardMenuNames.end() );
			menuNames.insert( menuNames.end(), customMenuNames.begin(), customMenuNames.end() );
			menuNames.insert( menuNames.end(), advancedMenuNames.begin(), advancedMenuNames.end() );
			std::string picked = menuSignal()( "Add Input", menuNames );
			if( !picked.size() )
			{
				return false;
			}

			std::string origName = nameMapping[picked];
			addPlug( cleanupChannelName( origName ), plugAdderOptions->member<IECore::Data>(origName) );

			return true;
		}

		// Which channels are available that haven't already been used, and that match the input plug if provided
		vector<std::string> availableChannels( const IECore::CompoundData* plugAdderOptions, const Plug *input = nullptr ) const
		{
			if( !plugAdderOptions )
			{
				throw IECore::Exception( "OSLImageUI::PlugAdder requires plugAdderOptions metadata" );
			}

			IECore::DataPtr matchingDataType;
			const ValuePlug *valueInput = IECore::runTimeCast< const ValuePlug >( input );
			if( valueInput )
			{
				try
				{
					matchingDataType = PlugAlgo::getValueAsData( valueInput );
				}
				catch( ... )
				{
					// If we can't extract data, then it doesn't match any of our accepted plug types
				}
			}

			vector<std::string> result;
			std::set<std::string> used = usedNames();
			for( auto it=plugAdderOptions->readable().begin(); it!=plugAdderOptions->readable().end(); it++ )
			{
				std::string bareLabel = cleanupChannelName( it->first );

				// For plugs that aren't closures or custom, we need to check if we've already
				// used the name
				if( it->second && bareLabel.substr( 0, 6 ) != "custom" && used.find( bareLabel ) != used.end() )
				{
					// Already added
					continue;
				}

				if( input )
				{
					if( input->typeId() == GafferOSL::ClosurePlug::staticTypeId() )
					{
						if( it->second )
						{
							continue;
						}
					}
					else
					{
						if( !matchingDataType || !it->second || matchingDataType->typeId() != it->second->typeId() )
						{
							continue;
						}
					}
				}

				result.push_back( it->first );
			}

			std::sort( result.begin(), result.end() );
			vector<std::string> customSortResult;
			for( const std::string &i : { "RGB", "RGBA", "R", "G", "B", "A" } )
			{
				if( std::find( result.begin(), result.end(), i ) != result.end() )
				{
					customSortResult.push_back( i );
				}
			}
			for( const std::string &i : result )
			{
				if( std::find( customSortResult.begin(), customSortResult.end(), i ) == customSortResult.end() )
				{
					customSortResult.push_back( i );
				}
			}

			return customSortResult;
		}

		PlugPtr m_plugsParent;
};

struct Registration
{
		Registration()
		{
			NoduleLayout::registerCustomGadget( "GafferOSLUI.OSLImageUI.PlugAdder", &create );
		}

	private :

		static GadgetPtr create( GraphComponentPtr parent )
		{
			return new OSLImagePlugAdder( parent );
		}
};

Registration g_registration;

} // namespace
