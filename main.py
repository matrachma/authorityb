#!/usr/bin/env python3
import os
import time
import mysql.connector
import requests
import random
import timeit
from bs4 import BeautifulSoup
from retrying import retry, RetryError
from datetime import datetime

total_proxy = 0
proxy_index = 0
proxy_hit_counter = 0
proxy_limit_hit = 45

db_conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', "localhost"),
    user=os.getenv('DB_USER', "root"),
    password=os.getenv('DB_PASSWORD', "root"),
    database=os.getenv('DB_NAME', "authorityb")
)


def get_domain():
    global db_conn

    my_cursor = db_conn.cursor()

    sql = "SELECT * FROM tbl_domain WHERE domain_result = '' OR domain_result IS NULL ORDER BY domain_id DESC "

    my_cursor.execute(sql)

    got_domains = my_cursor.fetchall()

    return got_domains


def update_domain(dom, result):
    global db_conn

    my_cursor = db_conn.cursor()

    sql_update = "UPDATE tbl_domain SET domain_result = %s , domain_date = %s WHERE domain_id = %s"

    data = (result, datetime.today().strftime('%Y-%m-%d'), dom[0])

    print("{} updating tbl_domain with id: {}".format(datetime.now(), dom[0]))
    my_cursor.execute(sql_update, data)

    db_conn.commit()
    print("{} updated".format(datetime.now()))


def get_proxies():
    global db_conn
    global total_proxy
    list_proxy = []

    my_cursor = db_conn.cursor()

    sql = "SELECT * FROM tbl_proxy "

    my_cursor.execute(sql)

    got_proxies = my_cursor.fetchall()

    for proxy in got_proxies:
        list_proxy.append("{}:{}@{}:{}".format(proxy[3], proxy[4], proxy[1], proxy[2]))
    total_proxy = len(list_proxy)
    return list_proxy


def run():
    global proxy_index
    global proxy_hit_counter
    global proxy_limit_hit
    global total_proxy

    total_processed = 0
    total_error = 0
    with open('user-agents.txt') as f:
        user_agents = [line.rstrip() for line in f]

    proxy_list = get_proxies()

    domain_to_check = get_domain()

    tic = timeit.default_timer()
    for d in domain_to_check:
        url = "https://www.google.com/search?q={}".format(d[1])
        try:
            print("{} checking: {}".format(datetime.now(), url))
            result = setup_proxy(url, user_agents, proxy_list)
            print("{} got result: {}".format(datetime.now(), result))
            update_domain(d, result)
            total_processed += 1
            proxy_hit_counter += 1
            if proxy_hit_counter > proxy_limit_hit:
                if proxy_index < total_proxy:
                    proxy_index += 1
                else:
                    proxy_index = 0
                proxy_hit_counter = 0
        except RetryError:
            print("{} error checking: {}".format(datetime.now(), url))
            print("{} result: x".format(datetime.now()))
            update_domain(d, "x")
            total_error += 1
            if proxy_index < total_proxy:
                proxy_index += 1
            else:
                proxy_index = 0
            continue

    toc = timeit.default_timer()
    print("{} Finish: elapsed time: {}, processed: {}, error: {}".format(datetime.now(), toc - tic, total_processed,
                                                                         total_error))
    f.close()
    # db_conn.close()


def retry_if_connection_refused_error(exception):
    """Return True if we should retry (in this case when it's an ConnectionRefusedError), False otherwise"""
    return isinstance(exception, ConnectionRefusedError)


def retry_if_attribute_error(exception):
    """Return True if we should retry (in this case when it's an AttributeError), False otherwise"""
    return isinstance(exception, AttributeError)


@retry(retry_on_exception=retry_if_connection_refused_error, wrap_exception=True, wait_fixed=100)
def setup_proxy(url, user_agents, proxy_list):
    global proxy_index
    proxies = {
        "https": "https://{}/".format(proxy_list[proxy_index]),
        "http": "http://{}/".format(proxy_list[proxy_index])
    }
    print("{} --- try using proxy: {}".format(datetime.now(), proxies["http"]))

    return check(url, user_agents, proxies)


@retry(retry_on_exception=retry_if_attribute_error, wait_exponential_multiplier=10, wait_exponential_max=100)
def check(url, user_agents, proxies):
    global proxy_index
    global total_proxy
    header = {
        "User-Agent": user_agents[random.randint(0, len(user_agents) - 1)]
    }
    print("{} --- --- try user-agent: {}".format(datetime.now(), header["User-Agent"]))
    r = requests.get(url, proxies=proxies, headers=header, verify=True)
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, 'html.parser')
    else:
        if proxy_index < total_proxy:
            proxy_index += 1
        else:
            proxy_index = 0
        if r.status_code == 429:
            print("{} --- --- got captcha on proxy: {}".format(datetime.now(), proxies["http"]))
            raise ConnectionRefusedError
        else:
            print("{} --- --- got another response error with status code: {}".format(datetime.now(), r.status_code))
            raise ConnectionError

    if soup.find(id="appbar") is not None:
        if soup.find(id="result-stats") is not None:
            result = soup.find(id="result-stats").text
        else:
            result = "-"
    else:
        raise AttributeError

    return result


def main():
    while True:
        run()
        print("{} get next batch after 10 minutes".format(datetime.now()))
        time.sleep(600)


if __name__ == '__main__':
    main()
