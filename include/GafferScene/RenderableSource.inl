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

#include "GafferScene/RenderableSource.h"

namespace GafferScene
{

template<typename BaseType>
const IECore::RunTimeTyped::TypeDescription<RenderableSource<BaseType> > RenderableSource<BaseType>::g_typeDescription;

template<typename BaseType>
RenderableSource<BaseType>::RenderableSource( const std::string &name, const std::string &namePlugDefaultValue )
	:	BaseType( name )
{
	BaseType::addChild( new Gaffer::StringPlug( "name", Gaffer::Plug::In, namePlugDefaultValue ) );
	BaseType::addChild( new Gaffer::TransformPlug( "transform" ) );
	BaseType::addChild( new Gaffer::ObjectPlug( "__renderable", Gaffer::Plug::Out ) );
	BaseType::addChild( new Gaffer::ObjectPlug( "__inputRenderable", Gaffer::Plug::In, 0, Gaffer::Plug::Default & ~Gaffer::Plug::Serialisable ) );
	inputRenderablePlug()->setInput( renderablePlug() );
}

template<typename BaseType>
RenderableSource<BaseType>::~RenderableSource()
{
}

template<typename BaseType>
Gaffer::StringPlug *RenderableSource<BaseType>::namePlug()
{
	return BaseType::template getChild<Gaffer::StringPlug>( "name" );
}

template<typename BaseType>
const Gaffer::StringPlug *RenderableSource<BaseType>::namePlug() const
{
	return BaseType::template getChild<Gaffer::StringPlug>( "name" );
}

template<typename BaseType>
Gaffer::TransformPlug *RenderableSource<BaseType>::transformPlug()
{
	return BaseType::template getChild<Gaffer::TransformPlug>( "transform" );
}

template<typename BaseType>
const Gaffer::TransformPlug *RenderableSource<BaseType>::transformPlug() const
{
	return BaseType::template getChild<Gaffer::TransformPlug>( "transform" );
}

template<typename BaseType>
void RenderableSource<BaseType>::affects( const Gaffer::ValuePlug *input, Gaffer::Node::AffectedPlugsContainer &outputs ) const
{
	BaseType::affects( input, outputs );
	
	if( input == inputRenderablePlug() )
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
Gaffer::ObjectPlug *RenderableSource<BaseType>::renderablePlug()
{
	return BaseType::template getChild<Gaffer::ObjectPlug>( "__renderable" );
}

template<typename BaseType>
const Gaffer::ObjectPlug *RenderableSource<BaseType>::renderablePlug() const
{
	return BaseType::template getChild<Gaffer::ObjectPlug>( "__renderable" );
}

template<typename BaseType>
Gaffer::ObjectPlug *RenderableSource<BaseType>::inputRenderablePlug()
{
	return BaseType::template getChild<Gaffer::ObjectPlug>( "__inputRenderable" );
}

template<typename BaseType>
const Gaffer::ObjectPlug *RenderableSource<BaseType>::inputRenderablePlug() const
{
	return BaseType::template getChild<Gaffer::ObjectPlug>( "__inputRenderable" );
}
		
template<typename BaseType>
void RenderableSource<BaseType>::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == renderablePlug() )
	{
		static_cast<Gaffer::ObjectPlug *>( output )->setValue( computeRenderable( context ) );
		return;
	}
	
	return BaseType::compute( output, context );
}

template<typename BaseType>
Imath::Box3f RenderableSource<BaseType>::computeBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	Imath::Box3f result;
	IECore::ConstVisibleRenderablePtr renderable = IECore::staticPointerCast<const IECore::VisibleRenderable>( inputRenderablePlug()->getValue() );
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
Imath::M44f RenderableSource<BaseType>::computeTransform( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path != "/" )
	{
		return transformPlug()->matrix();
	}
	return Imath::M44f();
}

template<typename BaseType>
IECore::PrimitivePtr RenderableSource<BaseType>::computeGeometry( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path != "/" )
	{
		IECore::ConstPrimitivePtr primitive = IECore::runTimeCast<const IECore::Primitive>( inputRenderablePlug()->getValue() );
		return primitive ? primitive->copy() : 0;
	}
	return 0;
}

template<typename BaseType>
IECore::StringVectorDataPtr RenderableSource<BaseType>::computeChildNames( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
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