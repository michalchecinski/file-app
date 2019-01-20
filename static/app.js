var username = document.currentScript.getAttribute('username');

    var source = new EventSource("https://pi.iem.pw.edu.pl:8143/checinsm/notify/subscribe/"+username)

    source.onmessage = function(event) {
      alert(event.data);
    };