var express = require('express');
var path = require('path');
var favicon = require('static-favicon');
var logger = require('morgan');
var cookieParser = require('cookie-parser');
//var bodyParser = require('body-parser');
var formidable = require('formidable');
var routes = require('./routes/index');
var users = require('./routes/users');

var app = express();
//var partials = require("express-partials");
// view engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');

app.use(favicon());
app.use(logger('dev'));
//app.use(bodyParser.json());
//app.use(bodyParser.urlencoded());
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));
//app.use(partials());
app.use('/', routes);
app.use('/users', users);
app.get('/', routes.index);
app.get('/blacklist', routes.blacklist);
app.post('/blacklist/upload', routes.blacklist_upload);
app.get('/blacklist/add', routes.blacklist_add);
app.get('/blacklist/del', routes.blacklist_del);
app.get('/blacklist/download', routes.blacklist_dl);
app.get('/blacklist/scan', routes.blacklist_scan);
app.get('/blacklist/addFriends', routes.blacklist_add_friends);
app.get('/:db', routes.db);
app.get('/:db/:table', routes.table);
app.get('/:db/:table/:ID', routes.data);
/// catch 404 and forwarding to error handler
app.use(function(req, res, next) {
    var err = new Error('Not Found');
    err.status = 404;
    next(err);
});

/// error handlers

// development error handler
// will print stacktrace
if (app.get('env') === 'development') {
    app.use(function(err, req, res, next) {
        res.status(err.status || 500);
        res.render('error', {
            message: err.message,
            error: err
        });
    });
}

// production error handler
// no stacktraces leaked to user
app.use(function(err, req, res, next) {
    res.status(err.status || 500);
    res.render('error', {
        message: err.message,
        error: {}
    });
});


module.exports = app;
