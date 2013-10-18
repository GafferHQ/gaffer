import IECore
import GafferUI
import GafferScene
import GafferSceneUI
import os

scriptNode = script
scriptWindow = GafferUI.ScriptWindow.acquire( script )
ea = GafferUI.NodeGraph( scriptNode )
eb = GafferUI.NodeGraph( scriptNode )
layout = eval( "GafferUI.CompoundEditor( scriptNode, children = ( GafferUI.SplitContainer.Orientation.Horizontal, 0.65, ( {'tabs': (ea,), 'tabsVisible': True, 'currentTab': 0, 'pinned': [True]}, {'tabs': (eb,), 'tabsVisible': True, 'currentTab': 0, 'pinned': [True]} ) ) )" )



script.selection().add( script["ThisIsABox"] )
eb.graphGadget().setRoot( script["ThisIsABox"] )

scriptWindow.setLayout( layout )
scriptWindow._Widget__qtWidget.resize(925,450)

ea.frame([script["Backdrop"],script["ThisIsABox"]])
eb.frame([ script["ThisIsABox"]["Cube3"], script["ThisIsABox"]["Cube2"], script["ThisIsABox"]["Sphere5"], script["ThisIsABox"]["PathFilter1"] ])
