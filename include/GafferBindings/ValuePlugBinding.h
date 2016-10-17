//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERBINDINGS_VALUEPLUGBINDING_H
#define GAFFERBINDINGS_VALUEPLUGBINDING_H

#include "Gaffer/ValuePlug.h"
#include "GafferBindings/PlugBinding.h"

namespace GafferBindings
{

void bindValuePlug();

/// Supports the following Context variables :
///
/// "valuePlugSerialiser:resetParentPlugDefaults"
///
/// :	Replaces the default value with the current value for plugs
///     of the parent node. This is used when exporting the contents
///     of a Box node.
class ValuePlugSerialiser : public PlugSerialiser
{

	public :

		virtual void moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules, const Serialisation &serialisation ) const;
		virtual std::string constructor( const Gaffer::GraphComponent *graphComponent, const Serialisation &serialisation ) const;
		virtual std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const;

		static std::string repr( const Gaffer::ValuePlug *plug, unsigned flagsMask = Gaffer::Plug::All, const std::string &extraArguments = "", const Serialisation *serialisation = NULL );

	protected :

		/// May be implemented by derived classes to control whether or not a setValue() call is emitted by postConstructor().
		/// The default implementation returns true only for input plugs without an incoming connection.
		virtual bool valueNeedsSerialisation( const Gaffer::ValuePlug *plug, const Serialisation &serialisation ) const;

};

} // namespace GafferBindings

#endif // GAFFERBINDINGS_VALUEPLUGBINDING_H
