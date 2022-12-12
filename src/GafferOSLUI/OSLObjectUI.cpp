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


#include "GafferOSL/OSLObject.h"
#include "GafferOSL/ClosurePlug.h"

#include "GafferUI/Nodule.h"
#include "GafferUI/NoduleLayout.h"
#include "GafferUI/PlugAdder.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/UndoScope.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/NameValuePlug.h"
#include "Gaffer/PlugAlgo.h"

#include "IECore/CompoundData.h"

#include "boost/bind/bind.hpp"

using namespace std;
using namespace boost::placeholders;
using namespace Gaffer;
using namespace GafferUI;

namespace
{

class OSLObjectPlugAdder : public PlugAdder
{

	public :

		OSLObjectPlugAdder( GraphComponentPtr plugsParent )
			:   m_plugsParent( IECore::runTimeCast<Plug>( plugsParent ) )
		{
			if( ! m_plugsParent )
			{
				throw IECore::Exception( "OSLObjectUI::PlugAdder constructor must be passed plug" );
			}
			buttonReleaseSignal().connect( boost::bind( &OSLObjectPlugAdder::buttonRelease, this, ::_2 ) );
		}

	protected :

		bool canCreateConnection( const Plug *endpoint ) const override
		{
			if( !PlugAdder::canCreateConnection( endpoint ) )
			{
				return false;
			}

			if( MetadataAlgo::readOnly( m_plugsParent.get() ) )
			{
				return false;
			}

			IECore::ConstCompoundDataPtr plugAdderOptions = Metadata::value<IECore::CompoundData>( m_plugsParent->node(), "plugAdderOptions" );
			return !availablePrimVars( plugAdderOptions.get(), endpoint ).empty();
		}

		void createConnection( Plug *endpoint ) override
		{
			IECore::ConstCompoundDataPtr plugAdderOptions = Metadata::value<IECore::CompoundData>( m_plugsParent->node(), "plugAdderOptions" );
			vector<std::string> names = availablePrimVars( plugAdderOptions.get(), endpoint );

			std::string picked = menuSignal()( "Connect To", names );
			if( !picked.size() )
			{
				return;
			}

			NameValuePlug *newPlug = addPlug( picked, plugAdderOptions->member<IECore::Data>( picked ) );
			newPlug->valuePlug()->setInput( endpoint );
		}

	private :
		std::set<std::string> usedNames() const
		{
			std::set<std::string> used;
			for( const auto &plug : NameValuePlug::Range( *m_plugsParent ) )
			{
				if( !PlugAlgo::dependsOnCompute( plug->namePlug() ) )
				{
					used.insert( plug->namePlug()->getValue() );
				}
			}
			return used;
		}

		NameValuePlug* addPlug( std::string primVarName, const IECore::Data *defaultData )
		{
			std::set<std::string> used = usedNames();

			std::string plugName = "primitiveVariable";
			PlugPtr valuePlug;
			if( defaultData )
			{
				if( used.find( primVarName ) != used.end() )
				{
					std::string newName;
					for( int i = 2; ; i++ )
					{
						newName = primVarName + std::to_string( i );
						if( used.find( newName ) == used.end() )
						{
							break;
						}
					}
					primVarName = newName;
				}
				valuePlug = PlugAlgo::createPlugFromData( "value", Plug::In, Plug::Flags::Default | Plug::Flags::Dynamic, defaultData );
			}
			else
			{
				valuePlug = new GafferOSL::ClosurePlug( "value", Plug::In, Plug::Flags::Default | Plug::Flags::Dynamic );
				plugName = "closure";
				primVarName = "";
			}

			UndoScope undoScope( m_plugsParent->ancestor<ScriptNode>() );

			NameValuePlugPtr created = new Gaffer::NameValuePlug( primVarName, valuePlug, true, plugName );
			m_plugsParent->addChild( created );
			return created.get();
		}

		bool buttonRelease( const ButtonEvent &event )
		{
			if( MetadataAlgo::readOnly( m_plugsParent.get() ) )
			{
				return false;
			}

			IECore::ConstCompoundDataPtr plugAdderOptions = Metadata::value<IECore::CompoundData>( m_plugsParent->node(), "plugAdderOptions" );
			vector<std::string> origNames = availablePrimVars( plugAdderOptions.get() );
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
			addPlug( origName, plugAdderOptions->member<IECore::Data>(origName) );

			return true;
		}

		// Which prim vars are available that haven't already been used, and that match the input plug if provided
		vector<std::string> availablePrimVars( const IECore::CompoundData* plugAdderOptions, const Plug *input = nullptr ) const
		{
			if( !plugAdderOptions )
			{
				throw IECore::Exception( "OSLObjectUI::PlugAdder requires plugAdderOptions metadata" );
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
				std::string name = it->first;
				// For plugs that aren't closures or custom, we need to check if we've already
				// used the primitive variable name
				if( it->second && name.substr( 0, 6 ) != "custom" && used.find( name ) != used.end() )
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

				result.push_back( name );
			}

			std::sort( result.begin(), result.end() );

			return result;
		}

		PlugPtr m_plugsParent;
};

struct Registration
{
		Registration()
		{
			NoduleLayout::registerCustomGadget( "GafferOSLUI.OSLObjectUI.PlugAdder", &create );
		}

	private :

		static GadgetPtr create( GraphComponentPtr parent )
		{
			return new OSLObjectPlugAdder( parent );
		}
};

Registration g_registration;

} // namespace
