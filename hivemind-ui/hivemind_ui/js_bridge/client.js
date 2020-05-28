class HivemindClient {
    constructor() {
        // Magic constants bound by the javascript injection function
        this._connection = new WebSocket("ws://localhost:" + _hivemind_port + "/" + _hivemind_key);
        this.daemon = {
            server: _hivemind_daemon_server,
            port: _hivemind_daemon_port,
        };

        this._callbacks = new Map();
        this._request_id = 0;

        this._run_cmd = this._run_cmd.bind(this);
        this._onmessage = this._onmessage.bind(this);

        this._connection.onmessage = this._onmessage;
    }

    _run_cmd(cmd, params, callback) {
        let id = this._request_id;
        this._request_id += 1;
        let msg = JSON.stringify({
            cmd: cmd,
            params: params,
            id: id
        });
        this._callbacks.set(id, callback);
        this._connection.send(msg);
    }

    _onmessage(event) {
        let msg = event.data;
        let jsn = JSON.parse(msg);
        if (jsn.success) {
            let resp = jsn.results;
            let id = jsn.id;
            let callback = this._callbacks.get(id);
            this._callbacks.delete('id');
            callback(resp);
        } else {
            /* TODO handle errors */
            console.log(resp);
        }
    }

    heartbeat(callback) {
        this._run_cmd('heartbeat', {}, callback);
    }

    run(target, params, callback) {
        let _params = {
            target: target,
            params: params,
        };
        this._run_cmd('run', _params, callback);
    }

    _run(target, params, callback) {
        let _params = {
            target: target,
            params: params,
        };
        this._run_cmd('_run', _params, callback);
    }

    result(result_hash, callback) {
        let _params = {
            result_hash: result_hash,
        };
        this._run_cmd('result', _params, callback);
    }

    packageInstall(package_spec, callback) {
        this._run_cmd('package.install', package_spec, callback);
    }

    packageFetch(package_spec, callback) {
        this._run_cmd('package.fetch', package_spec, callback);
    }

    packageActivate(name, version, callback) {
        let _params = {
            name: name,
            version: version,
        }
        this._run_cmd('package.activate', _params, callback);
    }

    packageDeactivate(name, version, callback) {
        let _params = {
            name: name,
            version: version,
        }
        this._run_cmd('package.deactivate', _params, callback);
    }

    packageRemove(name, version, callback) {
        let _params = {
            name: name,
            version: version,
        }
        this._run_cmd('package.remove', _params, callback);
    }

    packageList(callback) {
        this._run_cmd('package.list', {}, callback);
    }

    getDaemon(callback) {
        this._run_cmd('bridge.get_daemon', {}, callback);
    }

    getFileUrl(fileresult) {
        let url = "http://" + this.daemon.server + ":" + this.daemon.port + "/result/" + fileresult;
        return url;
    }
}

var hivemindClient = new HivemindClient();
