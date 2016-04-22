import IECore
import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI
import os
scriptNode = script
scriptWindow = GafferUI.ScriptWindow.acquire( script )
ea = GafferUI.NodeEditor( scriptNode )
eb = GafferUI.NodeEditor( scriptNode )
layout = eval( "GafferUI.CompoundEditor( scriptNode, children = ( GafferUI.SplitContainer.Orientation.Horizontal, 0.5, ( {'tabs': (ea,), 'tabsVisible': True, 'currentTab': 0, 'pinned': [True]}, {'tabs': (eb,), 'tabsVisible': True, 'currentTab': 0, 'pinned': [True]} ) ) )" )

ea.setNodeSet( Gaffer.StandardSet( [ script["ExampleNode"] ] ) )
eb.setNodeSet( Gaffer.StandardSet( [ script["PathFilter"] ] ) )


scriptWindow.setLayout( layout )
scriptWindow._Widget__qtWidget.resize(900,375)

