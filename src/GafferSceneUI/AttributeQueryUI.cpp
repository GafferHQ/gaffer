//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferSceneUI/AttributeQueryUI.h"

#include "Gaffer/BoxPlug.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/TypedPlug.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/UndoScope.h"

#include "GafferUI/NoduleLayout.h"
#include "GafferUI/PlugAdder.h"

#include "IECore/Exception.h"
#include "IECore/NullObject.h"

#include <boost/bind.hpp>
#include <boost/multi_index_container.hpp>
#include <boost/multi_index/mem_fun.hpp>
#include <boost/multi_index/ordered_index.hpp>
#include <boost/multi_index/random_access_index.hpp>

#include <algorithm>
#include <cassert>
#include <functional>
#include <iterator>

namespace
{

template< typename ValueType >
Gaffer::ConstValuePlugPtr createNumericPlug(
	const std::string& name, const Gaffer::Plug::Direction direction, const ValueType& value, const unsigned flags )
{
	const Gaffer::ConstValuePlugPtr plug( new Gaffer::NumericPlug< ValueType >( name, direction, value,
		ValueType( Imath::limits< ValueType >::min() ),
		ValueType( Imath::limits< ValueType >::max() ), flags ) );
	return plug;
}

template< typename ValueType >
Gaffer::ConstValuePlugPtr createCompoundNumericPlug(
	const std::string& name, const Gaffer::Plug::Direction direction, const ValueType& value, const unsigned flags )
{
	const Gaffer::ConstValuePlugPtr plug( new Gaffer::CompoundNumericPlug< ValueType >( name, direction, value,
		ValueType( Imath::limits< typename ValueType::BaseType >::min() ),
		ValueType( Imath::limits< typename ValueType::BaseType >::max() ), flags ) );
	return plug;
}

template< typename ValueType >
Gaffer::ConstValuePlugPtr createBoxPlug(
	const std::string& name, const Gaffer::Plug::Direction direction, const Imath::Box< ValueType >& value, const unsigned flags )
{
	const Gaffer::ConstValuePlugPtr plug( new Gaffer::BoxPlug< Imath::Box< ValueType > >( name, direction, value,
		ValueType( Imath::limits< typename ValueType::BaseType >::min() ),
		ValueType( Imath::limits< typename ValueType::BaseType >::max() ), flags ) );
	return plug;
}

template< typename ValueType >
Gaffer::ConstValuePlugPtr createVectorDataPlug(
	const std::string& name, const Gaffer::Plug::Direction direction, const IECore::TypedData< std::vector< ValueType > >* value, const unsigned flags )
{
	const Gaffer::ConstValuePlugPtr plug( new Gaffer::TypedObjectPlug< IECore::TypedData< std::vector< ValueType > > >( name, direction, value, flags ) );
	return plug;
}

struct MenuItem
{
	explicit
	MenuItem( const std::string& name, Gaffer::ConstValuePlugPtr plug = Gaffer::ConstValuePlugPtr() )
	: m_name( name )
	, m_plug( plug )
	{}

	const std::string& getName() const
	{
		return m_name;
	}

	const Gaffer::ValuePlug* getPlug() const
	{
		return m_plug.get();
	}

private:

	std::string m_name;
	Gaffer::ConstValuePlugPtr m_plug;
};

typedef boost::multi_index_container<
	MenuItem,
	boost::multi_index::indexed_by<
		boost::multi_index::random_access<>,
		boost::multi_index::ordered_non_unique<
			boost::multi_index::const_mem_fun< MenuItem, const std::string&, & MenuItem::getName > > > > MenuItemContainer;

struct PlugAdder : GafferUI::PlugAdder
{
	explicit PlugAdder( GafferScene::AttributeQuery& query )
	: GafferUI::PlugAdder()
	, m_query( & query )
	{
		m_query->childAddedSignal().connect( boost::bind( & PlugAdder::updateVisibility, this ) );
		m_query->childRemovedSignal().connect( boost::bind( & PlugAdder::updateVisibility, this ) );

		buttonReleaseSignal().connect( boost::bind( & PlugAdder::buttonRelease, this, ::_2 ) );

		updateVisibility();
	}

	~PlugAdder() override
	{}

protected:

	bool canCreateConnection( const Gaffer::Plug* plug ) const override
	{
		assert( m_query );

		return (
			( GafferUI::PlugAdder::canCreateConnection( plug ) ) &&
			( plug->direction() == Gaffer::Plug::In ) &&
			( plug->node() != m_query ) &&
			( m_query->canSetup( IECore::runTimeCast< const Gaffer::ValuePlug >( plug ) ) ) );
	}

	void createConnection( Gaffer::Plug* plug ) override
	{
		assert( plug->direction() == Gaffer::Plug::In );

		m_query->setup( IECore::assertedStaticCast< const Gaffer::ValuePlug >( plug ) );

		plug->setInput( m_query->valuePlug() );
	}

private:

	bool buttonRelease( const GafferUI::ButtonEvent& event )
	{
		return GafferSceneUI::AttributeQueryUI::showSetupMenu( *m_query );
	}

	void updateVisibility()
	{
		setVisible( !( m_query->isSetup() ) );
	}

	GafferScene::AttributeQueryPtr m_query;
};

struct Registration
{
	Registration()
	{
		GafferUI::NoduleLayout::registerCustomGadget( "GafferSceneUI.AttributeQueryUI.PlugAdder", & Registration::create );
	}

	static GafferUI::GadgetPtr create( Gaffer::GraphComponentPtr parent )
	{
		const GafferScene::AttributeQueryPtr query = IECore::runTimeCast< GafferScene::AttributeQuery >( parent );

		if( ! query )
		{
			throw IECore::Exception( "AttributeQueryUI.PlugAdder requires an AttributeQuery" );
		}

		const GafferUI::GadgetPtr gadget( new PlugAdder( *query ) );
		return gadget;
	}
};

Registration m_registration;

} // namespace

namespace GafferSceneUI
{
namespace AttributeQueryUI
{

bool showSetupMenu( GafferScene::AttributeQuery& query )
{
	static MenuItemContainer items;
	static std::vector< std::string > names;
	static const std::string title( "Plug type" );

	if( items.empty() )
	{
		const std::string name( "value" );
		const Gaffer::Plug::Direction direction = Gaffer::Plug::In;
		const unsigned flags = Gaffer::Plug::Flags::Default | Gaffer::Plug::Flags::Dynamic;

		items.push_back( MenuItem( "Bool", new Gaffer::BoolPlug( name, direction, false, flags ) ) );
		items.push_back( MenuItem( "Float", createNumericPlug( name, direction, 0.f, flags ) ) );
		items.push_back( MenuItem( "Int", createNumericPlug( name, direction, 0, flags ) ) );
		items.push_back( MenuItem( "" ) );
		items.push_back( MenuItem( "String", new Gaffer::StringPlug( name, direction, "", flags ) ) );
		items.push_back( MenuItem( "" ) );
		items.push_back( MenuItem( "V2i", createCompoundNumericPlug( name, direction, Imath::V2i( 0 ), flags ) ) );
		items.push_back( MenuItem( "V2f", createCompoundNumericPlug( name, direction, Imath::V2f( 0 ), flags ) ) );
		items.push_back( MenuItem( "V3i", createCompoundNumericPlug( name, direction, Imath::V3i( 0 ), flags ) ) );
		items.push_back( MenuItem( "V3f", createCompoundNumericPlug( name, direction, Imath::V3f( 0 ), flags ) ) );
		items.push_back( MenuItem( "" ) );
		items.push_back( MenuItem( "Color3f", createCompoundNumericPlug( name, direction, Imath::Color3f( 0 ), flags ) ) );
		items.push_back( MenuItem( "Color4f", createCompoundNumericPlug( name, direction, Imath::Color4f( 0 ), flags ) ) );
		items.push_back( MenuItem( "" ) );
		items.push_back( MenuItem( "Box2i", createBoxPlug( name, direction, Imath::Box2i( Imath::V2i( 0 ) ), flags ) ) );
		items.push_back( MenuItem( "Box2f", createBoxPlug( name, direction, Imath::Box2f( Imath::V2f( 0.f ) ), flags ) ) );
		items.push_back( MenuItem( "Box3i", createBoxPlug( name, direction, Imath::Box3i( Imath::V3i( 0 ) ), flags ) ) );
		items.push_back( MenuItem( "Box3f", createBoxPlug( name, direction, Imath::Box3f( Imath::V3f( 0.f ) ), flags ) ) );
		items.push_back( MenuItem( "" ) );
		items.push_back( MenuItem( "Object", new Gaffer::ObjectPlug( name, direction, IECore::NullObject::defaultNullObject(), flags ) ) );
		items.push_back( MenuItem( "" ) );
		items.push_back( MenuItem( "Array/Bool", createVectorDataPlug( name, direction, new IECore::BoolVectorData(), flags ) ) );
		items.push_back( MenuItem( "Array/Float", createVectorDataPlug( name, direction, new IECore::FloatVectorData(), flags ) ) );
		items.push_back( MenuItem( "Array/Int", createVectorDataPlug( name, direction, new IECore::IntVectorData(), flags ) ) );
		items.push_back( MenuItem( "Array/" ) );
		items.push_back( MenuItem( "Array/String", createVectorDataPlug( name, direction, new IECore::StringVectorData(), flags ) ) );
	}

	if( names.empty() )
	{
		const MenuItemContainer::nth_index< 0 >::type& index = items.get< 0 >();
		std::transform( index.begin(), index.end(), std::back_inserter( names ), std::mem_fn( & MenuItem::getName ) );
	}

	if( query.isSetup() )
	{
		return false;
	}

	const std::string name = GafferUI::PlugAdder::menuSignal()( title, names );

	if( name.empty() )
	{
		return false;
	}

	const MenuItemContainer::nth_index< 1 >::type& index = items.get< 1 >();
	const MenuItemContainer::nth_index< 1 >::type::iterator it = index.find( name );

	if( it == index.end() )
	{
		return false;
	}

	{
		Gaffer::UndoScope undoScope( query.ancestor< Gaffer::ScriptNode >() );
		query.setup( ( *it ).getPlug() );
	}

	return true;
}

} // AttributeQueryUI
} // GafferSceneUI
