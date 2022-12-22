from btclient import BtClient
from torrent import Torrent


def print_torrent(t: Torrent):
    n_complete = len(t.fm.complete_pieces)
    n_incomplete = len([d for d in t.fm.buffer if d])
    n_total = len(t.pieces_hash)
    n_peer = len(t.peer_map)
    print('length:', t.length, end='')
    print('complete/incomplete/total:', n_complete,
          '/', n_incomplete, '/', n_total, end='')
    print(' peer:', n_peer)


class Main(object):
    def __init__(self, bt: BtClient):
        self.bt = bt

    def cmd(self, args):
        if args[0] == 'status':
            self.status(args)
        elif args[0] == 'quit':
            self.quit(args)
        elif args[0] == 'refresh':
            self.refresh(args)

    def status(self, args):
        n = len(self.bt.torrent_list)
        print('Num of torrents: ', n)
        for k in self.bt.torrent_list:
            print_torrent(self.bt.torrent_list[k])
        return

    def quit(self, argx):
        self.bt.stop()

    def refresh(self, args):
        for k in self.bt.torrent_list:
            t = self.bt.torrent_list[k]
            t.tracker_get(t.announce, '')


if __name__ == '__main__':
    bt = BtClient()
    bt.start()
    fp = './resource/gatsby2.torrent'
    folder = './resource'
    bt.create_torrent(fp, folder)

    main = Main(bt)
    quit_flag = False
    while not quit_flag:
        s = input()
        args = s.split(' ')
        if args[0] == 'quit':
            quit_flag = True
        main.cmd(args)
    print('program end')
