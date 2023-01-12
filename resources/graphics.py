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
				"pointerAdd",
				"pointerRemove",
				"pointerRotate",
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
				'catalogueStatusInteractiveRenderRunning',

				'catalogueOutputHeader',
				'catalogueOutput1',
				'catalogueOutput2',
				'catalogueOutput3',
				'catalogueOutput4',
				'catalogueOutput1Highlighted',
				'catalogueOutput2Highlighted',
				'catalogueOutput3Highlighted',
				'catalogueOutput4Highlighted',
				'catalogueOutput1HighlightedTransparent',
				'catalogueOutput2HighlightedTransparent',
				'catalogueOutput3HighlightedTransparent',
				'catalogueOutput4HighlightedTransparent',
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
				'soloChannel3',
				'soloChannel-2',
			]

		},

		"imageButtonIcons" : {

			"options" : {
				"requiredWidth" : 13,
				"requiredHeight" : 13,
				"validatePixelAlignment" : True
			},

			"ids" : [
				'compareModeNone',
				'compareModeReplace',
				'compareModeOver',
				'compareModeUnder',
				'compareModeDifference',
				'compareModeSideBySide',
				'wipeDisabled',
				'wipeEnabled',
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

		},

		"tabIcons" : {

			"ids" : [
				"tabScrollMenu",
				"deleteSmall",
			],

		},

		"colorInspectorIcons" : {

			"options" : {
				"requiredWidth" : 16,
				"requiredHeight" : 16,
				"validatePixelAlignment" : True
			},

			"ids" : [
				'sourceCursor',
				'sourceArea',
				'sourcePixel'
			]

		},

		"graphEditor" : {

			"options" : {
				"requiredWidth" : 25,
				"requiredHeight" : 25,
				"validatePixelAlignment" : True
			},

			"ids" : [
				"annotations",
			],

		},

		"plugValueWidgetIcons" : {

			"options" : {
				"validatePixelAlignment" : True
			},

			"ids" : [
				"colorPlugValueWidgetSlidersOff",
				"colorPlugValueWidgetSlidersOn",
			]

		},

		"lightEditor" : {

			"options" : {
				"requiredWidth" : 16,
				"requiredHeight" : 16,
				"validatePixelAlignment" : True
			},

			"ids" : [
				"pointLight",
				"diskLight",
				"quadLight",
				"cylinderLight",
				"spotLight",
				"distantLight",
				"environmentLight",
				"meshLight",
				"photometricLight",
				"emptyLocation",
				"muteLight",
				"unMuteLight",
				"muteLightFaded",
				"unMuteLightFaded",
				"muteLightHighlighted",
				"unMuteLightHighlighted",
				"muteLightFadedHighlighted",
				"unMuteLightFadedHighlighted",
				"muteLightUndefined",
			]
		},

		"tweakModes" : {

			"options" : {
				"requiredWidth" : 14,
				"requiredHeight" : 14,
				"validatePixelAlignment" : True
			},

			"ids" : [
				"plusSmall",
				"minusSmall",
				"multiplySmall",
				"replaceSmall",
				"createSmall",
				"lessThanSmall",
				"greaterThanSmall",
				"listAppendSmall",
				"listPrependSmall",
				"listRemoveSmall",
				"removeSmall",
			]
		},

		"menu" : {

			"options" : {
				"validatePixelAlignment" : True
			},

			"ids" : [
				"menuBreadCrumb",
				"menuChecked",
				"menuIndicator",
				"menuIndicatorDisabled",
			]
		},

		"hierarchyView" : {

			"options" : {
				"requiredWidth" : 16,
				"requiredHeight" : 16,
				"validatePixelAlignment" : True
			},

			"ids" : [
				"descendantExcluded",
				"descendantIncluded",
				"descendantIncludedTransparent",
				"locationExcluded",
				"locationExcludedHighlighted",
				"locationExcludedHighlightedTransparent",
				"locationExcludedTransparent",
				"locationExpanded",
				"locationIncluded",
				"locationIncludedDisabled",
				"locationIncludedHighlighted",
				"locationIncludedHighlightedTransparent",
				"locationIncludedTransparent",
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
		'minus',
		'navigationArrow',
		'nodeSetNodeSelection',
		'nodeSetNumericBookmarkSet',
		'nodeSetStandardSet',
		'nodeSetFocusNode',
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
		'viewerSelectPrompt',
		'viewerFocusPrompt',
		'clearSearch',
		'lutGPU',
		'lutCPU',
		'editDisabled',
		'editOff',
		'editOn',
		'focusOn',
		'focusOff',
		'focusOnHover',
		'focusOffHover'
	]
}
