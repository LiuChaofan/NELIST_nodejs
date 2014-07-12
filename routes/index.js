var express = require('express');
var formidable = require('formidable');
var Stream = require('user-stream');
var stream = new Stream({
    consumer_key:'EMuscv9fTwLZVdCdaZE2LUybi',
    consumer_secret: '4Vqwy2GzqDFT8wsu2MKkh3QUrbWxor0K4gT0ZqiEUV3BjuRb68',
    access_token_key:'Vsx8SpxFGu7WJALCKHWnDGyMn1su5BlVWb9hwN8',
    access_token_secret:'s90C1dDSEAqGg7Aj5uOanDzuSnysq8B6Ql9wiphpCI8'
});
var fs = require('fs');
var readline = require('readline');

var router = express.Router();
var util = require('util');
var form = new formidable.IncomingForm();
var exec = require('child_process').exec;
form.keepExtensions = true;
form.uploadDir = 'tmp';

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
module.exports.blacklist=function(req, res){
    pool.getConnection(function(err, connection){
        connection.query('SELECT * FROM blacklist limit 0,20;', function(err, rows){
            //console.log(rows);
            var data = new Array();
            for(var i = 0; i < rows.length; i ++){
                if(i > 50){
                    break;
                }
                data[i] = rows[i];
                    
            }
            res.render('blacklist', {
                screen_names: data,
                screen_names_length: data.length
            
            })
        })
        connection.release();
    })
}

module.exports.blacklist_add_friends = function(req, res){
    var py_file = '/home/iot/cf/nodejs/T4281/python_script/requests_friends.py';
    var screen_name = req.query.screen_name;
    var cmd = 'python ' + py_file + ' ' + screen_name;
    python = exec(cmd);
    var output = '';
    python.stdout.on('data', function(data){
        console.log('添加用户的好友：' + data);
        output = output = data + ", ";
    });
    python.on('exit', function(code){
        console.log('已将该用户的所有好友添加进黑名单中，代码：' + code);
    });
    res.render('blresult',{
        action: 'addFriends',
        screen_name: screen_name
    });
}

module.exports.blacklist_upload = function(req, res){//一次性最多上传100个screen_name
    var screen_names = '';
    var py_file = '/home/iot/cf/nodejs/T4281/python_script/user_lookup.py'
    form.parse(req, function(err, fields, files){
        //console.log('files.upload.path: ' + files.filePath.path);
        //console.log(util.inspect({fields: fields, files: files}));
        //fs.renameSync()
        readStream = fs.createReadStream(files.filePath.path);
        var rl = readline.createInterface({
            input: readStream,
            output: process.stdout
        });
        var i = 0;
        rl.on('line', function(data){
            i ++;
            if(data == 'end' || i >= 100){
                rl.close();
                console.log('The rl has been closed!');
                var cmd = 'python ' + py_file + ' ' + screen_names; //运行user_lookup.py脚本，通过screen_name获取对应的uid，并将它们存进mysql数据库
                console.log(cmd);
                python = exec(cmd);
                python.stdout.on('data', function(data){
                    console.log('user lookup: ' + data);
                });
                python.on('exit', function(code){
                    console.log('已从Twitter服务器获取screen_name对应的UID，状态码：' + code);
                    res.render('blresult', {});
                });
                //res.redirect(301, '/blacklist');
                //res.end();
                return;
            }
            console.log('The ' + i + 'th line: ' + data);
            if(i == 1){
                screen_names = data
            }
            else{
                screen_names = screen_names + "," + data;
            }
            //pool.query("INSERT IGNORE INTO blacklist values('" + data + "');");
        });
    });
}

module.exports.blacklist_dl = function(req, res){
    var py_file = '/home/iot/cf/nodejs/T4281/python_script/oauth.py';
    var cmd = 'python ' + py_file;
    python = exec(cmd);
    var output = '';
    python.stdout.on('data', function(data){
        console.log('标准输出：' + data);
        output = output + data + ", ";
    });
    python.on('exit', function(code){
        console.log('历史数据下载完毕，代码：' + code);
    });
    res.render('bldownload', {
        action: 'download'
    });
}

module.exports.blacklist_scan = function(req, res){
    var params = {
        with:'wenyunchao'
    };
    stream.stream(params);
    stream.on('data', function(json){
        console.log(json);
    });
    stream.on('connected', function(){
        console.log('We have connected successfully!');
    });
}

module.exports.blacklist_add = function(req, res){
    var screen_name = req.query.screen_name;
    var py_file = '/home/iot/cf/nodejs/T4281/python_script/user_lookup.py'
    var cmd = 'python ' + py_file + ' ' + screen_name; //运行user_lookup.py脚本，通过screen_name获取对应的uid，并将它存进mysql数据库
    console.log(cmd);
    python = exec(cmd);
    python.stdout.on('data', function(data){
        console.log('user lookup: ' + data);
    });
    python.on('exit', function(code){
        console.log('已从Twitter服务器获取screen_name对应的UID，状态码：' + code);
        res.render('blresult', {
            action: "add",
            screen_name: screen_name
        });
    });
    //pool.query("INSERT IGNORE INTO blacklist values('" + screen_name + "', 0, 0);");
    res.render('blresult', {
        action: "add",
        screen_name: screen_name
    });
}
module.exports.blacklist_del = function(req, res){
    var screen_name = req.query.screen_name;
    pool.query("delete from blacklist where screen_name='" + screen_name + "';");
    res.render('blresult', {
        action: "del",
        screen_name: screen_name
    });
}

module.exports.db=function(req, res){

    if(req.params.db == "mysql"){
        res.render('db', {dbName: 'mysql'});
    }
    else{
        res.render('db',{dbName: 'couchdb'})
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
