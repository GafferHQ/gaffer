//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#include "GafferCortex/TypedParameterHandler.h"

#include "Gaffer/PlugAlgo.h"
#include "Gaffer/TypedPlug.h"

#include "IECore/CompoundObject.h"
#include "IECore/TypedParameter.h"

namespace GafferCortex
{

template<typename T>
ParameterHandler::ParameterHandlerDescription<TypedParameterHandler<T>, IECore::TypedParameter<T> > TypedParameterHandler<T>::g_description;

template<typename T>
TypedParameterHandler<T>::TypedParameterHandler( typename ParameterType::Ptr parameter )
	:	m_parameter( parameter )
{
}

template<typename T>
TypedParameterHandler<T>::~TypedParameterHandler()
{
}

template<typename T>
IECore::Parameter *TypedParameterHandler<T>::parameter()
{
	return m_parameter.get();
}

template<typename T>
const IECore::Parameter *TypedParameterHandler<T>::parameter() const
{
	return m_parameter.get();
}

template<typename T>
void TypedParameterHandler<T>::restore( Gaffer::GraphComponent *plugParent )
{
}

template<typename T>
typename TypedParameterHandler<T>::PlugType::Ptr TypedParameterHandler<T>::createPlug( Gaffer::Plug::Direction direction ) const
{
	return new PlugType( m_parameter->name(), direction, m_parameter->typedDefaultValue() );
}

template<>
TypedParameterHandler<std::string>::PlugType::Ptr TypedParameterHandler<std::string>::createPlug( Gaffer::Plug::Direction direction, IECore::StringAlgo::Substitutions substitutions ) const
{
	return new Gaffer::StringPlug( m_parameter->name(), direction, m_parameter->typedDefaultValue(), Gaffer::Plug::Default, substitutions );
}

template<typename T>
Gaffer::Plug *TypedParameterHandler<T>::setupPlug( Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction, unsigned flags )
{
	m_plug = plugParent->getChild<PlugType>( m_parameter->name() );
	if( !m_plug || m_plug->direction()!=direction )
	{
		m_plug = createPlug( direction );
		Gaffer::PlugAlgo::replacePlug( plugParent, m_plug );
	}

	setupPlugFlags( m_plug.get(), flags );

	return m_plug.get();
}

template<>
Gaffer::Plug *TypedParameterHandler<std::string>::setupPlug( Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction, unsigned flags )
{
	// We have to turn off substitutions for FileSequenceParameters because they'd remove the
	// #### destined for the parameter.
	IECore::StringAlgo::Substitutions substitutions = m_parameter->isInstanceOf( IECore::FileSequenceParameterTypeId ) ? IECore::StringAlgo::NoSubstitutions : IECore::StringAlgo::AllSubstitutions;

	// We also allow individual parameters to override the substitutions via userData
	if( const auto *gafferUserData = m_parameter->userData()->member<IECore::CompoundObject>( "gaffer" ) )
	{
		if( const auto *substitutionsUserData = gafferUserData->member<IECore::IntData>( "substitutions" ) )
		{
			substitutions = (IECore::StringAlgo::Substitutions)substitutionsUserData->readable();
		}
	}

	m_plug = plugParent->getChild<PlugType>( m_parameter->name() );
	if( !m_plug || m_plug->direction()!=direction || m_plug->substitutions()!=substitutions )
	{
		m_plug = createPlug( direction, substitutions );
		Gaffer::PlugAlgo::replacePlug( plugParent, m_plug );
	}

	setupPlugFlags( m_plug.get(), flags );

	return m_plug.get();
}

template<typename T>
Gaffer::Plug *TypedParameterHandler<T>::plug()
{
	return m_plug.get();
}

template<typename T>
const Gaffer::Plug *TypedParameterHandler<T>::plug() const
{
	return m_plug.get();
}

template<typename T>
void TypedParameterHandler<T>::setParameterValue()
{
	m_parameter->setTypedValue( m_plug->getValue() );
}

template<typename T>
void TypedParameterHandler<T>::setPlugValue()
{
	m_plug->setValue( m_parameter->getTypedValue() );
}

// explicit instantiations

template class GafferCortex::TypedParameterHandler<std::string>;
template class GafferCortex::TypedParameterHandler<bool>;

template class GafferCortex::TypedParameterHandler<Imath::Box2f>;
template class GafferCortex::TypedParameterHandler<Imath::Box3f>;

template class GafferCortex::TypedParameterHandler<Imath::Box2i>;
template class GafferCortex::TypedParameterHandler<Imath::Box3i>;

template class GafferCortex::TypedParameterHandler<Imath::V2f>;
template class GafferCortex::TypedParameterHandler<Imath::V3f>;

template class GafferCortex::TypedParameterHandler<Imath::V2i>;
template class GafferCortex::TypedParameterHandler<Imath::V3i>;

template class GafferCortex::TypedParameterHandler<Imath::Color3f>;
template class GafferCortex::TypedParameterHandler<Imath::Color4f>;

} // namespace Cortex
