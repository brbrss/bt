var express = require('express');
var router = express.Router();
let controller = require('../model/controller');

/* GET home page. */
router.get('/announce', function (req, res, next) {
  console.log('announce call: ',req.query);
  const ip = req.socket.remoteAddress;

  const msg = controller.announce(req.query,ip);
  res.type('text/plain').send(msg);
});

module.exports = router;
