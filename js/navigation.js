$(document).ready(function () {
    int_nav_menu_height();
});

$(window).resize(function () {
    int_nav_menu_height();
});

// ----------------------------------------------------------------
// Navigation Menu panel
// ----------------------------------------------------------------
var mobile_menu_icon = $(".nav-mobile");
var mobile_menu = $(".nav-menu");

// Mobile menu max height
function int_nav_menu_height() {
    mobile_menu.css("max-height", $(window).height() - $(".header").height() - 20 + "px"), $(window).width() <= 1024 ? $(".header").addClass("mobile-device") : $(window).width() > 1024 && ($(".header").removeClass("mobile-device"))
};

// Mobile menu toggle icon
mobile_menu_icon.click(function () {
    if (!($(this).hasClass('active'))) {
        mobile_menu_icon.addClass('active');
        mobile_menu.addClass('active');
    }
    else if ($(this).hasClass('active')) {
        mobile_menu_icon.removeClass('active');
        mobile_menu.removeClass('active');
    }
});


// Dropdown Sub menu
var menu_Sub = $(".menu-has-sub");
var menu_Sub_Li;

$(".mobile-device .menu-has-sub").find(".fa:first").removeClass("fa-angle-right").addClass("fa-angle-down");

menu_Sub.click(function () {
    if ($(".header").hasClass("mobile-device")) {
        menu_Sub_Li = $(this).parent("li:first");
        if (menu_Sub_Li.hasClass("menu-opened")) {
            menu_Sub_Li.find(".sub-dropdown:first").slideUp(function () {
                menu_Sub_Li.removeClass("menu-opened");
                menu_Sub_Li.find(".menu-has-sub").find(".fa:first").removeClass("fa-angle-up").addClass("fa-angle-down");
            });
        }
        else {
            $(this).find(".fa:first").removeClass("fa-angle-down").addClass("fa-angle-up");
            menu_Sub_Li.addClass("menu-opened");
            menu_Sub_Li.find(".sub-dropdown:first").slideDown();
        }
        return false;
    }
    else {
        return false;
    }
});

menu_Sub_Li = menu_Sub.parent("li");
menu_Sub_Li.hover(function () {
    if (!($(".header").hasClass("mobile-device"))) {
        $(this).find(".sub-dropdown:first").stop(true, true).fadeIn("fast");
    }

}, function () {
    if (!($(".header").hasClass("mobile-device"))) {
        $(this).find(".sub-dropdown:first").stop(true, true).delay(100).fadeOut("fast");
    }

});