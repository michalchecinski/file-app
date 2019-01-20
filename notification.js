const serverPort = 8113,
    httpsServerPort = 8143,
    bodyParser = require('body-parser')
    events = require('events'),
    emitter = new events.EventEmitter(),
    fs = require('fs'),
    http = require('http'),
    express = require('express'),
    https = require('https'),
    privateKey  = fs.readFileSync('ssl/file.key', 'utf8'),
    certificate = fs.readFileSync('ssl/file.crt', 'utf8'),
    credentials = {key: privateKey, cert: certificate},
    app = express();

    app.use(bodyParser.urlencoded({ extended: false }))

app.get('/checinsm/notify/subscribe/:username', function (request, response) {
    response.setHeader('Access-Control-Allow-Origin', '*');
    response.writeHead(200, {
        'Connection': 'keep-alive',
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Access-Control-Allow-Origin': '*'
    });


    var username = request.params.username;
    if (!username) {
        response.writeHeader(400, { "Content-Type": "text/html" });
        response.write('Bad request');
        response.end();
    }
    else {
        console.log("Subscribing: " + username);

        emitter.on(username, function (message) {
            response.write(
                `data: Hej, użytkownik "${username}" wgrał nowy plik "${message}"`);
            response.write('\n\n');
        });
    }
});

app.post('/checinsm/notify/send/:username', function (request, response) {
    var data = request.body;
    var username = request.params.username || data.username;

    if (username) {
        var filename = data.filename || '';
        emitter.emit(username, filename);
        response.writeHeader(200, { "Content-Type": "text/html" });
        response.write('OK wysylam');
        response.end();
    }
    else {
        response.writeHeader(400, { "Content-Type": "text/html" });
        response.write('Brak uzytkownika');
        response.end();
    }
});

const httpsServer = https.createServer(credentials, app),
httpServer = http.createServer(app);

httpServer.listen(serverPort, () => {
    console.log(`HTTP server started on port ` + serverPort);
});
httpsServer.listen(httpsServerPort, () => {
    console.log(`HTTPS server started on port ` + serverPort);
});