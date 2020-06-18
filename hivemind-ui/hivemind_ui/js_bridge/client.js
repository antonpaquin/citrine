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
            console.log(msg);
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

    getFileUrl(fileRef) {
        let key = fileRef.file_ref;
        let url = "http://" + this.daemon.server + ":" + this.daemon.port + "/result/" + key;
        return url;
    }
}

var hivemindClient = new HivemindClient();

class HivemindUtil {
    constructor() {
    }

    encodeImageTensor(imgElem, alpha) {
        if (alpha === undefined) {
            alpha = false;
        }
        let img_data;
        if (imgElem.nodeName == 'CANVAS') {
            let ctx = imgElem.getContext('2d');
            img_data = ctx.getImageData(0, 0, imgElem.width, imgElem.height);
        } else if (imgElem.nodeName == 'IMG') {
            let canvas = document.createElement('canvas');
            canvas.width = imgElem.naturalWidth;
            canvas.height = imgElem.naturalHeight;
            let ctx = canvas.getContext('2d');
            ctx.drawImage(imgElem, 0, 0);
            img_data = ctx.getImageData(0, 0, imgElem.naturalWidth, imgElem.naturalHeight);
        } else {
            throw "encodeImageTensor input should be an <img> or a <canvas>";
        }
        let data = img_data.data;
        let res = [];
        let b64map = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        for (let ii=0; ii<data.length;) {
            let c1 = data[ii++];
            let c2 = data[ii++];
            let c3 = data[ii++];
            if (!alpha) {
                ii++;
            }

            res.push(b64map[c1>>2]);
            res.push(b64map[((c1 & 3) << 4) | (c2 >> 4)]);
            if (isNaN(c2)) {
                res.push('=');
            } else {
                res.push(b64map[((c2 & 15) << 2) | (c3 >> 6)]);
            }
            if (isNaN(c3)) {
                res.push('=');
            } else {
                res.push(b64map[(c3 & 63)])
            }
        }
        let shape = [img_data.height, img_data.width];
        if (alpha) {
            shape.push(4);
        } else {
            shape.push(3);
        }
        return {
            data: res.join(''),
            shape: shape,
            dtype: "uint8",
        }
    }

    decodeImageTensor(tensor) {
        if (tensor.dtype !== "uint8") {
            throw "Image tensor must be uint8"
        }
        let alpha = (tensor.shape[2] === 4);
        let canvas = document.createElement('canvas');
        canvas.height = tensor.shape[0];
        canvas.width = tensor.shape[1];
        let ctx = canvas.getContext('2d');
        let img_data = ctx.createImageData(tensor.shape[0], tensor.shape[1]);
        let jj = 0;
        let b64map = new Map();
        let b64key = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        for (let ii=0; ii<b64key.length; ii++) {
            b64map.set(b64key[ii], ii);
        }
        for (let ii=0; ii<tensor.data.length; ) {
            let e1 = b64map.get(tensor.data[ii++]);
            let e2 = b64map.get(tensor.data[ii++]);
            let e3 = b64map.get(tensor.data[ii++]);
            let e4 = b64map.get(tensor.data[ii++]);

            img_data.data[jj++] = (e1 << 2) | (e2 >> 4);
            if (e3 !== '=') {
                img_data.data[jj++] = ((e2 & 15) << 4) | (e3 >> 2);
            }
            if (e4 !== '=') {
                img_data.data[jj++] = ((e3 & 3) << 6) | (e4);
            }
            if (!alpha) {
                img_data.data[jj++] = 255;
            }
        }
        return img_data;
    }
}

var hivemindUtil = new HivemindUtil();
