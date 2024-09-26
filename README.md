# Domain Check

This project allows you to verify and log responses from various domains through the Tor network. It uses IP addresses from a specified CIDR range to resolve each domain and capture the HTML response, including the page title.

## Description

The `domain_check.py` script performs the following functions:

- Checks if the Tor service is active.
- Makes HTTP and HTTPS requests to the specified domains using IPs in the CIDR range.
- Extracts the title from the HTML response.
- Stores the results in a SQLite database, including the domain, protocol, IP, response, and title.

Additionally, you can use `domain_check_dir.py` to process domains from a text file and read multiple CIDR range files from a directory.

```bash
$ python3.7 domain_check_dir.py -h
usage: domain_check_dir.py [-h] directory domains_file

Process CIDR addresses and domains from files.

positional arguments:
  directory     Directory containing files with CIDR addresses
  domains_file  File containing the domains

optional arguments:
  -h, --help    show this help message and exit
```

## Requirements

Make sure to have the following requirements installed:

- Python 3.x
- Necessary Python packages (listed in `requirements.txt`)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/N4rr34n6/DomainCheck.git
   cd DomainCheck
   ```

2. Install the dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

3. Ensure that Tor is installed and running. You can install Tor by following the [official instructions](https://2019.www.torproject.org/docs/tor-manual.html.en).

## Usage

### Using `domain_check.py`

Run the script with the following command:
```bash
python3.7 domain_check.py
```

### Using `domain_check_dir.py`

To process domains from a file and CIDR ranges from a directory, use the following command:
```bash
python domain_check_dir.py <CIDR_DIRECTORY> <DOMAINS_FILE>
```

- `<CIDR_DIRECTORY>`: Path to the directory containing CIDR address files.
- `<DOMAINS_FILE>`: Path to the file containing the domains to process.

## Database Structure

The `domain_responses.db` database contains a table named `domain_responses` with the following structure:

- `id`: Unique identifier (INTEGER)
- `domain`: Domain name (TEXT)
- `protocol`: Protocol used (HTTP/HTTPS) (TEXT)
- `ip`: IP address used for the request (TEXT)
- `response`: Full response from the server (TEXT)
- `title`: Title extracted from the HTML response (TEXT)
- `timestamp`: Timestamp of the entry (DATETIME)

## Contributions

Contributions are welcome. If you would like to contribute, please open an issue or submit a pull request.

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). See the [LICENSE](LICENSE) file for more details.
