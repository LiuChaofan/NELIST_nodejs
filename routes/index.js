var express = require('express');
var router = express.Router();

/* GET home page. */
router.get('/', function(req, res) {
  res.render('index', { title: 'Express' });
});

module.exports = router;
module.exports.index=function(req, res){
    res.render('index', {title: 'index'});
}

var client = require('mysql');
var pool = client.createPool({
    host: '172.16.20.204',
    user: 'root',
    password: 'iieneliot',
    database: 'weibo'
});
module.exports.db=function(req, res){
    if(req.params.db == "mysql"){
        res.render('db', {dbName: 'mysql'});
    }
    else{
        res.render('db', {dbName: 'couchdb'});
    }
}
module.exports.table=function(req, res){
        pool.getConnection(function(err, connection){

            var startInx = 0;
            var curPage = 1;
            if(req.query.page){
                curPage = req.query.page;
                startInx = (curPage - 1) * 10;
            }
            connection.query('SELECT * from ' + req.params.table + ' limit ' + startInx + ',10;', function(err, rows){
                var data = new Array();
                for(var i = 0; i < 10; i ++){
                    data[i] = rows[i];
                }
            
                res.render('table',{
                    dbName: req.params.db,
                    table: req.params.table,
                    data: data,
                    curPage: curPage
                });
            });
            connection.release();
        });
}
module.exports.data=function(req, res){
    if(req.params.db == 'mysql'){
        pool.getConnection(function(err, connection){
            var data;
            if(req.params.table == "dataset"){
                data = "ID号";
            }
            else if(req.params.table == "weibo"){
                data = "mid";
            }
            else{
                data = "uid";
            }
            connection.query('SELECT * from ' + req.params.table + ' where ' + data + '=' + req.params.ID, function(err, rows){
                var json = JSON.stringify(rows[0]);
                json = eval("(" + json + ")");
                res.render('data', {
                    dbName: req.params.db,
                    table: req.params.table, //dataset, weibo or user
                    ID: req.params.ID, //ID号, mid or uid
                    data: json //JSON data, should be parsed in the .ejs file.
                });
            });
            connection.release();
        });
    }
}
