
$(function () {
    let server;
    if (sessionStorage.getItem('information')) {
        server = JSON.parse(sessionStorage.getItem('information')).server_media;
        loadStream(server + $(".inner-scroll a.active").attr('id'));
    } else {
        fetch('/get_server')
            .then(r => r.json())
            .then(info => {
                info.server_media = '//' + info.server_url + '/media/';
                let url = info.server_media + $(".inner-scroll a.active").attr('id');
                sessionStorage.setItem('information', JSON.stringify(info))
                loadStream(url);
            });
    }

    function loadStream(url) {
        if (!Hls.isSupported() && video.canPlayType('application/vnd.apple.mpegurl')) {
            video.src = url;
            video.addEventListener('loadedmetadata', function () {
                video.play();
            });
        } else {
            if (hls) {
                hls.destroy();
                if (hls.bufferTimer) {
                    clearInterval(hls.bufferTimer);
                    hls.bufferTimer = undefined;
                }
                hls = null;
            }

            var hls = new Hls();
            hls.loadSource(url);
            hls.attachMedia(video);
            hls.on(Hls.Events.MANIFEST_PARSED, function () {
                video.play();
            });
            $('#playback_rate').text(document.querySelector('video').playbackRate)
        }
    }

    $(".inner-scroll a.list-group-item:not(.disabled)").click(function () {
        $(".inner-scroll a.list-group-item").removeClass('active')
        $(this).addClass('active')
        loadStream(server + this.id)
        children_url = '/detail/' + $(this).data('class_id') + '/children_id/' + this.id
        window.history.pushState(null, '', children_url)
    });


    $('.add_rate').click(function () {
        document.querySelector('video').playbackRate += 0.25
        $('#playback_rate').text(document.querySelector('video').playbackRate)
    })

    $('.del_rate').click(function () {
        document.querySelector('video').playbackRate -= 0.25
        $('#playback_rate').text(document.querySelector('video').playbackRate)
    })

});