from bs4 import BeautifulSoup
import requests
import pandas as pd
from flask import Flask, request, jsonify
import time
from seleniumwire import webdriver
import os
from flask import send_file

app = Flask(__name__)

def fetch_account_data(page_num):
    account_number=146040







    # Query parameters

    scraped_data = []

    options = webdriver.ChromeOptions()
    # options.add_argument(r'--profile-directory=C:\\Users\\Ahmad\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 3')
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    prefs = {"profile.managed_default_content_settings.images": 2}
    #options.headless = True

    options.add_experimental_option("prefs", prefs)

    windows_user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    scraped_data = {}
    

    options.add_argument(f"--user-agent={windows_user_agent}")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)

    driver.get(
        f'https://taxes.ci.newark.nj.us/ViewPay?accountNumber={str(account_number)}')
   
    headers = {
        "Host": "taxes.ci.newark.nj.us",
        "Sec-Ch-Ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.199 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://taxes.ci.newark.nj.us/?page=2" ,
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Priority": "u=0, i",
            }

    

    driver.get(
        f'https://taxes.ci.newark.nj.us/?page={page_num}')
    cookies=driver.get_cookies()
    driver.quit()
    cookies_dict = {}
    for cookie in cookies:
        cookies_dict[cookie['name']] = cookie['value']
    time.sleep(2)

    headers = ''
    for request in driver.requests:
        if request.response:
            headers = request.headers

    url = "https://taxes.ci.newark.nj.us/"

    querystring = {"page": str(page_num)}

    response = requests.get(url, headers=headers,cookies=cookies_dict, params=querystring)
    #print(response.text)
    
    soup = BeautifulSoup(response.text, 'lxml')

    # Find the table
    table = soup.find('table', {'class': 'table'})

    # Extract the account numbers
    account_numbers = []
    for row in table.find_all('tr')[1:]:  # Skipping the header row
        first_td = row.find('td')
        if first_td:
            account_numbers.append(first_td.get_text(strip=True))

    # Iterate over each account number
    for account_number in account_numbers:
        url = "https://taxes.ci.newark.nj.us/ViewPay"

        querystring = {"accountNumber": str(account_number)}
        response = requests.get(url, headers=headers, cookies=cookies_dict, params=querystring)
        account_data=response.text
        rowdat = extract_information(response.text)
        soup = BeautifulSoup(account_data, 'html.parser')

        table_data = get_firsttable_data(soup, first_expected_headers)
        secondtable = extract_data_from_html(account_data)
        print(table_data)
        combined_data = {**rowdat, **table_data, **secondtable}

        df = pd.DataFrame([combined_data])
        

        #print(account_data)







    return df


#account_data = fetch_account_data("3")
#soup = BeautifulSoup(account_data, 'html.parser')

# Helper function to extract text by row label
def extract_information(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    rows = soup.find_all('div', class_='row')
    data_dict = {}
    start_appending = False  # Flag to start appending data after Account# is found
    stop_appending = False  # Flag to stop appending data after L.Pay Date is found

    for row in rows:
        cols = row.find_all('div', recursive=False)
        for i in range(0, len(cols), 2):  # step by 2 to get label and value pairs
            label_col = cols[i]
            value_col = cols[i + 1] if i + 1 < len(cols) else None

            # Get the text for the label and value
            label = label_col.get_text(strip=True).rstrip(':')
            value = value_col.get_text(strip=True) if value_col and value_col.span else None

            if label == 'Account#':
                start_appending = True
                data_dict = {}  # Reset the dictionary to remove previous data

            if start_appending and not stop_appending:
                # Check for special case 'B/L/Q:'
                if label == 'B/L/Q':
                    parts = value.split('/')
                    data_dict['B'] = parts[0].strip() if parts[0].strip() else 'N/A'
                    data_dict['L'] = parts[1].strip() if len(parts) > 1 and parts[1].strip() else 'N/A'
                    data_dict['Q'] = parts[2].strip() if len(parts) > 2 and parts[2].strip() else 'N/A'
                else:
                    data_dict[label] = value if value else 'N/A'

                # Stop appending after L.Pay Date
                if label == 'L.Pay Date':
                    stop_appending = True
                    break  # Exit loop after L.Pay Date

    return data_dict

# Helper function to extract data from table
first_expected_headers = [
    "Certificate", "Date of Sale", "Amount", "Subsequents",
    "Type", "Status", "Lien Holder"
]


# Function to check if the table headers match expected headers
def first_headers_match(first_expected_headers, actual_headers):
    return all(eh.strip() == ah.strip() for eh, ah in zip(first_expected_headers, actual_headers))


# Function to extract data from the table
def get_firsttable_data(soup, header_labels):
    # Find all tables
    tables = soup.find_all('table', {'class': 'table'})

    # List to hold all rows data
    all_rows_data = []
    row_data = {header: 'N/A' for header in header_labels}
    # Process each table
    for table in tables:
        # Get current table headers
        current_headers = [header.get_text(strip=True) for header in table.find_all('th')]

        # Check if the current table headers match the expected headers
        if first_headers_match(header_labels, current_headers):
            # Extract data rows from the table
            for row in table.find_all('tr')[1:]:  # Skipping the header row
                cols = row.find_all('td')

                for label, col in zip(header_labels, cols):
                    # Assign 'N/A' if the column is empty or None, otherwise get text
                    row_data[label] = 'N/A' if col is None else col.get_text(strip=True)
                #all_rows_data.append(row_data)

    return row_data


def extract_data_from_html(html_content):
    # Load the HTML content into BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all tables
    tables = soup.find_all('table')

    # Define the headers we're looking for
    target_headers = ["Year", "Qtr", "Tr. / Due Date", "Description", "Billed", "Paid", "Open Balance", "Days",
                      "Interest Due", "Paid By"]

    # This will store our extracted data
    extracted_data = {}

    # Search through each table
    for table in tables:
        # Get all header elements
        headers = [header.get_text(strip=True) for header in table.find_all('th')]

        # Check if this table has the headers we're looking for
        if headers[:len(target_headers)] == target_headers:
            # If so, process this table
            rows = table.find_all('tr')
            paid_by_counter = 0

            # Skip the header row and iterate through the rest
            for row in rows[1:]:
                cols = row.find_all('td')
                if len(cols) == len(target_headers):  # Ensure the row has the correct number of columns
                    # Check if the 10th <td> (index 9) has a value
                    if cols[9].get_text(strip=True):
                        # Add the data to the dictionary, with labels as specified
                        extracted_data[f'Paid_by_{paid_by_counter}'] = cols[9].get_text(strip=True)
                        extracted_data[f'Tr._Date_{paid_by_counter}'] = cols[2].get_text(strip=True)
                        paid_by_counter += 1

    return extracted_data


# Define headers and extract data
headers = [
    "Account#", "Principal", "Owner", "Bank Code", "Interest", "Address",
    "Deductions", "Total", "City/State", "Int.Date", "Location", "B",
    "L", "Q", "L.Pay Date", "Certificate", "Date of Sale", "Amount",
    "Subsequents", "Type", "Status", "Lien Holder", "Paid_by_0",
    "Tr. Date 0", "Paid_by_1", "Tr. Date 1", "Paid_by_2", "Tr. Date 2",
    "Paid_by_3", "Tr. Date 3", "Paid_by_4", "Tr. Date 4", "Paid_by_5",
    "Tr. Date 5", "Paid_by_6", "Tr. Date 6"
]





@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        page_number = request.form.get('page_number')
        print(f"Page number received: {page_number}")  # Debug print
        return f'''
        <html>
            <head>
                <title>Download File</title>
            </head>
            <body>
                <script>
                    setTimeout(function() {{
                        window.location.href = '/download?page_number={page_number}';
                    }}, 3000);  // 3000 milliseconds delay
                </script>
                Please wait, processing...
            </body>
        </html>
        '''
    return '''
    <html>
        <body>
            <form method="post">
                Page Number: <input type="text" name="page_number"><br>
                <input type="submit" value="Submit">
            </form>
        </body>
    </html>
    '''

@app.route('/download')
def download():
    page_number = request.args.get('page_number', type=int, default=1)
    print(f"Downloading data for page number: {page_number}")  # Debug print
    excel_file_path = 'output.xlsx'  # Excel file path

    new_data = fetch_account_data(page_number)

    if os.path.exists(excel_file_path):
        # Read existing data and append new data
        existing_data = pd.read_excel(excel_file_path)
        combined_data = pd.concat([existing_data, new_data], ignore_index=True)
    else:
        combined_data = new_data

    # Write the combined data to the Excel file
    with pd.ExcelWriter(excel_file_path, engine='xlsxwriter') as writer:
        combined_data.to_excel(writer, index=False)

    return send_file(excel_file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

