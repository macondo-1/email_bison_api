import credentials as cred
import constants as const
import http.client
import json
import csv
import re

def make_api_call(method, api_call, payload):
    base_link = 'mail.sisconsult.co'
    conn = http.client.HTTPSConnection(base_link)

    headers = {
        #'Content-Type': "application/json",
        'Authorization': "Bearer {}".format(cred.api_token)
    }

    conn.request(method, api_call, payload, headers)

    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

    return data.decode("utf-8")

def list_campaigns():
    available_status = 'draft\n' \
    'launching\n' \
    'active\n' \
    'stopped\n' \
    'completed\n' \
    'paused\n' \
    'paused\n' \
    'failed\n' \
    'queued\n' \
    'archived'
    print('Available status:\n', available_status)
    status = input('Select 1 status: ')
    payload = {
        'status':'{}'.format(status)
    }
    payload = json.dumps(payload).encode('utf-8')
    api_call = '/api/campaigns'
    method = 'GET'
    records = make_api_call(method, api_call, payload)
    records = json.loads(records)
    with open('campaigns_info.csv', 'w') as file:
        fieldnames = records['data'][0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records['data'])

def create_a_campaign(campaign_name:str):
    payload = {
    "name": campaign_name,
    "type": "outbound"
    }
    payload = json.dumps(payload).encode('utf-8')
    api_call = '/api/campaigns'
    method = 'POST'
    data = make_api_call(method, api_call, payload)
    data = json.loads(data)
    campaign_id = data['data']['id']

    return campaign_id

def update_campaign_settings(max_emails_per_day:int, campaign_id:int):
    # modify: this payload should be automated to do as one pleases
    #payload = "{\"name\": \"New Campaign Name\",\n  \"max_emails_per_day\": 500,\n  \"max_new_leads_per_day\": 100,\n  \"plain_text\": true,\n  \"open_tracking\": true,\n  \"reputation_building\": true,\n  \"can_unsubscribe\": true,\n  \"unsubscribe_text\": \"Click here to unsubscribe\"}"
    payload = {
        'max_new_leads_per_day':'{}'.format(max_emails_per_day),
        'max_emails_per_day':'{}'.format(max_emails_per_day),
        'plain_text':True,
        'open_tracking':False
    }
    payload = json.dumps(payload).encode('utf-8')
    method = 'PATCH'
    api_call = '/api/campaigns/{}/update'.format(campaign_id)
    make_api_call(method, api_call, payload)

def create_campaign_schedule(campaign_id:int, timezone):

    payload = "{\"monday\": true,\n  \"tuesday\": true,\n  \"wednesday\": true,\n  \"thursday\": true,\n  \"friday\": true,\n  \"saturday\": false,\n  \"sunday\": false,\n  \"start_time\": \"09:00\",\n  \"end_time\": \"17:00\",\n  \"timezone\": \"America/New_York\",\n  \"save_as_template\": false}"
    payload = {
        'monday':True,
        'tuesday':True,
        'wednesday':True,
        'thursday':True,
        'friday':True,
        'saturday':False,
        'sunday':False,
        'start_time':'09:00',
        'end_time':'17:00',
        'timezone':'{}'.format(timezone),
        'save_as_template':False
    }
    payload = json.dumps(payload).encode('utf-8')
    method = 'POST'
    api_call = '/api/campaigns/{}/schedule'.format(campaign_id)
    make_api_call(method, api_call, payload)

def create_sequence_steps(campaign_id:int, filename:str):
    # modify: subject test and body test must be typed or read
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.readlines()
        subject = content[0]
        body = ''.join(content[1:])
        print('subject: ', subject)
        print('body: ', body)

    payload = {
        'title':'blast message sequence',
        'sequence_steps':[{
            'email_subject':'{}'.format(subject),
            'email_body':'{}'.format(body),
            'wait_in_days':'1'
        }]
    }
    payload = json.dumps(payload).encode('utf-8')
    method = 'POST'
    api_call = '/api/campaigns/{}/sequence-steps'.format(campaign_id)
    make_api_call(method, api_call, payload)

def bulk_create_leads(filename):
    file_path = '/Users/albertoruizcajiga/Documents/Documents - Alberto’s MacBook Air/final_final/to_process/'
    file_name = file_path + filename
    a = []
    with open(file_name) as file:
        records = csv.DictReader(file)
        for record in records:
            a.append(record)

    count = 0
    records_dict = {}
    records_dict['leads'] = a
    remaining_dict = {}

    if len(records_dict['leads']) > 500:
        while len(records_dict['leads']) > 500:
            records_dict['leads'] = records_dict['leads'][:500]
            remaining_dict['leads'] = records_dict['leads'][500:]
            payload = records_dict
            for x in payload['leads']:
                x['last_name'] = 'None'
            payload = json.dumps(payload).encode('utf-8')
            method = 'POST'
            api_call = '/api/leads/multiple'
            data = make_api_call(method, api_call, payload)

            leads_dict = json.loads(data)

            if 'errors' in leads_dict.keys(): #modify: figure out why it fails here?
                delete_index = []
                for x in leads_dict['errors'].keys():
                    delete_index.append(int(x.split('.')[1]))

                delete_index.reverse()
                for x in delete_index:
                    del records_dict['leads'][x]

                payload = records_dict
                payload = json.dumps(payload).encode('utf-8')
                data = make_api_call(method, api_call, payload)

            append_new_leads()
            records_dict['leads'] = remaining_dict['leads']

    else:
        payload = records_dict
        for x in payload['leads']:
            x['last_name'] = 'None'
        payload = json.dumps(payload).encode('utf-8')
        method = 'POST'
        api_call = '/api/leads/multiple'
        data = make_api_call(method, api_call, payload)

        leads_dict = json.loads(data)

        if 'errors' in leads_dict.keys(): #modify: figure out why it fails here?
            delete_index = []
            for x in leads_dict['errors'].keys():
                delete_index.append(int(x.split('.')[1]))

            delete_index.reverse()
            for x in delete_index:
                del records_dict['leads'][x]

            payload = records_dict
            payload = json.dumps(payload).encode('utf-8')
            data = make_api_call(method, api_call, payload)

        append_new_leads()

    # out of loop
    ids_list = search_leads_ids(filename)

    return ids_list
        
def get_all_leads():
    count = 0
    payload = ''
    method = 'GET'
    api_call = '/api/leads'
  
    leads_list = make_api_call(method, api_call, payload)
    leads_dict = json.loads(leads_list)
    print(leads_dict)
    
    while leads_dict['links']['next']:
        api_call = leads_dict['links']['next'].split('https://mail.sisconsult.co')[1]
        leads_list = make_api_call(method, api_call, payload)
        leads_dict_1 = json.loads(leads_list)

        # Correctly merge new data
        leads_dict['data'].extend(leads_dict_1['data'])

        # Update the 'links' dict so we follow the correct next page
        leads_dict['links'] = leads_dict_1.get('links', {})

        count += 1

        print(count)

    with open('test.csv', 'w') as file:
        fieldnames = leads_dict['data'][0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(leads_dict['data'])
        
    return leads_list
  
def append_new_leads():

    # read existing
    existing_emails = []
    records = []
    with open('test.csv', 'r') as file:
        reader = csv.DictReader(file)
        for x in reader:
            # get mails
            existing_emails.append(x['email'])
            # get records
            records.append(x)

    reached_existing_emails = False
    records_to_append = []
    count = 0
    page_number = 1
    while not reached_existing_emails:
        # get 15 new records
        
        payload = ''
        method = 'GET'
        api_call = '/api/leads?page={}'.format(page_number)
        print(api_call)
        leads_list = make_api_call(method, api_call, payload)
        leads_dict = json.loads(leads_list)

        # records in mails?
        
        for x in leads_dict['data']:
            if x['email'] in existing_emails: #this wont work
                reached_existing_emails = True
            else:
                # add to records
                records_to_append.append(x)
        count += 1
        page_number += 1
        print(count)

    records_to_append.extend(records)

    with open('test.csv', 'w') as file:
        fieldnames = records_to_append[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records_to_append)

def create_leads_list_from_csv(): # NOT WORKING
    import requests

    # --- Config ---
    url = "https://mail.sisconsult.co/api/leads/bulk/csv"
    token = cred.api_token
    csv_path = '/Users/albertoruizcajiga/Documents/Documents - Alberto’s MacBook Air/final_final/to_process/3_sartorius_alex_20250624.csv'

    # --- CSV field mapping (from your CSV column headers to expected server fields) ---
    # This maps your CSV columns to server-side expected fields
    columns_to_map_indexed = {
        "columnsToMap[0][first_name]": "first_name",
        "columnsToMap[0][last_name]": "",
        "columnsToMap[0][email]": "email",
        "columnsToMap[0][title]": "",
        "columnsToMap[0][company]": "",
        "columnsToMap[0][custom_variable]": ""
    }

    # Optional default values (if column is missing in CSV)
    columns_to_map_defaults = {
        "columnsToMap[first_name]": "et",
        "columnsToMap[last_name]": "aperiam",
        "columnsToMap[email]": "halle.west@example.org",
        "columnsToMap[title]": "qui",
        "columnsToMap[company]": "ullam"
    }

    # Name of the contact list
    form_data = {
        "name": "3_sartorius_alex_20250624"
    }

    # Merge all parts of the form data
    form_data.update(columns_to_map_indexed)
    form_data.update(columns_to_map_defaults)

    # File upload
    # files = {
    #     "csv": (csv_path, open(csv_path, "rb"), "text/csv")
    # }

    # Headers (Note: requests will set multipart content-type automatically)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    # --- Send POST request ---
    with open(csv_path, "rb") as f:
        files = {
            "csv": (csv_path, f, "text/csv")
        }
        response = requests.post(url, headers=headers, data=form_data, files=files)


    # --- Output ---
    print("Status:", response.status_code)
    print(response.text)

def import_leads_list_to_campaign():

    payload = "{\"lead_list_id\": 2}"

    method = 'POST'
    api_call = '/api/campaigns/5/leads/attach-lead-list'
    make_api_call(method, api_call, payload)

def import_leads_by_id_to_campaign(campaign_id, ids_list):

    payload = {
        'lead_ids':ids_list
    }
    payload = json.dumps(payload).encode('utf-8')
    method = 'POST'
    api_call = '/api/campaigns/{}/leads/attach-leads'.format(campaign_id)
    make_api_call(method, api_call, payload)

def view_available_timezones():

    payload = ''
    method = 'GET'
    api_call = '/api/campaigns/schedule/available-timezones'
    make_api_call(method, api_call, payload)

def get_list_of_sender_emails():
    method='GET'
    api_call = '/api/sender-emails'
    payload=''
    make_api_call(method,api_call,payload)

def import_sender_emails_by_id(campaign_id:int):
    ids_list = [x for x in range(273)]
    payload = {
        'sender_email_ids':ids_list[1:]
    }
    payload = json.dumps(payload).encode('utf-8')
    method = 'POST'
    api_call = '/api/campaigns/{}/attach-sender-emails'.format(campaign_id)
    make_api_call(method,api_call,payload)

def resume_campaign(campaign_id):
    method='PATCH'
    api_call = '/api/campaigns/{}/resume'.format(campaign_id)
    payload=''
    make_api_call(method,api_call,payload)

def create_new_project_in_email_bison():
    campaign_name = '143386_sedivention_germany_20250703'
    timezone = 'America/New_York'
    mail_message_filename = '/Users/albertoruizcajiga/python/sis_international/files/projects/143386_sedivention/' \
    '143386_sedivention.txt'
    #list_file_name = 'Cayman_List_1_2_Filtered.csv'

    max_emails_per_day = 1000
    campaign_id = create_a_campaign(campaign_name)
    list_campaigns() # modify: check if this has worked
    update_campaign_settings(max_emails_per_day, campaign_id)
    create_campaign_schedule(campaign_id,timezone)
    create_sequence_steps(campaign_id, mail_message_filename)
    import_sender_emails_by_id(campaign_id)
    # ids_list = bulk_create_leads(list_file_name)
    # import_leads_by_id_to_campaign(campaign_id, ids_list)
    # resume_campaign(campaign_id)

def add_list_and_start_campaign():
    campaign_id = int(input('Campaing id: '))
    list_file_name = input('List name: ')
    list_file_name = '{}.csv'.format(list_file_name)
    ids_list = bulk_create_leads(list_file_name)
    import_leads_by_id_to_campaign(campaign_id, ids_list)
    resume_campaign(campaign_id)

def search_leads_ids(filename):
    file_path = '/Users/albertoruizcajiga/Documents/Documents - Alberto’s MacBook Air/final_final/to_process/'
    file_name = file_path + filename
    a = []
    with open(file_name, 'r') as file:
        records = csv.DictReader(file)
        for record in records:
            a.append(record['email'])

    ids_list = []
    with open('test.csv', 'r') as file:
        reader = csv.DictReader(file)
        for x in reader:
            if x['email'] in a:
                ids_list.append(x['id'])

    return ids_list

def create_blacklisted_email():
    filename = const.BLACKLIST_PATH
    with open(filename, 'r') as file:
        contents = file.read()
        print(contents)

    # payload = "{\"email\": \"john@doe.com\"}"

    # method='POST'
    # api_call = '/api/blacklisted-emails'
    # payload=''
    # make_api_call(method,api_call,payload)

    # result = re.match(r'^([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+)\.([a-zA-Z]{2,})$','christine.saenger@web.de')

    # print(result.string)

# TO-DO

# bulk update email signature

# add to block list - email addresses
# add to block list - domains



add_list_and_start_campaign()

