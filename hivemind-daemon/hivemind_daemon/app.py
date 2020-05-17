from hivemind_daemon import storage, server, package


def main():
    storage.init_storage()
    package.db.init_db()
    server.parallel.init_workers(n_workers=16)
    server.run_server('127.0.0.1', 5402)
