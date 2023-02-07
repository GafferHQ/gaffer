##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

import unittest
import imath

import IECore

import Gaffer
from GafferSceneUI import _GafferSceneUI
import GafferScene
import GafferSceneUI
import GafferSceneTest
import GafferUITest


class LightEditorTest( GafferUITest.TestCase ) :

	def testMuteToggle( self ) :

		# Scene Hierarchy
		#  /
		#  /groupMute
		#  /groupMute/Mute
		#  /groupMute/UnMute
		#  /groupMute/None
		#  /groupUnMute
		#  /groupUnMute/Mute
		#  /groupUnMute/UnMute
		#  /groupUnMute/None
		#  /Mute
		#  /UnMute
		#  /None

		script = Gaffer.ScriptNode()

		script["parent"] = GafferScene.Parent()
		script["parent"]["parent"].setValue( "/" )

		for parent in [ "groupMute", "groupUnMute", None ] :
			for child in [ "Mute", "UnMute", None ] :
				childNode = GafferSceneTest.TestLight()
				childNode["name"].setValue( child or "None" )
				script.addChild( childNode )

				if parent is not None :
					if parent not in script :
						script[parent] = GafferScene.Group()
						script[parent]["name"].setValue( parent )
						script["parent"]["children"][len( script["parent"]["children"].children() ) - 1 ].setInput( script[parent]["out"] )

					script[parent]["in"][len( script[parent]["in"].children() ) - 1].setInput( childNode["out"] )
				else :
					script["parent"]["children"][len( script["parent"]["children"].children() ) - 1].setInput( childNode["out"] )

		def resetEditScope() :
			script["editScope"] = Gaffer.EditScope()
			script["editScope"].setup( script["parent"]["out"] )
			script["editScope"]["in"].setInput( script["parent"]["out"] )

			for state in ["Mute", "UnMute"] :

				# group*
				edit = GafferScene.EditScopeAlgo.acquireAttributeEdit(
					script["editScope"],
					f"/group{state}",
					"light:mute",
					createIfNecessary = True
				)
				edit["mode"].setValue(Gaffer.TweakPlug.Mode.Create)
				edit["value"].setValue( state == "Mute" )
				edit["enabled"].setValue( True )

				# group*/Mute
				edit = GafferScene.EditScopeAlgo.acquireAttributeEdit(
					script["editScope"],
					f"/group{state}/Mute",
					"light:mute",
					createIfNecessary = True
				)
				edit["mode"].setValue(Gaffer.TweakPlug.Mode.Create)
				edit["value"].setValue( True )
				edit["enabled"].setValue( True )

				# group*/UnMute
				edit = GafferScene.EditScopeAlgo.acquireAttributeEdit(
					script["editScope"],
					f"/group{state}/UnMute",
					"light:mute",
					createIfNecessary = True
				)
				edit["mode"].setValue(Gaffer.TweakPlug.Mode.Create)
				edit["value"].setValue( False )
				edit["enabled"].setValue( True )

				# light
				edit = GafferScene.EditScopeAlgo.acquireAttributeEdit(
					script["editScope"],
					f"/{state}",
					"light:mute",
					createIfNecessary = True
				)
				edit["mode"].setValue(Gaffer.TweakPlug.Mode.Create)
				edit["value"].setValue( state == "Mute" )
				edit["enabled"].setValue( True )

			script.setFocus( script["editScope"] )

		# Tests against a given state, which is a dictionary of the form :
		# { "sceneLocation" : ( attributesMuteValue, fullAttributesMuteValue ), ... }
		def testLightMuteAttribute( toggleCount, toggleLocation, newStates ) :

			for location in [
				"/groupMute",
				"/groupMute/Mute",
				"/groupMute/UnMute",
				"/groupMute/None",
				"/groupUnMute",
				"/groupUnMute/Mute",
				"/groupUnMute/UnMute",
				"/groupUnMute/None",
				"/Mute",
				"/UnMute",
				"/None",
			] :
				attributes = script["editScope"]["out"].attributes( location )
				fullAttributes = script["editScope"]["out"].fullAttributes( location )

				muteAttribute, fullMuteAttribute = newStates[location]

				with self.subTest( f"(attributes) Toggle {toggleCount} = {toggleLocation}", location = location ) :
					if muteAttribute is not None :
						self.assertIn( "light:mute", attributes )
						self.assertEqual( attributes["light:mute"].value, muteAttribute )
					else :
						self.assertNotIn( "light:mute", attributes )
				with self.subTest( f"(fullAttributes) Toggle {toggleCount} = {toggleLocation}", location = location ) :
					if fullMuteAttribute is not None :
						self.assertIn( "light:mute", fullAttributes )
						self.assertEqual( fullAttributes["light:mute"].value, fullMuteAttribute)
					else :
						self.assertNotIn( "light:mute", fullAttributes )

		initialState = {
			"/groupMute" : ( True, True ),
			"/groupMute/Mute" : ( True, True ),
			"/groupMute/UnMute" : ( False, False ),
			"/groupMute/None" : ( None, True ),
			"/groupUnMute" : ( False, False ),
			"/groupUnMute/Mute" : ( True, True ),
			"/groupUnMute/UnMute" : ( False, False ),
			"/groupUnMute/None" : ( None, False ),
			"/Mute" : ( True, True ),
			"/UnMute" : ( False, False ),
			"/None" : ( None, None ),
		}

		resetEditScope()
		testLightMuteAttribute( 0, "none", initialState )

		# dictionary of the form :
		# {
		#     ( "toggleLocation0", "toggleLocation1", ... ) : (
		#         firstToggleMuteState,
		#         secondToggleMuteState
		#     ),
		#     ...
		# }
		toggles = {
			( "/groupMute", ) : (
				{
					"/groupMute" : ( False, False ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, False ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				},
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				}
			),
			( "/groupMute/Mute", ) : (
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( False, False ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				},
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				}
			),
			( "/groupMute/UnMute", ) : (
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( True, True ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				},
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				}
			),
			( "/groupMute/None", ) : (
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( False, False ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				},
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( True, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				}
			),
			( "/groupUnMute", ) : (
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( True, True ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, True ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				},
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				}
			),
			( "/groupUnMute/Mute", ) : (
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( False, False ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				},
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				}
			),
			( "/groupUnMute/UnMute", ) : (
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( True, True ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				},
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				}
			),
			( "/groupUnMute/None", ) : (
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( True, True ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				},
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( False, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				}
			),
			( "/Mute", ) : (
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( False, False ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				},
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				}
			),
			( "/UnMute", ) : (
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( True, True ),
					"/None" : ( None, None ),
				},
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				}
			),
			( "/None", ) : (
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( True, True ),
				},
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( False, False ),
				}
			),
			( "/Mute", "/UnMute", ) : (
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : (True, True ),
					"/None" : ( None, None ),
				},
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( False, False ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				}
			),
			( "/UnMute", "/None", ) : (
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( True, True ),
					"/None" : ( True, True ),
				},
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( False, False ),
				}
			),
			( "/groupMute", "/groupMute/Mute" ) : (
				{
					"/groupMute" : ( False, False ),
					"/groupMute/Mute" : ( False, False ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, False ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				},
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				}
			),
			( "/groupMute", "/groupMute/UnMute" ) : (
				{
					"/groupMute" : ( True, True ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( True, True ),
					"/groupMute/None" : ( None, True ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				},
				{
					"/groupMute" : ( False, False ),
					"/groupMute/Mute" : ( True, True ),
					"/groupMute/UnMute" : ( False, False ),
					"/groupMute/None" : ( None, False ),
					"/groupUnMute" : ( False, False ),
					"/groupUnMute/Mute" : ( True, True ),
					"/groupUnMute/UnMute" : ( False, False ),
					"/groupUnMute/None" : ( None, False ),
					"/Mute" : ( True, True ),
					"/UnMute" : ( False, False ),
					"/None" : ( None, None ),
				}
			)
		}

		muteIndex = None

		for togglePaths, toggleData in toggles.items() :

			firstNewStates, secondNewStates = toggleData

			resetEditScope()
			editor = GafferSceneUI.LightEditor( script )
			editor._LightEditor__settingsNode["editScope"].setInput( script["editScope"]["out"] )

			widget = editor._LightEditor__pathListing
			columns = widget.getColumns()

			if muteIndex is None :
				for i, c in zip( range( 0, len( columns ) ), columns ) :
					if isinstance( c, _GafferSceneUI._LightEditorMuteColumn ) :
						muteIndex = i

			self.assertIsNotNone( muteIndex )

			selection = [ IECore.PathMatcher() for i in range( 0, len( columns ) ) ]
			for path in togglePaths :
				selection[muteIndex].addPath( path )

			widget.setSelection( selection )

			editor._LightEditor__editSelectedCells( widget )
			testLightMuteAttribute( 1, togglePaths, firstNewStates )

			editor._LightEditor__editSelectedCells( widget )
			testLightMuteAttribute( 2, togglePaths, secondNewStates )

			del widget, editor


if __name__ == "__main__" :
	unittest.main()
