//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferScene/ObjectSource.h"

namespace GafferScene
{

template<typename BaseType>
const IECore::RunTimeTyped::TypeDescription<ObjectSource<BaseType> > ObjectSource<BaseType>::g_typeDescription;

template<typename BaseType>
ObjectSource<BaseType>::ObjectSource( const std::string &name, const std::string &namePlugDefaultValue )
	:	BaseType( name )
{
	BaseType::addChild( new Gaffer::StringPlug( "name", Gaffer::Plug::In, namePlugDefaultValue ) );
	BaseType::addChild( new Gaffer::TransformPlug( "transform" ) );
	BaseType::addChild( new Gaffer::ObjectPlug( "__source", Gaffer::Plug::Out ) );
	BaseType::addChild( new Gaffer::ObjectPlug( "__inputSource", Gaffer::Plug::In, 0, Gaffer::Plug::Default & ~Gaffer::Plug::Serialisable ) );
	inputSourcePlug()->setInput( sourcePlug() );
}

template<typename BaseType>
ObjectSource<BaseType>::~ObjectSource()
{
}

template<typename BaseType>
Gaffer::StringPlug *ObjectSource<BaseType>::namePlug()
{
	return BaseType::template getChild<Gaffer::StringPlug>( "name" );
}

template<typename BaseType>
const Gaffer::StringPlug *ObjectSource<BaseType>::namePlug() const
{
	return BaseType::template getChild<Gaffer::StringPlug>( "name" );
}

template<typename BaseType>
Gaffer::TransformPlug *ObjectSource<BaseType>::transformPlug()
{
	return BaseType::template getChild<Gaffer::TransformPlug>( "transform" );
}

template<typename BaseType>
const Gaffer::TransformPlug *ObjectSource<BaseType>::transformPlug() const
{
	return BaseType::template getChild<Gaffer::TransformPlug>( "transform" );
}

template<typename BaseType>
void ObjectSource<BaseType>::affects( const Gaffer::ValuePlug *input, Gaffer::Node::AffectedPlugsContainer &outputs ) const
{
	BaseType::affects( input, outputs );
	
	if( input == inputSourcePlug() )
	{
		outputs.push_back( BaseType::outPlug() );
	}
	else if( input == namePlug() )
	{
		outputs.push_back( BaseType::outPlug()->childNamesPlug() );
	}
	else if( transformPlug()->isAncestorOf( input ) )
	{
		/// \todo Strictly speaking I think we should just push outPlug()->transformPlug()
		/// here, but the dirty propagation doesn't work for that just now. Get it working.
		outputs.push_back( BaseType::outPlug() );
	}

}

template<typename BaseType>
Gaffer::ObjectPlug *ObjectSource<BaseType>::sourcePlug()
{
	return BaseType::template getChild<Gaffer::ObjectPlug>( "__source" );
}

template<typename BaseType>
const Gaffer::ObjectPlug *ObjectSource<BaseType>::sourcePlug() const
{
	return BaseType::template getChild<Gaffer::ObjectPlug>( "__source" );
}

template<typename BaseType>
Gaffer::ObjectPlug *ObjectSource<BaseType>::inputSourcePlug()
{
	return BaseType::template getChild<Gaffer::ObjectPlug>( "__inputSource" );
}

template<typename BaseType>
const Gaffer::ObjectPlug *ObjectSource<BaseType>::inputSourcePlug() const
{
	return BaseType::template getChild<Gaffer::ObjectPlug>( "__inputSource" );
}
		
template<typename BaseType>
void ObjectSource<BaseType>::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == sourcePlug() )
	{
		static_cast<Gaffer::ObjectPlug *>( output )->setValue( computeSource( context ) );
		return;
	}
	
	return BaseType::compute( output, context );
}

template<typename BaseType>
Imath::Box3f ObjectSource<BaseType>::computeBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	Imath::Box3f result;
	IECore::ConstVisibleRenderablePtr renderable = IECore::runTimeCast<const IECore::VisibleRenderable>( inputSourcePlug()->getValue() );
	if( renderable )
	{
		result = renderable->bound();
		if( path == "/" )
		{
			result = Imath::transform( result, transformPlug()->matrix() );
		}
	}
	return result;
}

template<typename BaseType>
Imath::M44f ObjectSource<BaseType>::computeTransform( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path != "/" )
	{
		return transformPlug()->matrix();
	}
	return Imath::M44f();
}

template<typename BaseType>
IECore::ObjectPtr ObjectSource<BaseType>::computeObject( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path != "/" )
	{
		IECore::ConstObjectPtr object = inputSourcePlug()->getValue();
		return object ? object->copy() : 0;
	}
	return 0;
}

template<typename BaseType>
IECore::StringVectorDataPtr ObjectSource<BaseType>::computeChildNames( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path == "/" )
	{
		IECore::StringVectorDataPtr result = new IECore::StringVectorData();
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
	return 0;
}

} // namespace GafferScene