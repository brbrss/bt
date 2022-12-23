from btclient import BtClient
from torrent import Torrent
from peer import Peer


def b(x):
    if x:
        return 'Y'
    else:
        return 'N'


def print_torrent(t: Torrent):
    n_complete = len(t.fm.complete_pieces)
    n_incomplete = len([d for d in t.fm.buffer if d])
    n_total = len(t.pieces_hash)
    n_peer = len(t.peer_map)
    print('length:', t.length, end=' ')
    print('complete/incomplete/total:', n_complete,
          '/', n_incomplete, '/', n_total, end='')
    print(' peer:', n_peer, end=' ')
    if t.is_complete():
        print('complete')
    else:
        print('')


def print_peer(peer: Peer):
    addr = peer.conn.getpeername()
    n_local_req = len(peer.local_request)
    n_remote_req = len(peer.remote_request)
    n_remote_pieces = len(peer.remote_pieces)
    print('peer-', addr, end=' ')
    print('req', n_local_req, '/', n_remote_req, end=' ')
    print('choke', b(peer.local_choke), '/', b(peer.remote_choke), end=' ')
    print('interest', b(peer.local_interested),
          '/', b(peer.remote_interested), end=' ')
    print('pieces', n_remote_pieces, end=' ')
    print('d_rate', peer.d_rate())


class Main(object):
    def __init__(self, bt: BtClient):
        self.bt = bt

    def cmd(self, args):
        m = {'status': self.status,
             'quit': self.quit,
             'refresh': self.refresh,
             'add': self.add,
             'peer': self.peer
             }

        c = args[0]
        if c in m:
            m[c](args)
        else:
            print('Unknown cmd:', args[0])

    def status(self, args):
        n = len(self.bt.torrent_list)
        print('Num of torrents: ', n)
        for k in self.bt.torrent_list:
            print_torrent(self.bt.torrent_list[k])
        return

    def quit(self, args):
        self.bt.stop()

    def refresh(self, args):
        for k in self.bt.torrent_list:
            t = self.bt.torrent_list[k]
            t.tracker_get(t.announce, '')
        print('refreshed all trackers')

    def add(self, args):
        if len(args) < 3:
            print('invalid args')
            return
        fp = args[1]
        dst = args[2]
        res = self.bt.create_torrent(fp, dst)
        if res is None:
            print('added torrent file')
        else:
            print(res)

    def peer(self, args):
        n_peers = 0
        for k in self.bt.torrent_list:
            t = self.bt.torrent_list[k]
            for url in t.tracker_map:
                n_peers += len(t.tracker_map[url].peers)
            print('torrent', t.info_hash, 'peers', n_peers)
            for pk in t.peer_map:
                print_peer(t.peer_map[pk])
        return


if __name__ == '__main__':
    bt = BtClient()
    bt.start()
    # fp = './dldata/hasthree.torrent'
    # folder = './dldata'
    # bt.create_torrent(fp, folder)

    main = Main(bt)
    quit_flag = False
    while not quit_flag:
        s = input()
        args = s.split(' ')
        if args[0] == 'quit':
            quit_flag = True
        main.cmd(args)
    print('program end')
