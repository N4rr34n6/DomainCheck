from datetime import datetime
import sqlite3
import subprocess
import ipaddress
import socket
import socks
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from threading import Thread

# Function to check if the Tor service is running
def check_tor_service():
    try:
        sock = socket.create_connection(("127.0.0.1", 9050), timeout=5)
        sock.close()
        return True
    except (socket.error, socket.timeout):
        return False

# Function to execute curl with traffic through Tor
def run_curl_command(domain, protocol, ip):
    port = "443" if protocol == "https" else "80"
    command = f"curl --socks5 127.0.0.1:9050 --resolve '{domain}:{port}:{ip}' {protocol}://{domain}/ --max-time 10"
    try:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
        stdout = result.stdout.decode('utf-8')
        return stdout
    except subprocess.TimeoutExpired:
        return "Timeout"
    except Exception as e:
        return f"Error: {str(e)}"

# Function to extract the title from the HTML response
def extract_title(html_response):
    match = re.search(r'<title>(.*?)</title>', html_response, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

# Function to process an IP address
def process_ip(ip, domains, result_queue):
    for domain in domains:
        for protocol in ["https", "http"]:
            response = run_curl_command(domain, protocol, str(ip))
            title = extract_title(response)
            result_queue.put((domain, protocol, str(ip), response, title))

# Function to handle writing to the database
def db_writer(result_queue):
    conn = sqlite3.connect('domain_responses.db')
    cursor = conn.cursor()

    # Create the table if it does not exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS domain_responses (
        id INTEGER PRIMARY KEY,
        domain TEXT,
        protocol TEXT,
        ip TEXT,
        response TEXT,
        title TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    while True:
        domain, protocol, ip, response, title = result_queue.get()
        if domain is None:  # Exit signal
            break
        cursor.execute('''
            INSERT INTO domain_responses (domain, protocol, ip, response, title)
            VALUES (?, ?, ?, ?, ?)
        ''', (domain, protocol, ip, response, title))
        conn.commit()
    
    conn.close()

def main():
    if not check_tor_service():
        print("The Tor service is not active. Please ensure Tor is running.")
        exit(1)

    # Obfuscated domains and CIDR range
    domains = ["example1.xyz", "example2.xyz", "example3.xyz"]
    cidr_range = ipaddress.IPv4Network('192.0.2.0/24')  # Example CIDR range
    ip_list = list(cidr_range)
    random.shuffle(ip_list)

    result_queue = Queue()
    
    # Start the thread to write to the database
    writer_thread = Thread(target=db_writer, args=(result_queue,))
    writer_thread.start()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_ip, ip, domains, result_queue): ip for ip in ip_list}

        for future in as_completed(futures):
            ip = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"Error processing IP {ip}: {e}")

    # Signal the writer thread to terminate
    result_queue.put((None, None, None, None, None))
    writer_thread.join()

if __name__ == "__main__":
    main()
