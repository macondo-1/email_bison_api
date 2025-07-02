import credentials as cred
import http.client
import json
import csv

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
    #payload = "{\"search\": null,\n  \"status\": \"active\"}"

    #MODIFY: THIS IS NOT WORKING
    payload = {
        'status':'{}'.format(status)
    }
    payload = json.dumps(payload).encode('utf-8')
    api_call = '/api/campaigns'
    method = 'GET'
    make_api_call(method, api_call, payload)

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

    payload = records_dict
    for x in payload['leads']:
        x['last_name'] = 'None'
    payload = json.dumps(payload).encode('utf-8')
    method = 'POST'
    api_call = '/api/leads/multiple'
    data = make_api_call(method, api_call, payload)

    leads_dict = json.loads(data)

    if leads_dict['errors']:
        delete_index = []
        for x in leads_dict['errors'].keys():
            delete_index.append(int(x.split('.')[1]))

        for x in delete_index:
            del records_dict['leads'][x]

        payload = records_dict
        payload = json.dumps(payload).encode('utf-8')
        data = make_api_call(method, api_call, payload)

    return data
        
def get_all_leads():
    payload = ''
    method = 'GET'
    api_call = '/api/leads'
    leads_list = make_api_call(method, api_call, payload)

    return leads_list
  
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


#  COMPLETE WORKFLOW
# campaign_name = '124015_glassview_hearing_study_20250701'
# max_emails_per_day = 1000
# campaign_id = create_a_campaign(campaign_name)
# update_campaign_settings(max_emails_per_day, campaign_id)
# timezone = 'America/New_York'
# create_campaign_schedule(campaign_id,timezone)
# mail_message_filename = '/Users/albertoruizcajiga/python/sis_international/files/projects/124015_glassview_hearing_study/' \
# '124015_glassview_hearing_study.txt'
# create_sequence_steps(campaign_id, mail_message_filename)
# import_sender_emails_by_id(campaign_id)

campaign_id = 10
# ids_list = []
# with open('test.csv','r') as file:
#     content = file.readlines()
#     for x in content[1:]:
#         ids_list.append(x.split(',')[0])

#working
# leads_list = bulk_create_leads('usa_nyc_intern_entry_4.csv')
# leads_dict = json.loads(leads_list)
# ids_list = []
# for x in leads_dict['data']:
#     ids_list.append(x['id'])
# import_leads_by_id_to_campaign(campaign_id, ids_list)
#resume_campaign(campaign_id)



# checar
# leads_list = bulk_create_leads('usa_nyc_intern_entry_2.csv')
# leads_dict = json.loads(leads_list)
# ids_list = []
# for x in leads_dict['data']:
#     ids_list.append(x['id'])

# with open('test.csv', 'w') as file:
#     fieldnames = leads_dict['data'][0].keys()
#     writer = csv.DictWriter(file,fieldnames=fieldnames)
#     writer.writeheader()
#     writer.writerows(leads_dict['data'])

leads_list = bulk_create_leads('usa_nyc_intern_entry_5.csv')
leads_dict = json.loads(leads_list)

# for x in leads_dict['errors'].keys():
#     print(x.split('.')[1])

