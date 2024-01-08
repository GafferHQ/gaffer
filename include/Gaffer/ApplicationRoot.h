//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/ScriptNode.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Preferences )

/// \todo Derive from Node and merge with `Gaffer.Application`,
/// using `Gaffer::Plugs` instead of `IECore::Parameters` to
/// provide command-line arguments.
class GAFFER_API ApplicationRoot : public GraphComponent
{

	public :

		explicit ApplicationRoot( const std::string &name = defaultName<ApplicationRoot>() );
		~ApplicationRoot() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( Gaffer::ApplicationRoot, ApplicationRootTypeId, GraphComponent );

		/// Accepts no user added children.
		bool acceptsChild( const GraphComponent *potentialChild ) const override;
		/// Accepts no parent.
		bool acceptsParent( const GraphComponent *potentialParent ) const override;

		ScriptContainer *scripts();
		const ScriptContainer *scripts() const;

		//! @name Clipboard
		/// The ApplicationRoot class holds a clipboard which is
		/// shared by all ScriptNodes belonging to the application.
		/// The cut, copy and paste methods of the ScriptNodes
		/// operate using this central clipboard. The contents of the
		/// clipboard is simply stored as an IECore::Object.
		////////////////////////////////////////////////////////
		//@{
		/// Returns the clipboard contents, a copy should be taken
		/// if it must be modified.
		const IECore::Object *getClipboardContents() const;
		/// Sets the clipboard contents - a copy of clip is taken.
		void setClipboardContents( const IECore::Object *clip );
		/// A signal emitted when the clipboard contents have changed.
		using ClipboardSignal = Signals::Signal<void (ApplicationRoot *), Signals::CatchingCombiner<void>>;
		ClipboardSignal &clipboardContentsChangedSignal();
		//@}

		//! @name Preferences
		/// User preferences are represented as Plugs on a centrally
		/// held Node. During application startup plugs should be added
		/// to represent all available options. The plugSetSignal() may
		/// then be used to respond to user changes. The ApplicationRoot
		/// class provides access to the preferences node and also functions
		/// for saving the current preferences to disk and reloading them.
		/// Note that saving and loading is only supported on ApplicationRoots
		/// created from Python - this allows the main C++ library to avoid
		/// a python dependency.
		//@{
		/// Returns the preferences node.
		Preferences *preferences();
		const Preferences *preferences() const;
		/// Saves the current preferences to preferencesLocation()/preferences.py.
		void savePreferences() const;
		/// Saves the current preferences value to the specified file.
		virtual void savePreferences( const std::filesystem::path &fileName ) const;
		/// Returns the directory in which application preferences are stored,
		/// ensuring that it exists. Other application components may use this
		/// location to store settings they wish to persist across invocations.
		std::filesystem::path preferencesLocation() const;
		//@}

	private :

		std::filesystem::path defaultPreferencesFileName() const;

		IECore::ObjectPtr m_clipboardContents;
		ClipboardSignal m_clipboardContentsChangedSignal;

};

IE_CORE_DECLAREPTR( ApplicationRoot );

} // namespace Gaffer
