# File hosting and sharing app
This app was made based on Python flask microframework.

It's purpose is to host files and allow users to share them with others (Dropbox-style, but waaaay simpler app).

## Architecture
App has several micro-services:
* file.py - main app that serves views and manages users;
* dl.py - app used for uploading and downloading files;
* notification.js - notification server. When user is logged in on several devices would see on other devices that file was uploaded by him/her;
* resizer.py - app that makes minified versions of images to show on the files list. It uses imagemagick (you must provide that program).

## Technologies used:
| Technology name | purpose |
|------|-------|
| [Flask](http://flask.pocoo.org/) | framework used in file app and dl API app |
| [auth0.com](https://auth0.com) | Identity provider |
| [JWT](https://jwt.io/) | Tokens used for authorisng user between API (dl) app and main (file) app |
| [SSE](https://www.w3schools.com/html/html5_serversentevents.asp) | To receive notifications in HTML without constantlly sending requests to server |
| [Node.js](https://nodejs.org/en/) | Serve notifications |
| [RabbitMQ](https://www.rabbitmq.com/) | Communicate between dl.py app and resizer.py app. That way there can be few resizer instances to minify images. |
| [Redis](https://redis.io/) | Redis is used to store user sessions and allow secure logout |
| [Bootstrap](https://getbootstrap.com/) | To sites look nice (I'm not any good at styling and views) and also to be responsive. |
| [uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/) | To serve app via multi-server environment. Main config was made in NGNIX. Config for uWSGI is in file.ini and dl.ini files. |
