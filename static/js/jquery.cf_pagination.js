(function ($) {

    $.fn.cf_pagination = function(){

        /**
         * ...
         * @param {eventObject}
         */
        function submit(e) {
            e.preventDefault();

            $.when(getPaginatedPosts(getAjaxAction(e)))
            .then(updatePosts);
        }

        /**
         * ...
         * @param {string}
         */
        function updatePosts(results){
            // Animation
            // $('#pagination_content')
            // .fadeOut(400, function(){
            //     $(this).replaceWith(results);
            //     $('#pagination_content')
            //     .hide()
            //     .fadeIn(400);
            // });
            // $('html,body').animate({scrollTop: $('#pagination_content').offset().top}, 800);

            // No animation
            $('#pagination_content').replaceWith(results);
            $('html,body').animate({scrollTop: $('.content_main').offset().top}, 0);
        }

        /**
         * ...
         * @param {eventObject}
         */
        function getAjaxAction(e) {
            var action = '' + 
                         // Remove everything after the '?'
                         e.currentTarget.action.split('?')[0]
                         .replace('#pagination_content','') + // Remove '#pagination_content' so we can add it in the right spot
                         $(e.currentTarget).parents('.pagination').data('ajax-action') +
                         '?' +
                         $(e.currentTarget).serialize() +
                         '#pagination_content';
            console.log(action);
            return action;
        }

        /**
         * ...
         * @param {string}
         */
        function getPaginatedPosts(page) {
            var promise = $.get(page);
            return promise;
        }

        return $(this).each(function(){
            $(this).on('submit', '.pagination_form', submit)​;
        });
    };

    // Auto init
    $('body').cf_pagination();

}(jQuery));
