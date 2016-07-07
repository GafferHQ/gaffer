/*
 * Smoothproducts
 * http://kthornbloom.com/smoothproducts.php
 *
 * Copyright 2013, Kevin Thornbloom
 * Free to use and abuse under the MIT license.
 * http://www.opensource.org/licenses/mit-license.php
 */

(function ($) {
    $.fn.extend({
        smoothproducts: function () {


            var slideTiming = 300

            // Add some markup & set some CSS
            $('.sp-wrap').append('<div class="sp-large"></div><div class="sp-thumbs sp-tb-active"></div>');
            $('.sp-wrap').each(function () {
                $('a', this).appendTo($('.sp-thumbs', this));
                $('.sp-thumbs a:first', this).addClass('sp-current').clone().removeClass('sp-current').appendTo($('.sp-large', this)).addClass('sp-current-big');
                $('.sp-wrap').css({
                    display: 'inline-block'
                });
            });

            // Prevent clicking while things are happening
            $(document.body).on('click', '.sp-thumbs', function (event) {
                event.preventDefault();
            });

            // Clicking a thumbnail
            $(document.body).on('click', '.sp-tb-active a', function (event) {
                $(this).parent().find('.sp-current').removeClass();
                $(this).parent().parent().find('.sp-thumbs').removeClass('sp-tb-active');
                $(this).parent().parent().find('.sp-zoom').remove();
                $(this).parent().parent().find('.sp-full-screen').fadeOut(function () {
                    $(this).remove();
                });

                var currentHeight = $(this).parent().parent().find('.sp-large').height(),
                    currentWidth = $(this).parent().parent().find('.sp-large').width();
                $(this).parent().parent().find('.sp-large').css({
                    overflow: 'hidden',
                    height: currentHeight + 'px',
                    width: currentWidth + 'px'
                });

                $(this).parent().parent().find('.sp-large a').remove();
                $(this).addClass('sp-current').clone().hide().removeClass('sp-current').appendTo($(this).parent().parent().find('.sp-large')).addClass('sp-current-big').fadeIn(slideTiming, function () {

                    var autoHeight = $(this).parent().parent().find('.sp-large img').height();

                    $(this).parent().parent().find('.sp-large').animate({
                        height: autoHeight
                    }, 'fast', function () {
                        $('.sp-large').css({
                            height: 'auto',
                            width: 'auto',
                            
                        });
                    });

                    $(this).parent().parent().find('.sp-thumbs').addClass('sp-tb-active');
                });
                event.preventDefault();
            });

            //  Zoom In
            $(document.body).on('mouseover', '.sp-large a', function (event) {
                var largeUrl = $(this).attr('href');
                $(this).parent().parent().find('.sp-large').append('<div class="sp-zoom"><img src="' + largeUrl + '"/></div>');
                $(this).parent().parent().find('.sp-zoom').fadeIn();
                $(this).parent().parent().find(".sp-zoom").draggable();
                //$(this).parent().parent().prepend('<div class="sp-full-screen"><a href="#">↕</a></div>');
                event.preventDefault();
            });


            // Click To Lightbox Popup Show
            var lightBoxUrl = $('.sp-thumbs a:first').attr('href');
            $('.sp-full-screen a').attr('href', lightBoxUrl)
            $(".sp-thumbs a").click(function () {
                var bg = $(this).attr('href');
                $('.sp-full-screen a').attr('href', bg)
            });




            // Panning zoomed PC

            $('.sp-large').mousemove(function (e) {
                var viewWidth = $(this).width(),
                    viewHeight = $(this).height(),
                    largeWidth = $(this).find('.sp-zoom').width(),
                    largeHeight = $(this).find('.sp-zoom').height(),
                    parentOffset = $(this).parent().offset(),
                    relativeXPosition = (e.pageX - parentOffset.left),
                    relativeYPosition = (e.pageY - parentOffset.top),
                    moveX = Math.floor((relativeXPosition * (viewWidth - largeWidth) / viewWidth)),
                    moveY = Math.floor((relativeYPosition * (viewHeight - largeHeight) / viewHeight));

                $(this).find('.sp-zoom').css({
                    left: moveX,
                    top: moveY
                    
                });

            }).mouseout(function () {
                // Pause Panning
            });

            // Panning zoomed Mobile - inspired by http://popdevelop.com/2010/08/touching-the-web/

            $.fn.draggable = function () {
                var offset = null;
                var start = function (e) {
                    var orig = e.originalEvent;
                    var pos = $(this).position();
                    offset = {
                        x: orig.changedTouches[0].pageX - pos.left,
                        y: orig.changedTouches[0].pageY - pos.top
                    };
                };
                var moveMe = function (e) {
                    e.preventDefault();
                    var orig = e.originalEvent,
                        newY = orig.changedTouches[0].pageY - offset.y,
                        newX = orig.changedTouches[0].pageX - offset.x,
                        maxY = (($('.sp-zoom').height()) - ($('.sp-large').height())) * -1,
                        maxX = (($('.sp-zoom').width()) - ($('.sp-large').width())) * -1;
                    if (newY > maxY && 0 > newY) {
                        $(this).css({
                            top: newY
                        });
                    }
                    if (newX > maxX && 0 > newX) {
                        $(this).css({
                            left: newX
                        });
                    }
                };
                this.bind("touchstart", start);
                this.bind("touchmove", moveMe);
            };

            // Zoom Out
            $(document.body).on('mouseleave', '.sp-zoom', function (event) {
                $(this).fadeOut(function () {
                    $(this).remove();
                });
            });




        }
    });
})(jQuery);