{
	# \todo Remove once all artwork has been aligned
	"options" : {
		"validatePixelAlignment" : False
	},

	"groups" : {

		"pointers" : {

			"options" : {
				"requiredWidth" : 32,
				"requiredHeight" : 32,
				"validatePixelAlignment" : True
			},

			"ids" : [
				"plug", # \todo prefix with 'pointer'
				"values", # \todo prefix with 'pointer'
				"rgba", # \todo prefix with 'pointer'
				"nodes", # \todo prefix with 'pointer'
				"paths", # \todo prefix with 'pointer'
				'pointerContextMenu',
				'pointerTab',
				'pointerDetachedPanel',
				"move", # \todo prefix with 'pointer'
				"moveHorizontally", # \todo prefix with 'pointer',
				"moveVertically", # \todo prefix with 'pointer'
				"moveDiagonallyDown", # \todo prefix with 'pointer'
				"moveDiagonallyUp", # \todo prefix with 'pointer'
				'pointerTarget',
				'pointerCrossHair',
			]
		},

		"pointers-pathFilterUI" : {

			"options" : {
				"requiredWidth" : 64,
				"requiredHeight" : 32,
				"validatePixelAlignment" : True
			},

			"ids" : [
				"objects", # \todo prefix with 'pointer'
				"addObjects", # \todo prefix with 'pointer'
				"removeObjects", # \todo prefix with 'pointer'
				"replaceObjects" # \todo prefix with 'pointer'
			]
		},

		"arrows-10x10" : {

			"options" : {
				"requiredWidth" : 10,
				"requiredHeight" : 10,
				"validatePixelAlignment" : True
			},

			"ids" : [
				'arrowDown10',
				'arrowUp10',
				'arrowLeft10',
				'arrowRight10',
				'arrowDownDisabled10',
				'arrowUpDisabled10',
				'arrowLeftDisabled10',
				'arrowRightDisabled10',
				'collapsibleArrowDown',
				'collapsibleArrowDownHover',
				'collapsibleArrowDownValueChanged',
				'collapsibleArrowRight',
				'collapsibleArrowRightHover',
				'collapsibleArrowRightValueChanged'
			]

		},

		"catalogueStatus" : {

			"options" : {
				"requiredWidth" : 13,
				"requiredHeight" : 13,
				"validatePixelAlignment" : True
			},

			"ids" : [
				'catalogueStatusBatchRenderComplete',
				'catalogueStatusBatchRenderRunning',
				'catalogueStatusDisk',
				'catalogueStatusDisplay',
				'catalogueStatusInteractiveRenderComplete',
				'catalogueStatusInteractiveRenderRunning'
			]

		},

		"sceneView" : {

			"options" : {
				"requiredWidth" : 25,
				"requiredHeight" : 25,
				"validatePixelAlignment" : True
			},

			"ids" : [
				'cameraOff',
				'cameraOn',
				'drawingStyles',
				'expansion',
				'grid', # \todo rename to 'sceneViewGadgets'
				'selectionMaskOff',
				'selectionMaskOn',
				'shading'
			]

		},

		"imageView" : {

			"options" : {
				"requiredWidth" : 25,
				"requiredHeight" : 25,
				"validatePixelAlignment" : True
			},

			"ids" : [
				'clippingOff',
				'clippingOn',
				'exposureOff',
				'exposureOn',
				'gammaOff',
				'gammaOn',
				'soloChannel-1',
				'soloChannel0',
				'soloChannel1',
				'soloChannel2',
				'soloChannel3'
			]

		},

		"tools" : {

			"options" : {
				"requiredWidth" : 25,
				"requiredHeight" : 25,
				"validatePixelAlignment" : True
			},

			"ids" : [
				'gafferSceneUISelectionTool',
				'gafferSceneUICameraTool',
				'gafferSceneUICropWindowTool',
				'gafferSceneUIRotateTool',
				'gafferSceneUIScaleTool',
				'gafferSceneUITranslateTool',
			]

		},

		"browserIcons" : {

			"options" : {
				"requiredWidth" : 14,
				"requiredHeight" : 14,
				"validatePixelAlignment" : True
			},

			"ids" : [
				'bookmarks',
				'pathChooser',
				'pathListingList',
				'pathListingTree',
				'pathUpArrow',
				'refresh'
			]

		},

		"controls-checkBox" : {

			"options" : {
				"requiredWidth" : 20,
				"requiredHeight" : 20,
				"validatePixelAlignment" : True
			},

			"ids" : [
				'checkBoxChecked',
				'checkBoxCheckedDisabled',
				'checkBoxCheckedHover',
				'checkBoxIndeterminate',
				'checkBoxIndeterminateDisabled',
				'checkBoxIndeterminateHover',
				'checkBoxUnchecked',
				'checkBoxUncheckedDisabled',
				'checkBoxUncheckedHover'
			]

		},

		"controls-switch" : {

			"options" : {
				"requiredWidth" : 16,
				"requiredHeight" : 16,
				"validatePixelAlignment" : True
			},

			"ids" : [
				'toggleIndeterminate',
				'toggleIndeterminateDisabled',
				'toggleIndeterminateHover',
				'toggleOff',
				'toggleOffDisabled',
				'toggleOffHover',
				'toggleOn',
				'toggleOnDisabled',
				'toggleOnHover'
			]

		},

		"viewer" : {

			"options" : {
				"requiredWidth" : 25,
				"requiredHeight" : 25,
				"validatePixelAlignment" : True
			},

			"ids" : [
				'viewPause',
				'viewPaused'
			]

		}

	},

	"ids" : [
		'bookmarkStar',
		'bookmarkStar2',
		'boxInNode',
		'boxNode',
		'boxOutNode',
		'classVectorParameterHandle',
		'debugNotification',
		'debugSmall',
		'delete',
		'deleteSmall',
		'duplicate',
		'editScopeNode',
		'editScopeProcessorNode',
		'errorNotification',
		'errorSmall',
		'export',
		'extract',
		'failure',
		'gadgetError',
		'gear',
		'headerSortDown',
		'headerSortUp',
		'info',
		'infoNotification',
		'infoSmall',
		'layoutButton',
		'localDispatcherStatusFailed',
		'localDispatcherStatusKilled',
		'localDispatcherStatusRunning',
		'menuChecked',
		'menuIndicator',
		'menuIndicatorDisabled',
		'minus',
		'navigationArrow',
		'nodeSetDriverNodeSelection',
		'nodeSetDriverNodeSet',
		'nodeSetDrivertestMode',
		'nodeSetNumericBookmarkSet',
		'nodeSetStandardSet',
		'nodeSetDriverFocusNode',
		'plugAdder',
		'plugAdderHighlighted',
		'plus',
		'railBottom',
		'railGap',
		'railLine',
		'railMiddle',
		'railSingle',
		'railTop',
		'referenceNode',
		'renderStop',
		'renderStart',
		'renderResume',
		'renderPause',
		'reorderVertically',
		'scene',
		'sceneInspectorHistory',
		'sceneInspectorInheritance',
		'search',
		'setMembershipDot',
		'shuffleArrow',
		'subMenuArrow',
		'success',
		'successWarning',
		'timeline1',
		'timeline2',
		'timeline3',
		'timelineEnd',
		'timelinePause',
		'timelinePlay',
		'timelineStart',
		'timelineStop',
		'valueChanged',
		'warningNotification',
		'warningSmall',
		'scrollToBottom',
		'searchFocusOn',
		'searchFocusOff',
		'clearSearch',
		'lutGPU',
		'lutCPU',
		'editDisabled',
		'editOff',
		'editOn'
	]
}
