import argparse
import os
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

# Function to read CIDR addresses from files in a directory
def read_cidr_from_files(directory):
    cidr_list = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            with open(filepath, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        try:
                            cidr = ipaddress.IPv4Network(line)
                            cidr_list.append(cidr)
                        except ValueError:
                            print(f"Invalid CIDR address in file {filename}: {line}")
    return cidr_list

# Function to read domains from a file
def read_domains_from_file(file_path):
    domains = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                domains.append(line)
    return domains

def main():
    parser = argparse.ArgumentParser(description="Process CIDR addresses and domains from files.")
    parser.add_argument('directory', type=str, help='Directory containing files with CIDR addresses')
    parser.add_argument('domains_file', type=str, help='File containing the domains')
    args = parser.parse_args()

    if not check_tor_service():
        print("The Tor service is not active. Please ensure Tor is running.")
        exit(1)

    domains = read_domains_from_file(args.domains_file)
    cidr_list = read_cidr_from_files(args.directory)
    ip_list = [ip for cidr in cidr_list for ip in cidr]
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
