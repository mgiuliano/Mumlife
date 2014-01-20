/**
 * Mumlife - Common Scripts.
 *
 * @version     2014-01-20 1.0.0
 * @author      Michael Giuliano <michael@beatscope.co.uk>
 * @copyright   2014 Beatscope Limited | http://www.beatscope.co.uk/
 */


/**
 * jQuery Cookie plugin
 *
 * Copyright (c) 2010 Klaus Hartl (stilbuero.de)
 * Dual licensed under the MIT and GPL licenses:
 * http://www.opensource.org/licenses/mit-license.php
 * http://www.gnu.org/licenses/gpl.html
 *
 * Source: https://github.com/carhartl/jquery-cookie
 */
jQuery.cookie = function (key, value, options) {
    // key and at least value given, set cookie...
    if (arguments.length > 1 && String(value) !== "[object Object]") {
        options = jQuery.extend({}, options);
        if (value === null || value === undefined) {
            options.expires = -1;
        }
        if (typeof options.expires === 'number') {
            var days = options.expires, t = options.expires = new Date();
            t.setDate(t.getDate() + days);
        }
        value = String(value);
        return (document.cookie = [
            encodeURIComponent(key), '=',
            options.raw ? value : encodeURIComponent(value),
            options.expires ? '; expires=' + options.expires.toUTCString() : '', // use expires attribute, max-age is not supported by IE
            options.path ? '; path=' + options.path : '',
            options.domain ? '; domain=' + options.domain : '',
            options.secure ? '; secure' : ''
        ].join(''));
    }
    // key and possibly options given, get cookie...
    options = value || {};
    var result, decode = options.raw ? function (s) { return s; } : decodeURIComponent;
    return (result = new RegExp('(?:^|; )' + encodeURIComponent(key) + '=([^;]*)').exec(document.cookie)) ? decode(result[1]) : null;
};


/**
*   @name                           Elastic
*   @descripton                     Elastic is jQuery plugin that grow and shrink your textareas automatically
*   @version                        1.6.11
*   @requires                       jQuery 1.2.6+
*
*   @author                         Jan Jarfalk
*   @author-email                   jan.jarfalk@unwrongest.com
*   @author-website                 http://www.unwrongest.com
*
*   @licence                        MIT License - http://www.opensource.org/licenses/mit-license.php
*/
(function($){
    jQuery.fn.extend({
        elastic: function() {
            //  We will create a div clone of the textarea
            //  by copying these attributes from the textarea to the div.
            var mimics = [
                'paddingTop',
                'paddingRight',
                'paddingBottom',
                'paddingLeft',
                'fontSize',
                'lineHeight',
                'fontFamily',
                'width',
                'fontWeight',
                'border-top-width',
                'border-right-width',
                'border-bottom-width',
                'border-left-width',
                'borderTopStyle',
                'borderTopColor',
                'borderRightStyle',
                'borderRightColor',
                'borderBottomStyle',
                'borderBottomColor',
                'borderLeftStyle',
                'borderLeftColor'
            ];

            return this.each( function() {

            // Elastic only works on textareas
            if ( this.type !== 'textarea' ) {
                return false;
            }

            var $textarea   = jQuery(this),
                $twin       = jQuery('<div />').css({
                    'position'      : 'absolute',
                    'display'       : 'none',
                    'word-wrap'     : 'break-word',
                    'white-space'   :'pre-wrap'
                }),
                lineHeight  = parseInt($textarea.css('line-height'),10) || parseInt($textarea.css('font-size'),'10'),
                minheight   = parseInt($textarea.css('height'),10) || lineHeight*3,
                maxheight   = parseInt($textarea.css('max-height'),10) || Number.MAX_VALUE,
                goalheight  = 0;

                // Opera returns max-height of -1 if not set
                if (maxheight < 0) { maxheight = Number.MAX_VALUE; }

                // Append the twin to the DOM
                // We are going to meassure the height of this, not the textarea.
                $twin.attr('id', $textarea.attr('id') + '-twin');
                $twin.appendTo($textarea.parent());

                // Copy the essential styles (mimics) from the textarea to the twin
                var i = mimics.length;
                while(i--){
                    $twin.css(mimics[i].toString(),$textarea.css(mimics[i].toString()));
                }

                // Updates the width of the twin. (solution for textareas with widths in percent)
                function setTwinWidth(){
                    var curatedWidth = Math.floor(parseInt($textarea.width(),10));
                    if($twin.width() !== curatedWidth){
                        $twin.css({'width': curatedWidth + 'px'});

                        // Update height of textarea
                        update(true);
                    }
                }

                // Sets a given height and overflow state on the textarea
                function setHeightAndOverflow(height, overflow){
                    var curratedHeight = Math.floor(parseInt(height,10));
                    if($textarea.height() !== curratedHeight){
                        $textarea.css({'height': curratedHeight + 'px','overflow':overflow});
                    }
                }

                // This function will update the height of the textarea if necessary
                function update(forced) {
                    // Get curated content from the textarea.
                    var textareaContent = $textarea.val().replace(/&/g,'&amp;').replace(/ {2}/g, '&nbsp;').replace(/<|>/g, '&gt;').replace(/\n/g, '<br />');

                    // Compare curated content with curated twin.
                    var twinContent = $twin.html().replace(/<br>/ig,'<br />');

                    if(forced || textareaContent+'&nbsp;' !== twinContent){

                        // Add an extra white space so new rows are added when you are at the end of a row.
                        $twin.html(textareaContent+'&nbsp;');

                        // Change textarea height if twin plus the height of one line differs more than 3 pixel from textarea height
                        if(Math.abs($twin.height() + lineHeight - $textarea.height()) > 3){

                            var goalheight = $twin.height()+lineHeight;
                            if(goalheight >= maxheight) {
                                setHeightAndOverflow(maxheight,'auto');
                            } else if(goalheight <= minheight) {
                                setHeightAndOverflow(minheight,'hidden');
                            } else {
                                setHeightAndOverflow(goalheight,'hidden');
                            }

                        }

                    }
                }

                // Hide scrollbars
                $textarea.css({'overflow':'hidden'});

                // Update textarea size on keyup, change, cut and paste
                $textarea.bind('keyup change cut paste', function(e) {
                    update();
                });

                // Update width of twin if browser or textarea is resized (solution for textareas with widths in percent)
                $(window).bind('resize', setTwinWidth);
                $textarea.bind('resize', setTwinWidth);
                $textarea.bind('update', update);

                // And this line is to catch the browser paste event
                $textarea.bind('input paste',function(e){ setTimeout( update, 250); });

                // Run update once when elastic is initialized
                update();

            });

        }
    });
})(jQuery);


/**
 * Mumlife - Common Scripts
 * (c) 2014 Beatscope Limited | http://www.beatscope.co.uk/
 */

function csrfSafeMethod (method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    crossDomain: true,
    cache: true,
    beforeSend: function (xhr, settings) {
        var csrftoken = $.cookie('csrftoken');
        if (!csrfSafeMethod(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
            xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
        }
    }
});

if (typeof(ML) === 'undefined') {
    var ML = {};
}

function trim (str) {
    if (!str || typeof(str) === 'undefined') { return ''; }
    // trim beginning and end
    str = str.replace(/^\s+/, '');
    for (var i = str.length - 1; i >= 0; i--) {
        if (/\S/.test(str.charAt(i))) {
            str = str.substring(0, i + 1);
            break;
        }
    }
    // trim whitespaces
    //str = str.replace(/\s\s*/g, ' ');
    return str;
}


/**
 * Utility Functions
 */
ML.Utils = function () {};

// Change the visibility of an Image field
ML.Utils.prototype.set_image_visibility = function (field, visibility) {
    if (visibility) {
        $('img.'+field+'-edit').slideDown(250).show();
        $('#'+field+'_change').show();
    } else {
        $('img.'+field+'-edit').slideUp(250).hide();
        $('#'+field+'_change').hide();
    }
};

// Prevents enter key press from submitting the form
ML.Utils.prototype.preventEnterSubmit = function (e) {
    if (e.which == 13) {
        var $targ = $(e.target);
        if (!$targ.is("textarea") && !$targ.is(":button,:submit")) {
        var focusNext = false;
            $(this).find(":input:visible:not([disabled],[readonly]), a").each(function () {
                if (this === e.target) {
                    focusNext = true;
                } else if (focusNext){
                    $(this).focus();
                    return false;
                }
            });
            return false;
        }
    }
};

// Add the Utils instance to the ML object
ML.utils = new ML.Utils();

/**
 * Mumlife Settings
 */
ML.Settings = function (settings) {
    this.settings = {
        'site_url': settings['site_url'],
        'static_url': settings.hasOwnProperty('static_url') ? settings['static_url'] : '/static/',
        'api_url': settings['api_url'],
        'csrf_token': $.cookie('csrftoken')
    }
}

ML.Settings.prototype.getSettings = function () {
    return this.settings;
};

ML.Settings.prototype.get = function (name) {
    if (this.settings.hasOwnProperty(name)) {
        return this.settings[name];
    }
};

/**
 * Mumlife Application
 */
ML.Application = function (settings) {
    // Initialize application settings
    ML.settings = new ML.Settings(settings);
    this.init();
};

// Detect mobile v desktop version
ML.Application.prototype.init = function () {
    this.version = null;

    // Extract version parameter if given
    // used to override which version to display
    if (location.search) {
        var qs = location.search.substr(1).split('&');
        for (var p in qs) {
            var kv = qs[p].split('=');
            if (kv[0] == 'version') {
                this.version = trim(kv[1]);
                if (this.version == '') {
                    this.version = null;
                }
                $.cookie('version', this.version, {'path': '/'});
                // remove version parameter from the query string
                location.search = location.search.replace('?'+qs[p], '').replace('&'+qs[p], '');
                break;
            }
        }
    }

    // detect version
    if ($.cookie('version')) {
        this.version = $.cookie('version');
    }
    if (!this.version) {
        if (platform.product) {
            // We are on a mobile device
            this.version = 'mobile';
        } else {
            this.version = 'desktop';
        }
    }

    // add CSS
    if (this.version == 'mobile') {
        $('head').append('<link rel="stylesheet" href="' + ML.settings.get('static_url') + 'css/m.mumlife.css">');
    } else {
        $('head').append('<link rel="stylesheet" href="' + ML.settings.get('static_url') + 'css/d.mumlife.css">');
    }

    // load JS
    this.load();

    // Initialize Menu
    new ML.Menu();

};

ML.Application.prototype.load = function () {
    // Add jQuery Mobile framework if not already on the page
    // The framework is added by default for both desktop and mobile versions,
    // as some of its methods are used by the Mumlife App
    var self = this;
    $(document).bind("mobileinit", function () {
        $.mobile.ajaxEnabled = false;
        $.mobile.linkBindingEnabled = false;
    });
    if ($('head').find('script[src="' + ML.settings.get('static_url') + 'js/jquery.mobile-1.3.2.min.js"]').length == 0) {
        $.getScript(ML.settings.get('static_url') + "js/jquery.mobile-1.3.2.min.js", function () {
            self.ready();
        });
    } else {
        this.ready();
    }
};

ML.Application.prototype.ready = function () {
    $(document.body).show();
    
    // Initialize common widgets
    // we wait a fraction of a second to make sure the DOM has the CSS files added to it.
    // this issue has been seen on Windows Phone 8.
    setTimeout(function () {
        new ML.Notifications();
    }, 250);

    $(document).trigger('ml.Ready');
};

if (!window.ML) {
    window.ML=ML;
}


// Menu
ML.Menu = function () {
    $('[data-entity="menu"]').click(function () {
        if ($('#menu').is(':visible')) {
            $('#menu').slideUp(250);
        } else {
            $('#menu').slideDown(250);
        }
        $(this).blur();
        return false;
    });
};


// Notifications
ML.Notifications = function () {
    var n = $('[data-entity="notifications"]');
    if (n.size() > 0) {
        var url = ML.settings.get('site_url') + 'notifications/';
        $('#notifications').popup({
            afteropen: function( event, ui ) {
                $.mobile.loading("show");
                $('#notifications-content').html('<p><em>Loading notifications</em></p>');
                $('#notifications').popup('reposition', {x:0,y:0,positionTo:'body'});
                $.ajax({
                    url: url,
                    type: 'GET',
                    contentType: "text/html; charset=UTF-8",
                    success: function (response) {
                        $.mobile.loading("hide");
                        n.removeClass('active');
                        $('#notifications-content').html(response);
                        $('#notifications').popup('reposition', {x:0,y:0,positionTo:'body'});
                    },
                    error: function (e) {
                        $.mobile.loading("hide");
                        console.log('FAILED -- ' + e);
                    }
                });
            },
            afterclose: function( event, ui ) {
                $('#notifications-content').empty();
                $.mobile.loading("hide");
            }
        });
        // handle click
        n.on('click', function () {
            $('#notifications').popup('open');
            return false;
        });
    }
    n.removeClass('invisible');
}

// Image Upload Handler
ML.Upload = function (settings) {
    this.url = ML.settings.get('site_url') + 'upload';
    this.model = settings['model'];
    this.field = settings['field'];
    if (settings.hasOwnProperty('width')) {
        this.width = settings['width'];
    } else {
        this.width = 'auto';
    }
    if (settings.hasOwnProperty('height')) {
        this.height = settings['height'];
    } else {
        this.height = 'auto';
    }

    var self = this;

    $('input#'+this.field+'-clear_id').change(function () {
        ML.utils.set_image_visibility(self.field, !$(this).is(':checked'));
    });

    var post_params =  {
        'csrfmiddlewaretoken': ML.settings.get('csrf_token'),
        'model': this.model,
        'field': this.field
    }
    if (this.width !== 'auto') { post_params['width'] = this.width; }
    if (this.height !== 'auto') { post_params['height'] = this.height; }

    $('input#id_'+this.field).ajaxfileupload({
        'action': self.url,
        'params': post_params,
        'onComplete': function(response) {
            if ($('img.'+self.field+'-edit').length > 0) {
                $('img.'+self.field+'-edit').attr('src', response['filename']);
            } else {
                var img = $('<img>');
                img.addClass(self.field+'-edit');
                img.attr('width', self.width);
                img.attr('height', self.height);
                img.attr('src', response['filename']);
                $('input#id_'+self.field).before(img);
            }
            // Add hidden field with uploaded file value
            $('input#id_'+self.field+'_filepath').remove(); // remove field if already on the page
            var input = $('<input>');
            input.attr('type', "hidden");
            input.val(response['filename']);
            input.attr('name', self.field);
            input.attr('id', "id_"+self.field+"_filepath");
            $('input#id_'+self.field).after(input);
            ML.utils.set_image_visibility(self.field, true);
        },
        'onStart': function() {
            if ($('img.'+self.field+'-edit').length > 0) {
                ML.utils.set_image_visibility(self.field, false);
            }
        }
    });

};


/**
 * Feeds
 */
ML.Feed = function (settings) {
    var self = this;
    this.loading = false;
    this.settings = settings;
    this.button = $('.feed .ui-btn');
    this.button.click(function () {
        self.refresh();
        return false;
    });
    if (settings.hasOwnProperty('filters') && settings['filters']) {
        this.setFilters();
    }
    if (settings.hasOwnProperty('slider') && settings['slider']) {
        // update slider value
        var pattern = new RegExp(/\?range=\d+/g);
        var matches = pattern.exec(location.search);
        if (matches) {
            var match = matches.pop().split('=').pop();
            // we wait a fraction of a second to make sure the DOM has the CSS files added to it.
            // this issue has been seen on Windows Phone 8.
            setTimeout(function () {
                $("#range").val(match);
                $("#range").slider('refresh');
            }, 250);
            // update cookie value
            $.cookie('ml_range', match);
        }
        // add slider handler,
        // when button clicked on
        $("#filter").on("click", function (event) {
            self.slide($('#range').val());
            return false;
        });
    }
    if (settings['next'] != '') {
        this.button.show();
    }

    if (this.settings.hasOwnProperty('autoscroll') && this.settings['autoscroll']) {
        // Fetch more when end of page is reached
        $(window).scroll(function() {
            if (!self.loading && settings['next'] != '') {
                var trigger = $(".ui-page").height() - 25;
                if ($(document).scrollTop() + $(window).height() >= trigger) {
                    self.refresh();
                }
            }
        });
    }
};

ML.Feed.prototype.setFilters = function () {
    // Activate the correct filter
    var terms = $('.search-form').find('input[type="text"]').val();
    var pattern = new RegExp(/@\w+/g);
    var filter = pattern.exec(terms);
    filter = filter ? filter[0] : null;
    switch (filter) {
        case '@global':
            $('[data-role="filter-name"]').text("Global posts");
            $('[data-entity="filter"][rel="@local"]').removeClass('active');
            $('[data-entity="filter"][rel="@global"]').addClass('active');
            $('[data-entity="filter"][rel="@friends"]').removeClass('active');
            break;
        case '@friends':
            $('[data-role="filter-name"]').text("Friends' posts");
            $('[data-entity="filter"][rel="@local"]').removeClass('active');
            $('[data-entity="filter"][rel="@global"]').removeClass('active');
            $('[data-entity="filter"][rel="@friends"]').addClass('active');
            break;
        default:
            $('[data-role="filter-name"]').text("Local posts");
            $('[data-entity="filter"][rel="@local"]').addClass('active');
            $('[data-entity="filter"][rel="@global"]').removeClass('active');
            $('[data-entity="filter"][rel="@friends"]').removeClass('active');
    }
    // Filters take the search query and replace any flag with their own
    $('[data-entity="filter"]').click(function () {
        var terms = $('.search-form').find('input[type="text"]').val().split(' ');
        // remove current flags
        var filtered = [];
        for (var t in terms) {
            if (terms[t].charAt(0) != '@') {
                filtered.push(escape(terms[t]));
            }
        }
        // append filter flag
        filtered.push($(this).attr('rel'));
        // finally, go there
        location = trim(filtered.join(' '));
        return false;
    });
};

ML.Feed.prototype.slide = function (distance) {
    // Called when the slider is actioned
    // We assume only 1 parameter is only ever used,
    // therefore we use the question mark (?)
    //
    // if an empty range is provided (i.e. range=),
    // the range used will be the one saved in the cookie, if any.
    var pattern = new RegExp(/\?range=(\d*)/g);
    var loc = location.href;
    if (pattern.exec(loc)) {
        loc = loc.replace(pattern, '?range='+distance);
    } else {
        loc += '?range='+distance;
    }
    location = loc;
};

ML.Feed.prototype.refresh = function () {
    var self = this;
    this.loading = true;
    $.mobile.loading("show");
    this.button.remove();
    if (this.settings['next'] != '') {
        this.settings['next'] = this.settings['next'].replace('&amp;', '&');
        var url = ML.settings.get('site_url') + this.settings['next'];
        $.ajax({
            url: url,
            type: 'GET',
            contentType: "application/json; charset=UTF-8",
            dataType: "json",
            success: function (response) {
                $('.feed').append(response['html_content'])
                          .append(self.button);
                // re-attach the click event, which was removed
                // when we removed the element from the DOM
                self.button.click(function () {
                    self.refresh();
                    return false;
                });
                // update global next index
                self.settings['next'] = response['next'];
                self.finish();
            },
            error: function (e) {
                console.log('FAILED -- ' + e);
                self.finish();
            }
        });
    }
};

ML.Feed.prototype.finish = function () {
    if (this.settings['next'] != '') {
        this.button.show();
        this.button.blur();
    } else {
        this.button.hide();
    }
    $.mobile.loading("hide");
    this.loading = false;
};


/**
 * New Messages & Replies
 */
ML.Messages = function (settings) {
    this.mode = settings && settings.hasOwnProperty('edit-mode') && settings['edit-mode'] ? 'PATCH' : 'POST';
    this.event_id = settings && settings.hasOwnProperty('event_id') ? settings['event_id'] : null;
    this.refresh();
}

ML.Messages.prototype.refresh = function () {
    var self = this;

    $('textarea.message-body').unbind();
    $('textarea.message-body').elastic();

    // Handle message type selection
    var selected = $('.message-visibility').find('option[selected="selected"]');
    $('a[data-entity="message-type"]').each(function () {
        if ($(this).data('type') == selected.val()) {
            $(this).addClass('selected');
        }
    });
    $('a[data-entity="message-type"]').click(function () {
        // set the clicked item as 'selected'
        $('a[data-entity="message-type"]').removeClass('selected');
        $(this).addClass('selected');
        // set the hidden option
        $('.message-visibility').find('option').attr('selected', null);
        $('.message-visibility').find('option[value="'+$(this).data('type')+'"]').attr('selected', 'selected');
        return false;
    });

    // Occurence visibility
    function toggle(value) {
        if (value == 0) {
            $('[data-entity="occurrence-until"]').slideUp(250);
        } else {
            $('[data-entity="occurrence-until"]').slideDown(250);
        }
    }
    toggle($('[data-entity="occurrence"] input:checked').val());
    $('[data-entity="occurrence"] input').off('change').on('change', function () {
        toggle($(this).val());
    });

    // Attach the post handler
    $('[data-entity="message"]').each(function () {
        var box = $(this);
        if (!box.data('bound')) {
            box.data('bound', true);
            var recipient = null;
            // attach click handler to select friend recipient
            if (box.data('type') == 'private-message') {
                if (box.find('[data-entity="recipient"]').size() > 0) {
                    box.find('[data-entity="recipient"]').on('click', function () {
                        // remove the click handler from itself
                        $(this).off('click').on('click', function () { return false; });
                        recipient = $(this).data('id');
                        $(this).html('<p class="message-recipient">To: <strong>' + $(this).text() + '</strong></p>');
                        $('[data-entity="friends-list"]').replaceWith($(this));
                        return false;
                    });
                } else {
                    recipient = box.data('recipient');
                }
            }
            // attach POST click handler
            box.find('[data-entity="button"]').bind('click', function () {
                var errors = [];
                var body = trim(box.find('.message-body').val());
                var visibility = null;
                if (box.data('type') == 'private-message') {
                    visibility = 0; // PRIVATE
                    if (!recipient) {
                        errors.push('<p>Please select a friend</p>');
                    }
                } else {
                    visibility = box.find('.message-visibility').find('option[selected="selected"]').val();
                }
                var data = {
                    'body': body,
                    'visibility': visibility,
                    'mid': box.data('mid'),
                    'recipient': recipient
                };
                if (self.event_id) {
                    data['id'] = self.event_id
                }
                // Events have extra parameters
                // name*, start date*/time, end date/time, location*
                var is_event = false;
                if (box.find('.message-name').length > 0) {
                    // The message is an event
                    is_event = true;
                    data['name'] = box.find('.message-name').val();
<<<<<<< HEAD
                    var _eventdate = box.find('.message-date').val();
                    data['eventdate'] = _eventdate;
=======
                    data['eventdate'] = box.find('.message-date').val();
>>>>>>> e408518b8b6a522054bade7bf9514d948b02d416
                    if (box.find('.message-time').val() == '') {
                        data['eventdate'] += ' 00:00';
                    } else {
                        data['eventdate'] += ' ' + box.find('.message-time').val();
                    }
<<<<<<< HEAD
                    if (box.find('.message-endtime').val() != '') {
                        // eventendtime have the same date as eventdate
                        data['eventenddate'] = _eventdate + ' ' + box.find('.message-endtime').val();
=======
                    data['eventenddate'] = box.find('.message-enddate').val();
                    if (data['eventenddate'] != '') {
                        // if an end date is set, check for an end time
                        if (box.find('.message-endtime').val() == '') {
                            data['eventenddate'] += ' 00:00';
                        } else {
                            data['eventenddate'] += ' ' + box.find('.message-endtime').val();
                        }
>>>>>>> e408518b8b6a522054bade7bf9514d948b02d416
                    }
                    data['location'] = box.find('.message-location').val();
                    data['visibility'] = 3; // force global visibility for events
                    data['occurrence'] = parseInt(box.find('[data-entity="occurrence"] input:checked').val());
                    data['occurs_until'] = box.find('[data-entity="occurrence-until"] input').val();
                }
                // Check required fields
                var valid = true;
                box.find('*[required="required"]').each(function () {
                    if ($(this).val() == '') {
                        errors.push('<p><strong>' + $(this).data('name') + '</strong> is required</p>');
                    }
                });
                if (errors.length > 0) {
                    valid = false;
                    $('#errors-content').html(errors.join(''));
                    $('#errors').popup('open');
                }
                // Post message
                if (valid) {
                    $.ajax({
                        url: ML.settings.get('api_url') + 'message/post',
                        data: JSON.stringify(data),
                        type: self.mode,
                        contentType: "application/json; charset=UTF-8",
                        dataType: "json",
                        success: function (response) {
                            if (is_event) {
                                // Redirect events posts to events calendar
                                location = ML.settings.get('site_url') + 'events/';
                            } else if (box.data('type') == 'message') {
                                // Redirect posts to local feed
                                location = ML.settings.get('site_url');
                            } else {
                                // Reload the current page for replies and private messages
                                location.reload(true);
                            }
                        },
                        error: function (e) {
                            try {
                                console.log('FAILED -- ' + JSON.parse(e.responseText).detail);
                            } catch (err) {
                                console.log('FAILED -- ' + e);
                            }
                        }
                    });
                }
            });
        }
    });

    // Open/close private message
    $('a[data-entity="message"]').click(function () {
        var button = $(this);
        // find related box
        var box = $('div[data-entity="message"]');
        // toggle its visibility
        if (box.is(':visible')) {
            box.slideUp(250, function () {
                box.find('textarea').val('');
            });
        } else {
            box.slideDown(250, function () {
                if (box.find('input[data-type="search"]').size() > 0) {
                    box.find('input[data-type="search"]').focus();
                } else {
                    box.find('textarea').focus();
                }
            });
        }
        return false;
    });
    
};


// AutoFields are automatically saved when they lose focus
// @TODO fields value validation (DoB, postcode)
ML.AutoField = function (settings) {
    var self = this;
    this.model = settings['model'];
    this.entity = settings['entity'];
    this.field = $('#id_'+settings['field']);
    this.widget = settings.hasOwnProperty('widget') ? settings['widget'] : null;
    this.value = this.field.val(); // store initial value
    switch (this.widget) {
        case 'elastic':
            // The value for elastic textareas is in the twin object
            this.value = $('#id_'+settings['field']+'-twin').text();
            break;
        case 'select':
            // The value for selects is in the data-value attribute
            this.value = $('#id_'+settings['field']).data('value');
            var choices = this.field.find('input');
            choices.click(function () {
                self.field.val($(this).val());
                self.update();
            });
            break;
        case 'date':
            // attach onchange event
            this.field.on('change', function () {
            var value = self.field.val();
                if (value !== self.value) {
                    self.update();
                }
            });
            break;
    }

    // attach onblur event
    // store the data when user leaves the field
    this.field.on('blur', function () {
        var value = self.field.val();
        if (value !== self.value) {
            self.update();
        }
    });

    // Make sure the field is updated if the user leaves the page
    // without triggering the onblur event
    $(window).on('beforeunload', function (e) {
        var value = self.field.val();
        if (value && value !== self.value) {
            self.update(function () {
                // make sure to tell the browser to continue
                // once the request is complete
                return true;
            });
        }
    });

};

ML.AutoField.prototype.update = function (callback) {
    // disable field to avoid sending a second request
    // before the first has finished
    this.field.attr('disabled', 'disabled');
    var url = ML.settings.get('api_url') + this.model + '/' + this.entity + '/';
    var data = {};
    data[this.field.attr('name')] = this.field.val();
    var self = this;
    $.ajax({
        url: url,
        data: JSON.stringify(data),
        async: false, // always wait for the request to complete
        type: 'PATCH',
        contentType: "application/json; charset=UTF-8",
        dataType: "json",
        success: function (response) {
            self.done();
            if (typeof(callback) == 'function') {
                callback();
            }
        },
        error: function (e) {
            try {
                var messages = ['Oops something went wrong!\n'];
                var text = JSON.parse(e.responseText);
                for (var f in text) {
                    messages.push(text[f]);
                }
                alert(messages.join("\n"));
            } catch (err) {
                console.log('FAILED -- ' + err);
            }
            self.done();
            if (typeof(callback) == 'function') {
                callback();
            }
        }
    });
};

ML.AutoField.prototype.done = function () {
    this.value = this.field.val();
    this.field.attr('disabled', null);
};


/**
 * Add-to-friend buttons
 */
ML.AddToFriends = function (settings) {
    this.classname = settings['class'];

    var self = this;

    $('a.'+this.classname).click(function () {
        var button = $(this);
        var entities = button.attr('href').replace('#', '').split(',');
        var url = ML.settings.get('api_url') + 'friendships/';
        var status = 0;
        if (button.attr('rel') == 'block') {
            status = 2;
        }
        var data = {
            'from_member': parseInt(entities[0]),
            'to_member': parseInt(entities[1]),
            'status': status
        };
        $.ajax({
            url: url,
            data: JSON.stringify(data),
            type: 'POST',
            contentType: "application/json; charset=UTF-8",
            dataType: "json",
            success: function (response) {
                button.unbind('click').click(function () { return false; });
                if (button.attr('rel') == 'confirm') {
                    button.find('img').removeClass('icon-addtofriend').addClass('icon-friend');
                    button.find('span').text('Friend');
                } else if (button.attr('rel') == 'block') {
                    button.find('img').removeClass('icon-addtofriend').addClass('icon-addtofriend');
                    button.find('span').text('Blocked');
                } else {
                    button.find('img').removeClass('icon-addtofriend').addClass('icon-pendingfriend');
                    button.find('span').text('Requested');
                }
            },
            error: function (e) {
                try {
                    if (JSON.parse(e.responseText).detail == "Already Exists") {
                        // Fails silently - the relation is probably blocked
                    }
                } catch (err) {
                    console.log('FAILED -- ' + err);
                }
            }
        });
        return false;
    });
};
