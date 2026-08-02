//////////////////////////////////////////////////////////////////////////
//
//  Copyright ( c ) 2025, Lucien Fostier. All rights reserved.
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
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES ( INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION ) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT ( INCLUDING
//  NEGLIGENCE OR OTHERWISE ) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

#pragma once

#include "GafferOFX/EffectImageInstance.h"

#include "HostSupport/ofxhParam.h"

namespace GafferOFX
{

class PushbuttonInstance : public OFX::Host::Param::PushbuttonInstance
{
	protected : 
		GafferOFX::EffectImageInstance*   m_effect;
		OFX::Host::Param::Descriptor& m_descriptor;
	public :
		PushbuttonInstance( GafferOFX::EffectImageInstance* effect, const std::string& name, OFX::Host::Param::Descriptor& descriptor );
};


class IntegerInstance : public OFX::Host::Param::IntegerInstance
{
	protected : 
		GafferOFX::EffectImageInstance*   m_effect;
		OFX::Host::Param::Descriptor& m_descriptor;
	public :
		IntegerInstance( GafferOFX::EffectImageInstance* effect, const std::string& name, OFX::Host::Param::Descriptor& descriptor );
		OfxStatus get( int& ) override;
		OfxStatus get( OfxTime time, int& ) override;
		OfxStatus set( int ) override;
		OfxStatus set( OfxTime time, int ) override;
};

class DoubleInstance : public OFX::Host::Param::DoubleInstance
{
	protected : 
		GafferOFX::EffectImageInstance*   m_effect;
		OFX::Host::Param::Descriptor& m_descriptor;
	public :
		DoubleInstance( GafferOFX::EffectImageInstance* effect, const std::string& name, OFX::Host::Param::Descriptor& descriptor );
		OfxStatus get( double& ) override;
		OfxStatus get( OfxTime time, double& ) override;
		OfxStatus set( double ) override;
		OfxStatus set( OfxTime time, double ) override;
		OfxStatus derive( OfxTime time, double& ) override;
		OfxStatus integrate( OfxTime time1, OfxTime time2, double& ) override;
};

class BooleanInstance : public OFX::Host::Param::BooleanInstance
{
	protected : 
		GafferOFX::EffectImageInstance*   m_effect;
		OFX::Host::Param::Descriptor& m_descriptor;
	public :
		BooleanInstance( GafferOFX::EffectImageInstance* effect, const std::string& name, OFX::Host::Param::Descriptor& descriptor );
		OfxStatus get( bool& ) override;
		OfxStatus get( OfxTime time, bool& ) override;
		OfxStatus set( bool ) override;
		OfxStatus set( OfxTime time, bool ) override;
};

class ChoiceInstance : public OFX::Host::Param::ChoiceInstance
{
	protected : 
		GafferOFX::EffectImageInstance*   m_effect;
		OFX::Host::Param::Descriptor& m_descriptor;
	public :
		ChoiceInstance( GafferOFX::EffectImageInstance* effect,  const std::string& name, OFX::Host::Param::Descriptor& descriptor );
		OfxStatus get( int& ) override;
		OfxStatus get( OfxTime time, int& ) override;
		OfxStatus set( int ) override;
		OfxStatus set( OfxTime time, int ) override;
};

class RGBAInstance : public OFX::Host::Param::RGBAInstance
{
	protected : 
		GafferOFX::EffectImageInstance*   m_effect;
		OFX::Host::Param::Descriptor& m_descriptor;
	public :
		RGBAInstance( GafferOFX::EffectImageInstance* effect, const std::string& name, OFX::Host::Param::Descriptor& descriptor );
		OfxStatus get( double&, double&, double&, double& ) override;
		OfxStatus get( OfxTime time,  double&, double&, double&, double& ) override;
		OfxStatus set( double, double, double, double ) override;
		OfxStatus set( OfxTime time,  double, double, double, double ) override;
};


class RGBInstance : public OFX::Host::Param::RGBInstance
{
	protected : 
		GafferOFX::EffectImageInstance*   m_effect;
		OFX::Host::Param::Descriptor& m_descriptor;
	public :
		RGBInstance( GafferOFX::EffectImageInstance* effect, const std::string& name, OFX::Host::Param::Descriptor& descriptor );
		OfxStatus get( double&, double&, double& ) override;
		OfxStatus get( OfxTime time, double&, double&, double& ) override;
		OfxStatus set( double, double, double ) override;
		OfxStatus set( OfxTime time,  double, double, double ) override;
};

class Double2DInstance : public OFX::Host::Param::Double2DInstance
{
	protected : 
		GafferOFX::EffectImageInstance*   m_effect;
		OFX::Host::Param::Descriptor& m_descriptor;
	public :
		Double2DInstance( GafferOFX::EffectImageInstance* effect, const std::string& name, OFX::Host::Param::Descriptor& descriptor );
		OfxStatus get( double&, double& ) override;
		OfxStatus get( OfxTime time, double&, double& ) override;
		OfxStatus set( double, double ) override;
		OfxStatus set( OfxTime time, double, double ) override;
};

class Integer2DInstance : public OFX::Host::Param::Integer2DInstance
{
	protected : 
		GafferOFX::EffectImageInstance*   m_effect;
		OFX::Host::Param::Descriptor& m_descriptor;
	public :
		Integer2DInstance( GafferOFX::EffectImageInstance* effect,  const std::string& name, OFX::Host::Param::Descriptor& descriptor );
		OfxStatus get( int&, int& ) override;
		OfxStatus get( OfxTime time, int&, int& ) override;
		OfxStatus set( int, int ) override;
		OfxStatus set( OfxTime time, int, int ) override;
};

class Double3DInstance : public OFX::Host::Param::Double3DInstance
{
	protected : 
		GafferOFX::EffectImageInstance*   m_effect;
		OFX::Host::Param::Descriptor& m_descriptor;
	public :
		Double3DInstance( GafferOFX::EffectImageInstance* effect, const std::string& name, OFX::Host::Param::Descriptor& descriptor );
		OfxStatus get( double&, double&, double& ) override;
		OfxStatus get( OfxTime time, double&, double&, double& ) override;
		OfxStatus set( double, double, double ) override;
		OfxStatus set( OfxTime time, double, double, double ) override;
};

class Integer3DInstance : public OFX::Host::Param::Integer3DInstance
{
	protected : 
		GafferOFX::EffectImageInstance*   m_effect;
		OFX::Host::Param::Descriptor& m_descriptor;
	public :
		Integer3DInstance( GafferOFX::EffectImageInstance* effect,  const std::string& name, OFX::Host::Param::Descriptor& descriptor );
		OfxStatus get( int&, int&, int& ) override;
		OfxStatus get( OfxTime time, int&, int&, int& ) override;
		OfxStatus set( int, int, int ) override;
		OfxStatus set( OfxTime time, int, int, int ) override;
};

class StringInstance : public OFX::Host::Param::StringInstance
{
	protected : 
		GafferOFX::EffectImageInstance*   m_effect;
		OFX::Host::Param::Descriptor& m_descriptor;
		mutable std::string m_returnValue;
	public :
		StringInstance( GafferOFX::EffectImageInstance* effect,  const std::string& name, OFX::Host::Param::Descriptor& descriptor );
		OfxStatus get( std::string& ) override;
		OfxStatus get( OfxTime time, std::string& ) override;
		OfxStatus set( const char* ) override;
		OfxStatus set( OfxTime time, const char* ) override;

		// Override getV to use our own m_returnValue instead of
		// the HostSupport's _returnValue, which may be at a wrong
		// offset due to std::string ABI differences between libraries.
		OfxStatus getV( va_list arg ) override;
		OfxStatus getV( OfxTime time, va_list arg ) override;
};

}

