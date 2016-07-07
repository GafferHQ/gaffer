$(function () {
    "use strict";




    $(document).ready(function () {

        // Slider Video
        $('.intro-Rev_Video').revolution({
            sliderType: "hero",
            delay: 9000,
            startwidth: 1170,
            startheight: 500,
            fullScreen: "on",
            forceFullWidth: "on",
            minFullScreenHeight: "320",
            touchenabled: "off",
        });

        // Slider Dark Light
        var revslider_two = $('.intro-RevSlider');
        revslider_two.revolution({
            delay: 15000,
            startwidth: 1170,
            startheight: 500,
            hideThumbs: 10,
            hideTimerBar: "off",
            fullWidth: "off",
            fullScreen: "on",
            fullScreenOffsetContainer: "",
            navigationStyle: "preview4",
            navigationType: "none",
        });

        // Header color "dark" "light  |-------------------------------------------------------"
        revslider_two.bind("revolution.slide.onchange", function (e, data) {

            var color = $(this).find('li').eq(data.slideIndex - 1).data('slide');

            if (color == 'dark-slide') {
                $('#header').addClass('header').removeClass('header-light');
                $('#header').removeClass('header-default');
            }
            if (color == 'light-slide') {
                $('#header').addClass('header-light').removeClass('header-dark');
                $('#header').removeClass('header-default');
            }
            if (color == 'default-slide') {
                $('#header').removeClass('header-dark');
                $('#header').removeClass('header-light');
                $('#header').addClass('header');
            }
            // console.log("rev slide color: " + color);

        });


    });




});