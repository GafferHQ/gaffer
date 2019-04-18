import Gaffer
import GafferUI

GafferUI.Examples.registerExample(
	"Box Basics",
	"$GAFFER_ROOT/resources/examples/boxBasics.gfr",
	description = """
	Demonstrates the use of the Box node with custom plugs to construct re-usable
	and configurable tools.
	""",
	notableNodes = [
		Gaffer.Box
	]
)
