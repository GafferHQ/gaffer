##########################################################################
#
#  Internationalisation startup script.
#
#  Configures the i18n system based on system locale or GAFFER_LANG
#  environment variable. This uses the standard GAFFER_STARTUP_PATHS
#  mechanism — no separate configuration file is needed.
#
#  To override the language, set the environment variable before
#  launching Gaffer:
#
#      GAFFER_LANG=es gaffer
#
#  If GAFFER_LANG is not set, the system locale is used automatically.
#  If the system locale is not supported, English is used as fallback.
#
##########################################################################

import Gaffer
import GafferUI
from GafferUI import i18n as _i18n

# ---------------------------------------------------------------------------
# Register language preference in Preferences node
# ---------------------------------------------------------------------------

preferences = application.root()["preferences"]

preferences["language"] = Gaffer.Plug()

preferences["language"]["uiLanguage"] = Gaffer.StringPlug(
	defaultValue = "en"
)

# Set current value from the detected language
preferences["language"]["uiLanguage"].setValue( _i18n.language() )

# ---------------------------------------------------------------------------
# Metadata – layout section and widget types
# ---------------------------------------------------------------------------

Gaffer.Metadata.registerValue(
	preferences["language"], "plugValueWidget:type",
	"GafferUI.LayoutPlugValueWidget", persistent = False
)
Gaffer.Metadata.registerValue(
	preferences["language"], "layout:section",
	"Language", persistent = False
)

# UI language dropdown via presets
Gaffer.Metadata.registerValue(
	preferences["language"]["uiLanguage"], "plugValueWidget:type",
	"GafferUI.PresetsPlugValueWidget", persistent = False
)
Gaffer.Metadata.registerValue(
	preferences["language"]["uiLanguage"], "label",
	"UI Language", persistent = False
)
Gaffer.Metadata.registerValue(
	preferences["language"]["uiLanguage"], "preset:English", "en",
	persistent = False
)
Gaffer.Metadata.registerValue(
	preferences["language"]["uiLanguage"], "preset:Español", "es",
	persistent = False
)

# ---------------------------------------------------------------------------
# Restart notification on language change
# ---------------------------------------------------------------------------

__initialising = True

def __languagePlugDirtied( plug ) :

	global __initialising
	if __initialising :
		return

	if plug != preferences["language"]["uiLanguage"] :
		return

	lang = preferences["language"]["uiLanguage"].getValue()
	if lang != _i18n.language() :
		dialogue = GafferUI.Dialogue( "Language Changed" )
		dialogue._setWidget(
			GafferUI.Label(
				"The language change will take effect after restarting Gaffer."
			)
		)
		closeButton = dialogue._addButton( "OK" )
		closeButton.clickedSignal().connect(
			lambda button : button.ancestor( GafferUI.Window ).setVisible( False )
		)
		dialogue.setVisible( True )

preferences.plugDirtiedSignal().connect(
	__languagePlugDirtied
)

__initialising = False
