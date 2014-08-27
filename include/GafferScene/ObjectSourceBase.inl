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

#include "OpenEXR/ImathBoxAlgo.h"

#include "IECore/NullObject.h"
#include "IECore/Camera.h"
#include "IECore/CoordinateSystem.h"

#include "Gaffer/Context.h"

#include "GafferScene/ObjectSourceBase.h"

namespace GafferScene
{

template<typename BaseType>
const IECore::RunTimeTyped::TypeDescription<ObjectSourceBase<BaseType> > ObjectSourceBase<BaseType>::g_typeDescription;

template<typename BaseType>
size_t ObjectSourceBase<BaseType>::g_firstPlugIndex = 0;

template<typename BaseType>
ObjectSourceBase<BaseType>::ObjectSourceBase( const std::string &name, const std::string &namePlugDefaultValue )
	:	BaseType( name )
{
	BaseType::storeIndexOfNextChild( g_firstPlugIndex );
	BaseType::addChild( new Gaffer::StringPlug( "name", Gaffer::Plug::In, namePlugDefaultValue ) );
	BaseType::addChild( new Gaffer::TransformPlug( "transform" ) );
	BaseType::addChild( new Gaffer::ObjectPlug( "__source", Gaffer::Plug::Out, IECore::NullObject::defaultNullObject() ) );
	BaseType::addChild( new Gaffer::ObjectPlug( "__inputSource", Gaffer::Plug::In, IECore::NullObject::defaultNullObject(), Gaffer::Plug::Default & ~Gaffer::Plug::Serialisable ) );
	inputSourcePlug()->setInput( sourcePlug() );
}

template<typename BaseType>
ObjectSourceBase<BaseType>::~ObjectSourceBase()
{
}

template<typename BaseType>
Gaffer::StringPlug *ObjectSourceBase<BaseType>::namePlug()
{
	return BaseType::template getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

template<typename BaseType>
const Gaffer::StringPlug *ObjectSourceBase<BaseType>::namePlug() const
{
	return BaseType::template getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

template<typename BaseType>
Gaffer::TransformPlug *ObjectSourceBase<BaseType>::transformPlug()
{
	return BaseType::template getChild<Gaffer::TransformPlug>( g_firstPlugIndex + 1 );
}

template<typename BaseType>
const Gaffer::TransformPlug *ObjectSourceBase<BaseType>::transformPlug() const
{
	return BaseType::template getChild<Gaffer::TransformPlug>( g_firstPlugIndex + 1 );
}

template<typename BaseType>
void ObjectSourceBase<BaseType>::affects( const Gaffer::Plug *input, Gaffer::DependencyNode::AffectedPlugsContainer &outputs ) const
{
	BaseType::affects( input, outputs );

	if( input == inputSourcePlug() )
	{
		outputs.push_back( BaseType::outPlug()->boundPlug() );
		outputs.push_back( BaseType::outPlug()->objectPlug() );
	}
	else if( input == namePlug() )
	{
		outputs.push_back( BaseType::outPlug()->childNamesPlug() );
	}
	else if( transformPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( BaseType::outPlug()->transformPlug() );
	}

}

template<typename BaseType>
void ObjectSourceBase<BaseType>::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BaseType::hash( output, context, h );

	if( output == sourcePlug() )
	{
		hashSource( context, h );
	}
}

template<typename BaseType>
Gaffer::ObjectPlug *ObjectSourceBase<BaseType>::sourcePlug()
{
	return BaseType::template getChild<Gaffer::ObjectPlug>( g_firstPlugIndex + 2 );
}

template<typename BaseType>
const Gaffer::ObjectPlug *ObjectSourceBase<BaseType>::sourcePlug() const
{
	return BaseType::template getChild<Gaffer::ObjectPlug>( g_firstPlugIndex + 2 );
}

template<typename BaseType>
Gaffer::ObjectPlug *ObjectSourceBase<BaseType>::inputSourcePlug()
{
	return BaseType::template getChild<Gaffer::ObjectPlug>( g_firstPlugIndex + 3 );
}

template<typename BaseType>
const Gaffer::ObjectPlug *ObjectSourceBase<BaseType>::inputSourcePlug() const
{
	return BaseType::template getChild<Gaffer::ObjectPlug>( g_firstPlugIndex + 3 );
}

template<typename BaseType>
void ObjectSourceBase<BaseType>::hashBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	BaseType::hashBound( path, context, parent, h );
	inputSourcePlug()->hash( h );
	if( path.size() == 0 )
	{
		transformPlug()->hash( h );
	}
}

template<typename BaseType>
void ObjectSourceBase<BaseType>::hashTransform( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	BaseType::hashTransform( path, context, parent, h );
	transformPlug()->hash( h );
}

template<typename BaseType>
void ObjectSourceBase<BaseType>::hashObject( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	BaseType::hashObject( path, context, parent, h );
	inputSourcePlug()->hash( h );
}

template<typename BaseType>
void ObjectSourceBase<BaseType>::hashChildNames( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	BaseType::hashChildNames( path, context, parent, h );
	namePlug()->hash( h );
}

template<typename BaseType>
void ObjectSourceBase<BaseType>::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == sourcePlug() )
	{
		static_cast<Gaffer::ObjectPlug *>( output )->setValue( computeSource( context ) );
		return;
	}

	return BaseType::compute( output, context );
}

template<typename BaseType>
Imath::Box3f ObjectSourceBase<BaseType>::computeBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	Imath::Box3f result;
	IECore::ConstObjectPtr object = inputSourcePlug()->getValue();

	if( const IECore::VisibleRenderable *renderable = IECore::runTimeCast<const IECore::VisibleRenderable>( object.get() ) )
	{
		result = renderable->bound();
	}
	else if( object->isInstanceOf( IECore::Camera::staticTypeId() ) )
	{
		result = Imath::Box3f( Imath::V3f( -0.5, -0.5, 0 ), Imath::V3f( 0.5, 0.5, 2.0 ) );
	}
	else if( object->isInstanceOf( IECore::CoordinateSystem::staticTypeId() ) )
	{
		result = Imath::Box3f( Imath::V3f( 0 ), Imath::V3f( 1 ) );
	}
	else
	{
		result = Imath::Box3f( Imath::V3f( -0.5 ), Imath::V3f( 0.5 ) );
	}

	if( path.size() == 0 )
	{
		result = Imath::transform( result, transformPlug()->matrix() );
	}
	return result;
}

template<typename BaseType>
Imath::M44f ObjectSourceBase<BaseType>::computeTransform( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() == 1 )
	{
		return transformPlug()->matrix();
	}
	return Imath::M44f();
}

template<typename BaseType>
IECore::ConstCompoundObjectPtr ObjectSourceBase<BaseType>::computeAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return parent->attributesPlug()->defaultValue();
}

template<typename BaseType>
IECore::ConstObjectPtr ObjectSourceBase<BaseType>::computeObject( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() == 1 )
	{
		return inputSourcePlug()->getValue();
	}
	return parent->objectPlug()->defaultValue();
}

template<typename BaseType>
IECore::ConstInternedStringVectorDataPtr ObjectSourceBase<BaseType>::computeChildNames( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() == 0 )
	{
		IECore::InternedStringVectorDataPtr result = new IECore::InternedStringVectorData();
		const std::string &name = namePlug()->getValue();
		if( name.size() )
		{
			result->writable().push_back( name );
		}
		else
		{
			result->writable().push_back( "unnamed" );
		}
		return result;
	}
	return parent->childNamesPlug()->defaultValue();
}

template<typename BaseType>
IECore::ConstCompoundObjectPtr ObjectSourceBase<BaseType>::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return parent->globalsPlug()->defaultValue();
}

} // namespace GafferScene
