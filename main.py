import credentials as cred
import constants as const
import http.client
import json
import csv
import re
import pandas as pd
from pathlib import Path
import datetime

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
    #print(data.decode("utf-8"))

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
    leads_dict = json.loads(records)

    count = 0
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

    with open('campaigns_info.csv', 'w') as file:
        fieldnames = leads_dict['data'][0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(leads_dict['data'])
        

    # with open('campaigns_info.csv', 'w') as file:
    #     fieldnames = records['data'][0].keys()
    #     writer = csv.DictWriter(file, fieldnames=fieldnames)
    #     writer.writeheader()
    #     writer.writerows(records['data'])

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
        'plain_text':False,
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
    file_path = const.TO_PROCESS_PATH
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
        print('list is larger than 500 records')
        while len(records_dict['leads']) > 500:
            print('uploading the {}th 500 records'.format(count))
            count += 1
            remaining_dict['leads'] = records_dict['leads'][500:]
            records_dict['leads'] = records_dict['leads'][:500]
            payload = records_dict
            for x in payload['leads']:
                x['last_name'] = 'None'
            payload = json.dumps(payload).encode('utf-8')
            method = 'POST'
            api_call = '/api/leads/multiple'
            data = make_api_call(method, api_call, payload)

            leads_dict = json.loads(data)

            if 'errors' in leads_dict.keys():
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

        if 'errors' in leads_dict.keys():
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


    records_to_append.extend(records)

    with open('test.csv', 'w') as file:
        fieldnames = records_to_append[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records_to_append)

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
    leads_list = make_api_call(method,api_call,payload)
    leads_dict = json.loads(leads_list)
    count = 0
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

    with open('sender_emails.csv', 'w') as file:
        fieldnames = leads_dict['data'][0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(leads_dict['data'])
        
    return leads_list

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
    campaign_name = input('Project name: ')
    date = datetime.datetime.now()
    date = date.strftime('%Y%m%d')
    campaign_name = '{0}_{1}'.format(campaign_name, date)
    timezone = input('time zone: ')
    mail_message_filename = '{0}/{1}/{1}.txt'.format(const.PROJECTS_DIR, campaign_name)

    max_emails_per_day = 500
    campaign_id = create_a_campaign(campaign_name)
    list_campaigns()
    update_campaign_settings(max_emails_per_day, campaign_id)
    create_campaign_schedule(campaign_id,timezone)
    create_sequence_steps(campaign_id, mail_message_filename)
    import_sender_emails_by_id(campaign_id)

def add_list_and_start_campaign():
    campaign_id = int(input('Campaing id: '))
    list_file_name = input('List name: ')
    list_file_name = '{}.csv'.format(list_file_name)
    ids_list = bulk_create_leads(list_file_name)
    import_leads_by_id_to_campaign(campaign_id, ids_list)
    resume_campaign(campaign_id)

def search_leads_ids(filename):
    file_path = const.TO_PROCESS_PATH
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

def get_all_blacklisted_emails():
    method = 'GET'
    api_call = '/api/blacklisted-emails'
    payload = ''
    blacklisted_emails = make_api_call(method,api_call,payload)
    blacklisted_emails = json.loads(blacklisted_emails)
    blacklisted_emails = [x['email'] for x in blacklisted_emails['data']]

    return blacklisted_emails

def create_blacklisted_email():
    blacklisted_emails = get_all_blacklisted_emails()
    pattern = r'^([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+)\.([a-zA-Z]{2,})$'
    filename = const.BLACKLIST_PATH

    with open(filename, 'r') as file:
        contents = file.readlines()

    pending_emails = [x.strip() for x in contents if x.strip() in blacklisted_emails]
    print(len(pending_emails))


    # count = 0
    # for x in contents:
    #     x = x.strip()
    #     result = re.match(pattern,x)
    #     if result:
    #         print('correo en loop: ', result.string)
    #         #if result.string not in blacklisted_emails:
    #         payload = {'email':result.string}
    #         payload = json.dumps(payload).encode('utf-8')
    #         method='POST'
    #         api_call = '/api/blacklisted-emails'
    #         count +=1
    #         make_api_call(method,api_call,payload)
    #         print(count)
                
def bulk_update_email_signatures():

    #ids_list = [x for x in range(273)]
    ids_list = [270]
    payload = {
        'sender_email_ids': ids_list[1:],
        #"email_signature": "<div style='font-style: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: 0px; orphans: auto; text-indent: 0px; text-transform: none; white-space: normal; widows: auto; word-spacing: 0px; -webkit-text-stroke-width: 0px; text-decoration: none; box-sizing: border-box; caret-color: rgb(0, 0, 0); color: rgb(0, 0, 0); text-align: left; direction: ltr; font-family: Arial, "Helvetica Neue", Helvetica, sans-serif; font-size: 14px; line-height: 16.799999px;' id="isPasted"><div style='box-sizing: border-box; color: rgb(0, 0, 0); direction: ltr; font-family: Arial, "Helvetica Neue", Helvetica, sans-serif; font-size: 14px; font-weight: 400; letter-spacing: 0px; line-height: 16.799999px; text-align: left;'><p style="box-sizing: border-box; line-height: inherit; margin: 0px 0px 16px;">Kind regards,<br>Senior Project Director<br>Maria Miller</p></div></div><div style='font-style: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: 0px; orphans: auto; text-indent: 0px; text-transform: none; white-space: normal; widows: auto; word-spacing: 0px; -webkit-text-stroke-width: 0px; text-decoration: none; box-sizing: border-box; caret-color: rgb(0, 0, 0); color: rgb(0, 0, 0); text-align: left; direction: ltr; font-family: Arial, "Helvetica Neue", Helvetica, sans-serif; font-size: 14px; line-height: 16.799999px;'><div style="box-sizing: border-box;"><p style="box-sizing: border-box; line-height: inherit;"><span lang="EN-US" style="box-sizing: border-box;">Feel free to visit our website: <a href="https://www.sisinternational.com/" target="_blank" rel="noopener" style="box-sizing: border-box;">www.sisinternational.com</a></span></p></div><div style="box-sizing: border-box;"><p style="box-sizing: border-box; line-height: inherit;"><span lang="EN-US" style="box-sizing: border-box;">We reserve the right to validate all information.&nbsp;</span></p></div><div style="box-sizing: border-box;"><p style="box-sizing: border-box; line-height: inherit;"><span lang="EN-US" style="box-sizing: border-box;">The incentive processing time is approximately 4 to 6 weeks</span></p><p style="box-sizing: border-box; line-height: inherit;"><br></p></div><p style="box-sizing: border-box; line-height: inherit; margin: 0px 0px 16px;">SIS International Research<br style="box-sizing: border-box;">11 E 22nd Street NY, NY 10010<br style="box-sizing: border-box;">(212) 505 6805</p><p style="box-sizing: border-box; line-height: inherit; margin: 0px 0px 16px;"><span style="box-sizing: border-box; color: rgb(11, 93, 149);"><strong style="box-sizing: border-box;"><span style="box-sizing: border-box; color: rgb(153, 102, 0);">New York</span> ‚ñ™ <span style="box-sizing: border-box; color: rgb(153, 102, 0);">London</span> ‚ñ™ <span style="box-sizing: border-box; color: rgb(153, 102, 0);">Los Angeles</span> ‚ñ™ <span style="box-sizing: border-box; color: rgb(153, 102, 0);">Hamburg</span> ‚ñ™ <span style="box-sizing: border-box; color: rgb(153, 102, 0);">Shanghai</span></strong></span></p><p style="box-sizing: border-box; line-height: inherit; margin: 0px 0px 16px;">Mentioned in <span style="box-sizing: border-box; color: rgb(11, 93, 149);"><strong style="box-sizing: border-box;">Forbes</strong></span>, <span style="box-sizing: border-box; color: rgb(11, 93, 149);"><strong style="box-sizing: border-box;">USA Today</strong></span> &amp; <span style="box-sizing: border-box; color: rgb(11, 93, 149);"><strong style="box-sizing: border-box;">Bloomberg</strong></span></p></div>"
        #'email_signature': '<p><strong>{SENDER_FIRST_NAME}</strong> | Consultant</p>'
    

    }
    
    payload = json.dumps(payload).encode('utf-8')
    payload = "{\n  \"sender_email_ids\": [\n    270,\n    2\n  ],\n  \"email_signature\": \"<p><strong>{SENDER_FIRST_NAME}</strong> | Consultant</p>\"\n}"
    method = 'PATCH'
    api_call = '/api/sender-emails/signatures/bulk'
    make_api_call(method, api_call, payload)

def show_sending_schedules():
    payload = "{\"day\": \"tomorrow\"}"
    method = 'GET'
    api_call = '/api/campaigns/sending-schedules'
    data = make_api_call(method, api_call ,payload)

    data = json.loads(data)
    with open('campaigns_schedule_tomorrow_2.csv', 'w') as file:
        fieldnames = data['data'][0].keys()
        writer = csv.DictWriter(file,fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(data['data'])

def get_ids_from_csv():
    """
    reads a csv, gets its emails and returns the ids of those already in bison
    """
    dir_path = Path(const.TO_PROCESS_PATH)
    campaign_id = input('campaign id: ')
    filename = input('file name: ')
    filename = '{}.csv'.format(filename)
    filename = dir_path / filename
    df = pd.read_csv(filename)
    emails = list(df.email)

    df_bison = pd.read_csv('test.csv', low_memory=False)
    df_ids = df_bison[df_bison.email.isin(emails)]
    ids_list = list(df_ids.id)

    import_leads_by_id_to_campaign(campaign_id, ids_list)

def restart_campaigns_schedule():
    df = pd.read_csv('campaigns_info.csv')
    ids_list = list(df.id)
    for id in ids_list:
        campaign_id = id
        resume_campaign(campaign_id)

add_list_and_start_campaign()