//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#pragma once

#include "GafferImage/Format.h"
#include "GafferImage/TypeIds.h"

#include "Gaffer/BoxPlug.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( ScriptNode )
IE_CORE_FORWARDDECLARE( Context )

} // namespace Gaffer

namespace GafferImage
{

/// Compound plug for representing an image format in a way
/// easily edited by users, with individual child plugs for
/// each aspect of the format.
class GAFFERIMAGE_API FormatPlug : public Gaffer::ValuePlug
{

	public :

		using ValueType = Format;

		GAFFER_PLUG_DECLARE_TYPE( GafferImage::FormatPlug, FormatPlugTypeId, Gaffer::ValuePlug );

		FormatPlug(
			const std::string &name = defaultName<FormatPlug>(),
			Direction direction=In,
			Format defaultValue = Format(),
			unsigned flags = Default
		);

		~FormatPlug() override;

		/// Accepts no children following construction.
		bool acceptsChild( const GraphComponent *potentialChild ) const override;
		Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

		Gaffer::Box2iPlug *displayWindowPlug();
		const Gaffer::Box2iPlug *displayWindowPlug() const;

		Gaffer::FloatPlug *pixelAspectPlug();
		const Gaffer::FloatPlug *pixelAspectPlug() const;

		Format defaultValue() const;

		/// \undoable
		void setValue( const Format &value );
		/// Implemented to substitute in the default format from the current
		/// context if the current value is empty.
		/// \note Substitution is not performed automatically when accessing
		/// individual components (display window and pixel aspect) from the
		/// child plugs directly.
		Format getValue() const;

		/// Reimplemented to account for the substitutions performed in getValue().
		IECore::MurmurHash hash() const override;
		/// Ensures the method above doesn't mask
		/// ValuePlug::hash( h )
		using ValuePlug::hash;

		/// @name Default format
		///
		/// The FormatPlug provides the concept of a default format - one which
		/// will be used automatically wherever a FormatPlug contains an empty
		/// (default constructed) value. The default format is specified via a
		/// context variable, so the same node graph may be evaluated with
		/// different defaults in different contexts.
		///
		/// To expose this mechanism to user control, a default format may be
		/// specified for each script via a plug on the ScriptNode itself.
		////////////////////////////////////////////////////////////////////
		//@{
		/// Returns the default format in effect for the specified context.
		static Format getDefaultFormat( const Gaffer::Context *context );
		/// Sets the default format for the specified context.
		static void setDefaultFormat( Gaffer::Context *context, const Format &format );
		/// Acquires (creating if necessary) a plug which the user can use
		/// to specify the default format for a particular script. When the
		/// value of this plug is changed, the default format within
		/// ScriptNode::context() will be updated automatically.
		static FormatPlug *acquireDefaultFormatPlug( Gaffer::ScriptNode *scriptNode );
		//@}

	private :

		void parentChanging( Gaffer::GraphComponent *newParent ) override;
		void plugDirtied( Gaffer::Plug *plug );

		Gaffer::Signals::ScopedConnection m_plugDirtiedConnection;

};

IE_CORE_DECLAREPTR( FormatPlug );

} // namespace GafferImage
