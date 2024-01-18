import rt.rest1
import json
import logging
from datetime import datetime

# Initialize a logger for process_incident_reports
process_logger = logging.getLogger('process_incident_reports')
process_logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
process_logger.addHandler(console_handler)

def generate_process_id():
    # Generates a unique ID for each process
    try:
        with open('action_log.json', 'r') as file:
            data = json.load(file)
            last_id = max(map(int, data.keys()))
            return str(last_id + 1)
    except (FileNotFoundError, ValueError, KeyError):
        return '1'

def log_action(process_id, action_details):
    # Logs action details for a given process
    try:
        with open('action_log.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}

    if process_id not in data:
        data[process_id] = []
    data[process_id].append(action_details)

    with open('action_log.json', 'w') as file:
        json.dump(data, file, indent=4)

def read_answer_from_file(file_path, keyword):
    # Reads an answer from a file based on a keyword
    try:
        with open(file_path, 'r') as file:
            answers = json.load(file)
            return answers.get(keyword)
    except Exception as e:
        process_logger.error(f"Error reading answer from file: {e}")
        return None

def load_keywords_from_json(file_path):
    # Loads keywords from a JSON file
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return list(data.keys())
    except Exception as e:
        process_logger.error(f"Error loading keywords: {e}")
        return []

def process_incident_reports(rt_url, username, password, answer_keyword, link_to_id, incident_ids, selected_status):
    # Main function to process incident reports
    process_id = generate_process_id()

    try:
        tracker = rt.rest1.Rt(rt_url, username, password)
        if not tracker.login():
            process_logger.error('Login failed, please check credentials')
            return

        for incident_id in incident_ids:
            try:
                incident_details = tracker.get_ticket(incident_id)
                if incident_details.get('Status') in ['resolved', 'rejected']:
                    process_logger.info(f"Incident ID: {incident_id} is already {incident_details.get('Status')}. Skipping.")
                    continue

                tracker.edit_ticket(incident_id, Owner=username)
                process_logger.info(f'User changed to {username}...')

                answer_text = read_answer_from_file('answer.json', answer_keyword)
                if answer_text and answer_text != 'none':
                    tracker.reply(incident_id, text=answer_text)
                    process_logger.info("Response sent.")

                if link_to_id != 0:
                    tracker.edit_link(incident_id, 'MemberOf', link_to_id)
                    process_logger.info("Incident linked.")

                if selected_status in ["Close", "Reject"]:
                    new_status = 'resolved' if selected_status == "Close" else 'rejected'
                    tracker.edit_ticket(incident_id, Status=new_status)
                    process_logger.info(f"Incident report {selected_status.lower()}ed.")
                
                log_action(process_id, {
                    "incident_id": incident_id,
                    "answer_type": answer_keyword,
                    "status": selected_status,
                    "date_and_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

            except Exception as e:
                process_logger.error(f"Error processing Incident ID {incident_id}: {e}")

        tracker.logout()
        process_logger.info("All incidents processed.")
    except Exception as e:
        process_logger.error(f"Error processing incidents: {e}")

# Removed unused logger configurations and unnecessary commented code.

