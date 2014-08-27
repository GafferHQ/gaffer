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

#include "IECore/Camera.h"
#include "IECore/Transform.h"
#include "IECore/AngleConversion.h"
#include "IECore/MatrixTransform.h"

#include "IECoreGL/Primitive.h"

#include "Gaffer/CompoundPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/TypedPlug.h"

#include "GafferUI/View3D.h"

using namespace Imath;
using namespace IECoreGL;
using namespace Gaffer;
using namespace GafferUI;

IE_CORE_DEFINERUNTIMETYPED( View3D );

View3D::View3D( const std::string &name, Gaffer::PlugPtr inPlug )
	:	View( name, inPlug ), m_baseState( new IECoreGL::State( true ) )
{

	// base state setup

	m_baseState->add( new WireframeColorStateComponent( Color4f( 0.2f, 0.2f, 0.2f, 1.0f ) ) );
	m_baseState->add( new PointColorStateComponent( Color4f( 0.9f, 0.9f, 0.9f, 1.0f ) ) );
	m_baseState->add( new IECoreGL::Primitive::PointWidth( 2.0f ) );

	// plugs

	CompoundPlugPtr baseState = new CompoundPlug( "baseState" );
	addChild( baseState );

	CompoundPlugPtr solid = new CompoundPlug( "solid" );
	baseState->addChild( solid );
	solid->addChild( new BoolPlug( "enabled", Plug::In, true ) );
	solid->addChild( new BoolPlug( "override" ) );

	CompoundPlugPtr wireframe = new CompoundPlug( "wireframe" );
	baseState->addChild( wireframe );
	wireframe->addChild( new BoolPlug( "enabled" ) );
	wireframe->addChild( new BoolPlug( "override" ) );

	CompoundPlugPtr points = new CompoundPlug( "points" );
	baseState->addChild( points );
	points->addChild( new BoolPlug( "enabled" ) );
	points->addChild( new BoolPlug( "override" ) );

	CompoundPlugPtr bound = new CompoundPlug( "bound" );
	baseState->addChild( bound );
	bound->addChild( new BoolPlug( "enabled" ) );
	bound->addChild( new BoolPlug( "override" ) );

	plugSetSignal().connect( boost::bind( &View3D::plugSet, this, ::_1 ) );

	// camera

	IECore::CameraPtr camera = new IECore::Camera();

	camera->parameters()["projection"] = new IECore::StringData( "perspective" );
	camera->parameters()["projection:fov"] = new IECore::FloatData( 54.43 ); // 35 mm focal length

	M44f matrix;
	matrix.translate( V3f( 0, 0, 1 ) );
	matrix.rotate( IECore::degreesToRadians( V3f( -25, 45, 0 ) ) );
	camera->setTransform( new IECore::MatrixTransform( matrix ) );

	viewportGadget()->setCamera( camera.get() );
}

View3D::~View3D()
{
}

const IECoreGL::State *View3D::baseState() const
{
	return m_baseState.get();
}

View3D::BaseStateChangedSignal &View3D::baseStateChangedSignal()
{
	return m_baseStateChangedSignal;
}

void View3D::plugSet( const Gaffer::Plug *plug )
{
	if( plug == getChild<Plug>( "baseState" ) )
	{
		updateBaseState();
	}
}

void View3D::updateBaseState()
{
	const CompoundPlug *baseState = getChild<CompoundPlug>( "baseState" );

	const CompoundPlug *solid = baseState->getChild<CompoundPlug>( "solid" );
	m_baseState->add(
		new Primitive::DrawSolid( solid->getChild<BoolPlug>( "enabled" )->getValue() ),
		solid->getChild<BoolPlug>( "override" )->getValue()
	);

	const CompoundPlug *wireframe = baseState->getChild<CompoundPlug>( "wireframe" );
	m_baseState->add(
		new Primitive::DrawWireframe( wireframe->getChild<BoolPlug>( "enabled" )->getValue() ),
		wireframe->getChild<BoolPlug>( "override" )->getValue()
	);

	const CompoundPlug *points = baseState->getChild<CompoundPlug>( "points" );
	m_baseState->add(
		new Primitive::DrawPoints( points->getChild<BoolPlug>( "enabled" )->getValue() ),
		points->getChild<BoolPlug>( "override" )->getValue()
	);

	const CompoundPlug *bound = baseState->getChild<CompoundPlug>( "bound" );
	m_baseState->add(
		new Primitive::DrawBound( bound->getChild<BoolPlug>( "enabled" )->getValue() ),
		bound->getChild<BoolPlug>( "override" )->getValue()
	);

	baseStateChangedSignal()( this );
}
