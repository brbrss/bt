
function strname(ip, port) {
    return ip + '' + port;
}

class PeerDb {
    constructor() {
        this.db = {};
    }

    add(info_hash, ip, port, completed) {
        const entry = { ip, port, time: new Date(), completed };
        if (info_hash in this.db) {
        } else {
            this.db[info_hash] = {};
        }
        const name = strname(ip, port);
        this.db[info_hash][name] = entry;
        return name;
    }
    remove(info_hash, ip, port) {
        const entry = { ip, port, time: new Date() };
        if (info_hash in this.db) {
        } else {
            this.db[info_hash] = {};
        }
        const name = strname(ip, port);
        delete this.db[info_hash][name];
    }
    get(info_hash) {
        if (info_hash in this.db) {
            const arr = []
            for (entry of this.db[info_hash]) {
                const d = { ip: entry.ip, port: entry.port };
                arr.push(d);
            }
            return arr;
        } else {
            return [];
        }
    }
    complete(info_hash, name) {
        if (info_hash in this.db) {
            if (name in this.db[info_hash]){
                this.db[info_hash][name].completed = true
            }
        } 
    }

};

/**
 * Global instance of database
 */
const db = new PeerDb();

module.exports = db;