from conn_pool import ConnPool
from peer import Peer
from torrent import Torrent
import threading
import concurrent.futures
import time
import socket


class BtClient(object):
    '''One listening thread for each torrent, plus one socket pool thread'''

    def __init__(self):
        def cb(): return self.refresh_cb()
        self.conn_pool = ConnPool(cb)
        self.torrent_list = {}
        #self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.worker_thread = None
        return

    def create_torrent(self, fp, folder):
        t = Torrent(fp, folder)
        self.torrent_list[t.info_hash] = t
        def cb(s): return self.add_conn(s, self, False)
        t.start(cb)
        return

    def start(self):
        def f(): return self.conn_pool.run()
        self.worker_thread = threading.Thread(target=f)

    def stop(self):
        for t in self.torrent_list:
            t.server.close()

        self.conn_pool.close()

    def check(self):
        for t in self.torrentList:
            t.refresh()
        pass

    def refresh_cb(self):
        for t in self.torrent_list:
            self.refresh_torrent(t)
        return

    def refresh_torrent(self, t: Torrent):
        fresh_tracker = self.refresh_tracker(t)
        if fresh_tracker:
            self.refresh_peer(t)
        self.refresh_status(t)
        self.refresh_request(t)
        return

    def refresh_tracker(self, t: Torrent):
        '''return whether is refreshed'''
        now = time.time()
        tracker_url = t.announce
        tracker = t.tracker_map[tracker_url]
        if tracker.last_time - now > tracker.interval:
            t.tracker_get(tracker_url)
            return True
        return False

    def _add_peer(self, t: Torrent, ip: tuple[int, int, int, int], port: int):
        address = ('.'.join(ip), port)
        conn = socket.socket()
        conn.connect(address)
        p = Peer(conn, t, True)
        t.add_peer(ip, port, p)

    def refresh_peer(self, t: Torrent):
        for tracker_url in t.tracker_map:
            tracker = t.tracker_map[tracker_url]
            for pid in tracker.peers:
                if pid not in t.peer_map:
                    ip, port = pid
                    self._add_peer(t, ip, port)
        return

    def refresh_status(self, t: Torrent):
        now = time.time()
        if now - t.last_choke_time > 29:
            t.decide_choke()
        if now - t.last_interest_time > 9.9:
            t.decide_interest()
        return

    def _fill_req(self, t: Torrent, peer: Peer):
        '''call peer.add_request as many times as appropriate'''
        MAX_PEER_REQ = 8
        n = len(peer.local_request)  # cur no of req
        for i in range(n, MAX_PEER_REQ):
            res = t.decide_request(peer)
            if res is None:  # peer has no available data
                return
            else:
                peer.add_request(res)  # add request
        return

    def refresh_request(self, t: Torrent):
        for k in t.peer_map:
            peer = t.peer_map[k]
            if peer.local_interested and not peer.remote_choke:
                self._fill_req(t, peer)
        return

    def add_conn(self, conn, torrent, is_initiating):
        p = Peer(conn, torrent, is_initiating)
        self.conn_pool.register(p)
