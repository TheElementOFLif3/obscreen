 const getPayload = function() {
        let screen = $('#screen');
        let screenWidth = screen.width();
        let screenHeight = screen.height();

        $('.element').each(function () {
            let offset = $(this).position();
            let x = offset.left;
            let y = offset.top;
            let width = $(this).width();
            let height = $(this).height();

            let xPercent = (x / screenWidth) * 100;
            let yPercent = (y / screenHeight) * 100;
            let widthPercent = (width / screenWidth) * 100;
            let heightPercent = (height / screenHeight) * 100;

            console.log(JSON.stringify({
                xPercent: xPercent,
                yPercent: yPercent,
                widthPercent: widthPercent,
                heightPercent: heightPercent
            }));
        });
    };

jQuery(document).ready(function ($) {
    let currentElement = null;
    let elementCounter = 0;

    $('.screen').css({
        width: $('.screen').width(),
        height: $('.screen').height(),
        position: 'relative',
    }).parents('.screen-holder:eq(0)').css({
        width: 'auto',
        'padding-top': '0px'
    });



    function createElement() {
        let screen = $('#screen');
        let screenWidth = screen.width();
        let screenHeight = screen.height();

        // Dimensions de l'élément
        let elementWidth = 100;
        let elementHeight = 50;

        // Générer des positions aléatoires
        let x = Math.round(Math.random() * (screenWidth - elementWidth));
        let y = Math.round(Math.random() * (screenHeight - elementHeight));

        // Constrain x and y
        x = Math.round(Math.max(0, Math.min(x, screenWidth - elementWidth)));
        y = Math.round(Math.max(0, Math.min(y, screenHeight - elementHeight)));

        let elementId = elementCounter++;
        let element = $('<div class="element" id="element-' + elementId + '" data-id="' + elementId + '"><button>Button</button></div>');
        // let element = $('<div class="element" id="' + elementId + '"><button>Button</button><div class="rotate-handle"></div></div>');

        element.css({
            left: x,
            top: y,
            width: elementWidth,
            height: elementHeight,
            transform: `rotate(0deg)`
        });

        element.draggable({
            containment: "#screen",
            start: function (event, ui) {
                focusElement(ui.helper);
            },
            drag: function (event, ui) {
                updateForm(ui.helper);
            }
        });

        element.resizable({
            containment: "#screen",
            handles: 'nw, ne, sw, se',
            start: function (event, ui) {
                focusElement(ui.element);
            },
            resize: function (event, ui) {
                updateForm(ui.element);
            }
        });
        /*
        element.rotatable({
            handle: element.find('.rotate-handle'),
            rotate: function(event, ui) {
                updateForm(ui.element);
            }
        });
        */

        element.click(function () {
            focusElement($(this));
        });

        $('#screen').append(element);
        addElementToList(elementId);
        setTimeout(function() {
            focusElement(element);
        }, 10);
    }

    $(document).on('click', '.element-list-item', function(){
        focusElement($('#element-' + $(this).attr('data-id')));
    })

    $(document).on('click', '.remove-element', function(){
          removeElementById($(this).attr('data-id'));
    })

    function removeElementById(elementId) {
        $('.element[data-id='+elementId+'], .element-list-item[data-id='+elementId+']').remove();
        updateZIndexes();
    }

    function addElementToList(elementId) {
        let listItem = $('<div class="element-list-item" data-id="' + elementId + '">Element ' + elementId + ' <button type="button" class="remove-element" data-id="' + elementId + '">remove</button></div>');
        $('#elementList').append(listItem);
        updateZIndexes();
    }

    function unfocusElements() {
        $('.element, .element-list-item').removeClass('focused');
        currentElement = null;
        updateForm(null);
    }

    function focusElement(element) {
        unfocusElements();
        currentElement = element;
        currentElement.addClass('focused');
        const listElement = $('.element-list-item[data-id="' + currentElement.attr('data-id') + '"]');
        listElement.addClass('focused');
        updateForm(currentElement);
    }

    function updateForm(element) {
        if (!element) {
            $('form#elementForm input').val('').prop('disabled', true);
            return;
        }

        $('form#elementForm input').prop('disabled', false);

        let offset = element.position();

        if (offset !== undefined) {
            $('#elem-x').val(offset.left);
            $('#elem-y').val(offset.top);
            $('#elem-width').val(element.width());
            $('#elem-height').val(element.height());
        }
        /*
        let rotation = element.css('transform');
        let values = rotation.split('(')[1].split(')')[0].split(',');
        let angle = Math.round(Math.atan2(values[1], values[0]) * (180/Math.PI));
        $('#elem-rotate').val(angle);
        */
    }

    $(document).on('input', '#elementForm input', function () {
        if (currentElement) {
            let screenWidth = $('#screen').width();
            let screenHeight = $('#screen').height();

            let x = Math.round(parseInt($('#elem-x').val()));
            let y = Math.round(parseInt($('#elem-y').val()));
            let width = Math.round(parseInt($('#elem-width').val()));
            let height = Math.round(parseInt($('#elem-height').val()));
            // let rotation = parseInt($('#elem-rotate').val());

            // Constrain x and y
            x = Math.max(0, Math.min(x, screenWidth - width));
            y = Math.max(0, Math.min(y, screenHeight - height));

            // Constrain width and height
            width = Math.min(width, screenWidth - x);
            height = Math.min(height, screenHeight - y);

            currentElement.css({
                left: x,
                top: y,
                width: width,
                height: height
                // transform: `rotate(${rotation}deg)`
            });

            // Update form values to reflect clamped values
            $('#elem-x').val(x);
            $('#elem-y').val(y);
            $('#elem-width').val(width);
            $('#elem-height').val(height);
        }
    });

    $(document).on('click', '#addElement', function () {
        createElement();
    });

    $(document).on('click', '#removeAllElements', function () {
        $('.element, .element-list-item').remove();
        updateZIndexes();
    });

    $(document).on('mousedown', function (e) {
        const keepFocusedElement = $(e.target).hasClass('element')
            || $(e.target).hasClass('element-list-item')
            || $(e.target).parents('.element:eq(0)').length !== 0
            || $(e.target).parents('.element-list-item:eq(0)').length !== 0
            || $(e.target).is('input,select,textarea')

        if (!keepFocusedElement) {
            unfocusElements();
        }
    });

    $(document).on('click', '#presetGrid2x2', function () {
        let screenWidth = $('#screen').width();
        let screenHeight = $('#screen').height();
        let elements = $('.element');
        if (elements.length < 4) {
            while (elements.length < 4) {
                createElement();
                elements = $('.element');
            }
        }

        let gridPositions = [
            {x: 0, y: 0},
            {x: screenWidth / 2, y: 0},
            {x: 0, y: screenHeight / 2},
            {x: screenWidth / 2, y: screenHeight / 2}
        ];

        elements.each(function (index) {
            let position = gridPositions[index];
            $(this).css({
                left: position.x,
                top: position.y,
                width: screenWidth / 2,
                height: screenHeight / 2
            });
            updateForm($(this));
        });
    });

    function updateZIndexes() {
        const zindex = $('.element-list-item').length + 1;
        $('.element-list-item').each(function(index) {
            let id = $(this).attr('data-id');
            $('#element-' + id).css('z-index', zindex - index);
        });
    }

    $('#elementList').sortable({
        update: function(event, ui) {
            updateZIndexes();
        }
    });

    createElement();
    updateForm(null);
});
