jQuery(document).ready(function ($) {

    const main = function () {
        const $qrcode = $('#qrcode');

        if ($qrcode.length) {
            new QRCode($qrcode.get(0), {
                text: $qrcode.attr('data-qrcode-payload'),
                width: 128,
                height: 128,
                colorDark: '#222',
                colorLight: '#fff',
                correctLevel: QRCode.CorrectLevel.H
            });
        }
    };

    $(document).on('click', '.playlist-add', function () {
        showModal('modal-playlist-add');
        $('.modal-playlist-add input:eq(0)').focus().select();
    });

    $(document).on('click', '.playlist-preview', function () {
        const $icon = $(this).find('i');
        const isPlay = $icon.hasClass('fa-play');
        const $holder = $(this).parents('.preview:eq(0)');

        if (isPlay) {
            const $iframe = $('<iframe>', {
                src: $(this).attr('data-url'),
                frameborder: 0
            });

            $holder.append($iframe);
            $(this).addClass('hover-only');
            $icon.removeClass('fa-play').addClass('fa-pause');
        } else {
            $holder.find('iframe').remove();
            $(this).removeClass('hover-only');
            $icon.removeClass('fa-pause').addClass('fa-play');
        }
    });

    main();
});
