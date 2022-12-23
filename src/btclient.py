from conn_pool import ConnPool
from peer import Peer
from torrent import Torrent
import threading
import concurrent.futures
import time
import socket


def peer_address(ip: tuple[int, int, int, int], port: int):
    address = ('.'.join([str(i) for i in ip]), port)
    return address


class BtClient(object):
    '''One listening thread for each torrent, plus one socket pool thread'''

    def __init__(self):
        def cb(): return self.refresh_cb()
        self.conn_pool = ConnPool(cb)
        self.torrent_list: dict[bytes, Torrent] = {}
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.worker_thread = None
        return

    def create_torrent(self, fp, folder):
        t = Torrent(fp, folder)
        self.torrent_list[t.info_hash] = t
        def cb(s): return self.add_conn(s, t, False)
        t.start(cb)
        return

    def start(self):
        def f(): return self.conn_pool.run()
        self.worker_thread = threading.Thread(target=f)
        self.worker_thread.start()

    def stop(self):
        for t in self.torrent_list:
            self.torrent_list[t].close()
        self.conn_pool.close()

    def check(self):
        for t in self.torrentList:
            t.refresh()
        pass

    def refresh_cb(self):
        for k in self.torrent_list:
            t = self.torrent_list[k]
            self.refresh_torrent(t)
        return

    def refresh_torrent(self, t: Torrent):
        self.purge_peer(t)
        self.refresh_tracker(t)
        self.refresh_peer(t)
        self.refresh_status(t)
        self.refresh_request(t)
        return

    def purge_peer(self, t: Torrent):
        d = {}
        for k in t.peer_map:
            p = t.peer_map[k]
            if p.conn.fileno() != -1:
                d[k] = p
        t.peer_map = d

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
        '''Add connection to peer.
        Peer address should be from tracker'''
        def _f():
            address = peer_address(ip, port)
            conn = socket.socket()
            try:
                conn.connect(address)
            except:
                return
            self.add_conn(conn, t, True)
        self.executor.submit(_f)

    def refresh_peer(self, t: Torrent):
        if not t.fresh:
            return
        t.fresh = False
        for tracker_url in t.tracker_map:
            tracker = t.tracker_map[tracker_url]
            for pid in tracker.peers:
                ip, port = pid
                p_addr = peer_address(ip, port)
                if p_addr not in t.peer_map:
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

    def add_conn(self, conn: socket.socket, torrent: Torrent, is_initiating):
        ip, port = conn.getpeername()
        torrent.lock_peer.acquire()
        if (ip,port) not in torrent.peer_map:
            p = Peer(conn, torrent, is_initiating)
            torrent.add_peer(ip, port, p)
            self.conn_pool.register(p)
        else:
            conn.close()
        torrent.lock_peer.release()
