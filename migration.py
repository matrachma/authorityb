import mysql.connector
import os
import datetime

db_conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', "178.128.89.252"),
    user=os.getenv('DB_USER', "root"),
    password=os.getenv('DB_PASSWORD', "sLo8($;1-+slSj4j"),
    database=os.getenv('DB_NAME', "authorityb")
)


def migrate_domain(db):
    cursor = db.cursor()

    with open('listdomain.txt') as h:
        domains = [line.rstrip() for line in h]

    sql = "INSERT INTO tbl_domain (domain_name, domain_result) VALUES (%s, %s)"

    for domain in domains:
        val = (domain, "")
        cursor.execute(sql, val)
        db.commit()
    print(cursor.rowcount, "record inserted.")


def migrate_proxy(db):
    cursor = db.cursor()

    with open('proxies.txt') as g:
        proxy_list = [line.rstrip() for line in g]

    sql = "INSERT INTO tbl_proxy (proxy_ip, proxy_port, proxy_username, proxy_password) VALUES (%s, %s, %s, %s)"

    for proxy in proxy_list:
        first_split = proxy.split("@")
        uname_pswd, ip_port = first_split[0].split(":"), first_split[1].split(":")
        val = (ip_port[0], ip_port[1], uname_pswd[0], uname_pswd[1])
        cursor.execute(sql, val)
        db.commit()
    print(cursor.rowcount, "record inserted.")


def get_proxy(db):
    cursor = db.cursor()

    sql = "SELECT * FROM tbl_proxy "

    cursor.execute(sql)

    got_proxies = cursor.fetchall()

    for proxy in got_proxies:
        print("{}:{}@{}:{}".format(proxy[3], proxy[4], proxy[1], proxy[2]))


# migrate_domain(db_conn)
get_proxy(db_conn)
db_conn.close()
