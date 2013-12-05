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
 * (c) 2013 Beatscope Limited | http://www.beatscope.co.uk/
 */

function csrfSafeMethod (method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    crossDomain: true,
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
 * Utility Objects
 */

// Image Upload Handler
ML.Upload = function (settings) {
    this.url = settings['url'];
    this.model = settings['model'];
    this.field = settings['field'];
    this.token = settings['token'];
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
        'csrfmiddlewaretoken': this.token,
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
 * New Messages & Replies
 */
ML.Messages = function (settings) {
    this.api_url = settings['api_url'];
    this.token = settings['token'];
    this.refresh();
}

ML.Messages.prototype.refresh = function () {
    var self = this;

    $('.message-body').unbind();
    $('.message-body').elastic();

    // Show reply post button when the textarea has a value
    $('.message-body').keyup(function () {
        var postbutton = $('[data-entity="button"][data-mid="'+ $(this).data('mid') +'"]');
        if ($(this).val().length <= 0) {
            postbutton.hide();
        } else {
            postbutton.show();
        }
    });

    // Handle message type selection
    $('a[data-entity="message-type"]').click(function () {
        // set the clicked item as 'selected'
        $('a[data-entity="message-type"]').removeClass('selected');
        $(this).addClass('selected');
        // set the hidden option
        $('.message-visibility').find('option').attr('selected', null);
        $('.message-visibility').find('option[value="'+$(this).data('type')+'"]').attr('selected', 'selected');
        return false;
    });

    // Attach the post handler to the textareas
    $('[data-entity="message"]').each(function () {
        var box = $(this);
        if (!box.data('bound')) {
            box.data('bound', true);
            box.find('button.message-button').bind('click', function () {
                var body = trim(box.find('.message-body').val());
                var visibility = null;
                var recipient = null;
                if (box.data('type') == 'private-message') {
                    visibility = 0; // PRIVATE
                    recipient = box.data('recipient');
                } else if (box.find('.message-visibility').find('option:selected').length > 0) {
                    visibility = box.find('.message-visibility').find('option:selected').val();
                }
                var data = JSON.stringify({
                    'body': body,
                    'visibility': visibility,
                    'mid': box.data('mid'),
                    'recipient': recipient
                });
                if (body.length > 0) {
                    $.ajax({
                        url: self.api_url + 'messages/post',
                        data: data,
                        type: 'POST',
                        contentType: "application/json; charset=UTF-8",
                        dataType: "json",
                        success: function (response) {
                            if (box.data('type') == 'message') {
                                location = SITE_URL;
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

    // Open/close replies
    $('a[data-entity="replies"]').unbind().click(function () {
        var button = $(this);
        // find related box
        var box = $('div[data-entity="replies"][data-rel="'+button.attr('rel')+'"]');
        // toggle its visibility
        if (box.is(':visible')) {
            box.slideUp(250);
        } else {
            box.slideDown(250);
        }
        return false;
    });

    // Open/close private message
    $('a[data-entity="message"]').click(function () {
        var button = $(this);
        // find related box
        var box = $('div[data-entity="message"]');
        // toggle its visibility
        if (box.is(':visible')) {
            box.slideUp(250);
        } else {
            box.slideDown(250, function () {
                box.find('textarea').focus();
            });
        }
        return false;
    });
    
};


// AutoFields are automatically saved when they lose focus
// @TODO fields value validation (DoB, postcode)
ML.AutoField = function (settings) {
    var self = this;

    this.entity = settings['entity'];
    this.api_url = settings['api_url'];
    this.token = settings['token'];
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
            var selects = this.field.find('[data-entity="select-option"]');
            selects.click(function () {
                self.field.val($(this).data('value'));
                self.update(function () {
                    selects.removeClass('selected');
                    selects.filter('[data-value="'+self.field.val()+'"]').addClass('selected');
                });
                return false;
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
};

ML.AutoField.prototype.update = function (callback) {
    // disable field to avoid sending a second request
    // before the first has finished
    this.field.attr('disabled', 'disabled');
    var url = this.api_url + this.entity + '/';
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
    this.class = settings['class'];
    this.api_url = settings['api_url'];
    this.token = settings['token'];

    var self = this;

    $('a.'+this.class).click(function () {
        var button = $(this);
        var entities = button.attr('href').replace('#', '').split(',');
        var url = self.api_url + 'friendships/';
        var data = {
            'from_member': parseInt(entities[0]),
            'to_member': parseInt(entities[1]),
            'status': 0
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
                } else {
                    button.find('img').removeClass('icon-addtofriend').addClass('icon-pendingfriend');
                    button.find('span').text('Requested');
                }
            },
            error: function (e) {
                console.log('FAILED -- ' + JSON.parse(e.responseText).detail);
            }
        });
        return false;
    });
};
