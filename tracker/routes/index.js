var express = require('express');
var router = express.Router();
let db = require('./model/peerdb');

/* GET home page. */
router.get('/', function (req, res, next) {
  console.log(req.query);
  const ip = req.socket.remoteAddress;
  const port = req.query.port;
  const info_hash = req.query.info_hash;
  const event = req.query.event;
  if(event==='started'){
    const peerList = db.get(info_hash);
    db.add(info_hash,ip,port);

  }else if(event==='stopped'){
    db.remove(info_hash,ip,port);
  }else if (event==='completed'){
    //
  }else{ // or not set

  }
  db.add(info_hash,ip,port);
  let msg = (new Date()).toString();
  res.send('from tracker at: ' + msg);
});

module.exports = router;
