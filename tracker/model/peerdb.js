

class PeerDb {
    constructor() {
        this.db = {};
    }
    strname(ip, port) {
        return ip + '>' + port; // > to prevent ipv6 colon confusion
    }

    add(info_hash, ip, port, completed) {
        const entry = { ip, port, time: new Date(), completed };
        if (info_hash in this.db) {
        } else {
            this.db[info_hash] = {};
        }
        const name = this.strname(ip, port);
        this.db[info_hash][name] = entry;
        return name;
    }
    remove(info_hash, ip, port) {
        const entry = { ip, port, time: new Date() };
        if (info_hash in this.db) {
        } else {
            this.db[info_hash] = {};
        }
        const name = this.strname(ip, port);
        delete this.db[info_hash][name];
    }
    get(info_hash, ip, port) {
        const reqname = this.strname(ip, port);

        if (info_hash in this.db) {
            const arr = []
            for (const name in this.db[info_hash]) {
                if (name != reqname) {
                    const entry = this.db[info_hash][name];
                    const d = { ip: entry.ip, port: entry.port };
                    arr.push(d);
                }
            }
            return arr;
        } else {
            return [];
        }
    }
    complete(info_hash, name) {
        if (info_hash in this.db) {
            if (name in this.db[info_hash]) {
                this.db[info_hash][name].completed = true
            }
        }
    }
    reset() {
        this.db = {};
    }
};

/**
 * Global instance of database
 */
const db = new PeerDb();

module.exports = db;