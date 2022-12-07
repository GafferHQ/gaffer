/*!
 * Bootstrap v3.4.1 (https://getbootstrap.com/)
 * Copyright 2011-2019 Twitter, Inc.
 * Licensed under the MIT license
 */

if (typeof jQuery === 'undefined') {
    throw new Error('Bootstrap\'s JavaScript requires jQuery')
}
  
+function ($) {
    'use strict';
    var version = $.fn.jquery.split(' ')[0].split('.')
    if ((version[0] < 2 && version[1] < 9) || (version[0] == 1 && version[1] == 9 && version[2] < 1) || (version[0] > 3)) {
    throw new Error('Bootstrap\'s JavaScript requires jQuery version 1.9.1 or higher, but lower than version 4')
    }
}(jQuery);
  
  
/* ========================================================================
* Bootstrap: scrollspy.js v3.4.1
* https://getbootstrap.com/docs/3.4/javascript/#scrollspy
* ========================================================================
* Copyright 2011-2019 Twitter, Inc.
* Licensed under MIT (https://github.com/twbs/bootstrap/blob/master/LICENSE)
* ======================================================================== */

+function ($) {
    'use strict';

    // SCROLLSPY CLASS DEFINITION
    // ==========================

    function ScrollSpy(element, options) {
        this.$body          = $(document.body)
        this.$scrollElement = $(element).is(document.body) ? $(window) : $(element)
        this.options        = $.extend({}, ScrollSpy.DEFAULTS, options)
        this.selector       = (this.options.target || '') + ' .nav li > a'
        this.offsets        = []
        this.targets        = []
        this.activeTarget   = null
        this.scrollHeight   = 0

        this.$scrollElement.on('scroll.bs.scrollspy', $.proxy(this.process, this))
        this.refresh()
        this.process()
    }

    ScrollSpy.VERSION  = '3.4.1'

    ScrollSpy.DEFAULTS = {
        offset: 10
    }

    ScrollSpy.prototype.getScrollHeight = function () {
        return this.$scrollElement[0].scrollHeight || Math.max(this.$body[0].scrollHeight, document.documentElement.scrollHeight)
    }

    ScrollSpy.prototype.refresh = function () {
    var that          = this
    var offsetMethod  = 'offset'
    var offsetBase    = 0

    this.offsets      = []
    this.targets      = []
    this.scrollHeight = this.getScrollHeight()

    if (!$.isWindow(this.$scrollElement[0])) {
    offsetMethod = 'position'
    offsetBase   = this.$scrollElement.scrollTop()
    }

    this.$body
    .find(this.selector)
    .map(function () {
        var $el   = $(this)
        var href  = $el.data('target') || $el.attr('href')
        var $href = /^#./.test(href) && $(href)

        return ($href
        && $href.length
        && $href.is(':visible')
        && [[$href[offsetMethod]().top + offsetBase, href]]) || null
    })
    .sort(function (a, b) { return a[0] - b[0] })
    .each(function () {
        that.offsets.push(this[0])
        that.targets.push(this[1])
    })
}

ScrollSpy.prototype.process = function () {
    var scrollTop    = this.$scrollElement.scrollTop() + this.options.offset
    var scrollHeight = this.getScrollHeight()
    var maxScroll    = this.options.offset + scrollHeight - this.$scrollElement.height()
    var offsets      = this.offsets
    var targets      = this.targets
    var activeTarget = this.activeTarget
    var i

    if (this.scrollHeight != scrollHeight) {
    this.refresh()
    }

    if (scrollTop >= maxScroll) {
    return activeTarget != (i = targets[targets.length - 1]) && this.activate(i)
    }

    if (activeTarget && scrollTop < offsets[0]) {
    this.activeTarget = null
    return this.clear()
    }

    for (i = offsets.length; i--;) {
    activeTarget != targets[i]
        && scrollTop >= offsets[i]
        && (offsets[i + 1] === undefined || scrollTop < offsets[i + 1])
        && this.activate(targets[i])
    }
}

ScrollSpy.prototype.activate = function (target) {
    this.activeTarget = target

    this.clear()

    var selector = this.selector +
    '[data-target="' + target + '"],' +
    this.selector + '[href="' + target + '"]'

    var active = $(selector)
    .parents('li')
    .addClass('active')

    if (active.parent('.dropdown-menu').length) {
    active = active
        .closest('li.dropdown')
        .addClass('active')
    }

    active.trigger('activate.bs.scrollspy')
}

ScrollSpy.prototype.clear = function () {
    var test = $(this.selector)
    .parentsUntil(this.options.target, '.active')
    .removeClass('active')
}


// SCROLLSPY PLUGIN DEFINITION
// ===========================

function Plugin(option) {
    return this.each(function () {
    var $this   = $(this)
    var data    = $this.data('bs.scrollspy')
    var options = typeof option == 'object' && option

    if (!data) $this.data('bs.scrollspy', (data = new ScrollSpy(this, options)))
    if (typeof option == 'string') data[option]()
    })
}

var old = $.fn.scrollspy

$.fn.scrollspy             = Plugin
$.fn.scrollspy.Constructor = ScrollSpy


// SCROLLSPY NO CONFLICT
// =====================

$.fn.scrollspy.noConflict = function () {
    $.fn.scrollspy = old
    return this
}


// SCROLLSPY DATA-API
// ==================

$(window).on('load.bs.scrollspy.data-api', function () {
    $('[data-spy="scroll"]').each(function () {
    var $spy = $(this)
    Plugin.call($spy, $spy.data())
    })
})

}(jQuery);

/* ====================================================================
* Function for generating a hierarchical TOC in pure JS. Assembles a
* list of links based on Sphinx headings, then injects them into a
* Bootstrap-compliant #nav-scroll container.
* ================================================================== */

function GenerateTOC() {
    /* Grab the main Sphinx article and heading anchors */
    var page = document.querySelector('div.wy-nav-content');
    var article = page.querySelector('div[itemprop="articleBody"]');
    /* Exit if the article starts with a !NO_SCROLLSPY comment */
    var testNode = article.childNodes[1];
    if (testNode.nodeType == 8 && testNode.textContent.includes("!NO_SCROLLSPY")) {
        return false;
    };

    /* Sphinx uses the .headerlink class for its article headers.
    Convert to an array because the HTMLCollection type doesn't support
    array methods. */
    var anchors = Array.from(article.getElementsByClassName('headerlink'));
    /* Remove the title from the anchor array, since it won't be in
    the scrollspy hierarchy */
    anchors.splice(0, 1);
    var TOCHTML = "";
    var prevLevel = 1;

    /* Compose scrollspy nav container */
    var navScrollHTML = '<div id="nav-scroll"><h1>In this article</h1><div class="nav"></div></div>';
    /* Inject scrollspy into page */
    page.insertAdjacentHTML('beforebegin', navScrollHTML);

    /* Build the TOC */
    anchors.forEach(
        function(anchor) {
            var headingMatch = anchor.parentNode.nodeName.match(/^H([1-6])$/);
            if (!headingMatch) {
                /* Only include anchors that are children of a heading */
                return;
            }
            /* Grab the bookmark */
            var bookmark = anchor.getAttribute('href');
            /* Clone the heading, since we must manipulate its nodes in
            order to guarantee preservation of its non-anchor HTML */
            var heading = anchor.parentNode.cloneNode(true);
            /* Remove the anchor (and pilcrow) from the cloned node */
            heading.removeChild(heading.lastChild);
            var headingHTML = heading.innerHTML;
            var curLevel = Number(headingMatch[1]);

            if (curLevel > prevLevel) {
                TOCHTML += (new Array(curLevel - prevLevel + 1)).join('<ul>');
            } else if (curLevel < prevLevel) {
                TOCHTML += (new Array(prevLevel - curLevel + 1)).join('</li></ul>');
            } else {
                TOCHTML += (new Array(prevLevel + 1)).join('</li>');
            }

            prevLevel = curLevel;
            TOCHTML += '<li><a href="' + bookmark + '">' + headingHTML + '</a>';
        }
    );

    TOCHTML += (new Array(prevLevel + 1)).join('</ul>');
    /* Add to scrollspy's inner .nav container */
    page.previousSibling.childNodes[1].insertAdjacentHTML('beforeend', TOCHTML);
    return true;
};

document.addEventListener('DOMContentLoaded',
    function() {
        hasTOC = GenerateTOC();
        /* If a TOC was made, call scrollspy on it */
        if (hasTOC) {
            $('body').scrollspy({ target: '#nav-scroll', offset: 150 });
        }; 
    }
);
