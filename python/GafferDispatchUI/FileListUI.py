##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import functools

import Gaffer
import GafferUI
import GafferDispatch

Gaffer.Metadata.registerNode(

	GafferDispatch.FileList,

	"description",
	"""
	Searches the filesystem for files matching certain criteria,
	and outputs a list of the file paths.
	""",

	"nodeGadget:type", "GafferUI::AuxiliaryNodeGadget",
	"auxiliaryNodeGadget:label", "f",
	"nodeGadget:focusGadgetVisible", False,

	plugs = {

		"*" : {

			"nodule:type" : "",

		},

		"directory" : {

			"description" :
			"""
			The directory in which to search for files. By default, all files
			in the directory will be returned. Use the `filePatterns` and
			`fileExtensions` plugs to filter the files.
			""",

			"plugValueWidget:type" : "GafferUI.FileSystemPathPlugValueWidget",

		},

		"refreshCount" : {

			"description" :
			"""
			May be incremented to force a fresh search, taking into account
			any changes to the filesystem that have occurred since the
			previous one.
			""",

			"plugValueWidget:type" : "GafferUI.RefreshPlugValueWidget",
			"layout:label" : "",
			"layout:accessory" : True,

		},

		"inclusions" : {

			"description" :
			"""
			A space-separated list of patterns used to filter the file
			list. Only filenames matching the patterns are included in
			the output. The following wildcards are available :

			- `*` : Matches any sequence of characters, except `/`.
			- `?` : Matches any single character.
			- `[A-Z]` : Matches any single character in the specified range.
			- `...` : Matches any number of subdirectories.

			Examples :

			- `*` : Matches all files in the directory.
			- `test*` : Matches all files starting with `test`.
			- `imageFiles/*` : Matches all files in an `imageFiles` subdirectory.
			- `imageFiles/.../*` : Matches recursively, finding all files in all
			  subdirectories of `imageFiles`.
			""",

		},

		"exclusions" : {

			"description" :
			"""
			A space-separated list of patterns used to exclude files from the
			list. Supports the same wildcards as `inclusions`.
			""",

		},

		"extensions" : {

			"description" :
			"""
			A list of file extensions to filter on. Extension comparison
			is case-insensitive.
			""",

			"preset:All" : "*",

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"presetsPlugValueWidget:allowCustom" : True,

		},

		"searchSubdirectories" : {

			"description" :
			"""
			Extends the search to all subdirectories of `directory`.
			Equivalent to prefixing all `inclusions` and `exclusions`
			with `.../`.
			""",

		},

		"absolute" : {

			"description" :
			"""
			Outputs absolute paths. When off, the output paths are relative
			to the `directory`.
			""",

		},

		"sequenceMode" : {

			"description" :
			"""
			Defines how frame sequences are treated. A frame sequence is a group of files
			whose names differ only in their frame number.

			- Files : All files are listed. Files from frame sequences are listed individually.
			- Sequences : Files from each frame sequence are listed as a single path containing
			  `#` characters representing the frame numbers. Files not from a frame sequence are omitted.
			- FilesAndSequences : As for Sequences mode, but also including files not in any frame sequence.
			""",

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"preset:Files" : GafferDispatch.FileList.SequenceMode.Files,
			"preset:Sequences" : GafferDispatch.FileList.SequenceMode.Sequences,
			"preset:Files And Sequences" : GafferDispatch.FileList.SequenceMode.FilesAndSequences,

		},

		"out" : {

			"description" :
			"""
			The list of all files found by the node.
			""",

			"layout:section" : "Files",
			"nodule:type" : "GafferUI::StandardNodule",

		}

	}

)

def __createFileList( plugs ) :

	parentNode = next( iter( plugs ) ).node().parent()

	with Gaffer.UndoScope( parentNode.scriptNode() ) :

		fileList = GafferDispatch.FileList()
		parentNode.addChild( fileList )

		for plug in plugs :
			plug.setInput( fileList["out"] )

	GafferUI.NodeEditor.acquire( fileList )

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	if not len( plugValueWidget.getPlugs() ) :
		return

	for plug in plugValueWidget.getPlugs() :
		if not Gaffer.Metadata.value( plug, "ui:acceptsFileList" ) :
			return
		if plug.getInput() is not None :
			return
		node = plug.node()
		if node is None or node.parent() is None :
			return

	menuDefinition.prepend( "/FileListDivider", { "divider" : True } )
	menuDefinition.prepend(
		"/Create File List...",
		{
			"command" : functools.partial( __createFileList, plugValueWidget.getPlugs() )
		}
	)

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )
