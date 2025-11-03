import fdb

def connect(database, user, password, host="localhost", port=3050):
    return fdb.connect(
        dsn=f"{host}/{port}:{database}",
        user=user,
        password=password
    )
