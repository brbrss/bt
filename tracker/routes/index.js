var express = require('express');
var router = express.Router();
let controller = require('../model/controller');

/* GET home page. */
router.get('/announce', function (req, res, next) {
  console.log('announce call: ', req.query);
  const ip = req.socket.remoteAddress;

  const msg = controller.announce(req.query, ip);
  let b = Buffer.from(msg,'latin1');
  res.type('text/plain').send(b);
});

router.get('/test', function (req, res, next) {
  let ar = [107, 0, 0, 1, 102, 156,220,255];
  let msg = '';
  for (let c of ar) {
    let cc = String.fromCharCode(c);
    msg += cc;
  }
  let b = Buffer.from(msg,'latin1');
  res.type('text/plain').send(b);
});


module.exports = router;
