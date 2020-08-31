from flask import Flask
from flask import request, render_template

from tinydb import TinyDB
from lib.db import PickleDatabase

from lib.vault import VaultClient
from audit.server import AuditServer
from lib.suggestions import Suggestions
from lib.ssl import update_ssl

from multiprocessing import Process
from apscheduler.schedulers.background import BackgroundScheduler

import logging

app = Flask(__name__)

# Log
handlers=[logging.StreamHandler()]
logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s', handlers=handlers)
logging.info("Starting VaultAIDE ...")

# Database access
pickle_db = PickleDatabase('../db/settings/config.db')
db_week = TinyDB('../db/audit/operations.db', default_table='week_operations')
db_month = TinyDB('../db/audit/operations.db', default_table='month_operations')

# Setting configuration
'''
    All the config variables are in db/configuration/config.db
'''
vault_addr = pickle_db.get_data('vault_host')
vault_token = pickle_db.get_data('vault_token')
audit_host = pickle_db.get_data('audit_host')
audit_port = pickle_db.get_data('audit_port')

# Initializing lib objects
vault_client = VaultClient(vault_addr, vault_token, pickle_db, db_week, db_month)
suggestions = Suggestions(vault_client, pickle_db)
audit_server = AuditServer(audit_host, audit_port, suggestions, vault_client, db_week, db_month)

# Starting the socket too query audit logs
audit_process = Process(target=audit_server.serve)
audit_process.start()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/config')
def config_page():
    '''
        Configuration page for VaultAIDE
    '''
    return render_template('bot_config.html')

@app.route('/save-config', methods=['POST'])
def save_config():
    '''
        Function to update the configuration in db/configuration/config.db
    '''
    config_info = request.form

    pickle_db.set_data('vault_host', config_info.get("vault_host", ""))
    pickle_db.set_data('vault_port', config_info.get("vault_port", ""))
    pickle_db.set_data('vault_tls', config_info.get("vault_tls", ""))
    pickle_db.set_data('vault_token', config_info.get("vault_token", ""))
    
    pickle_db.set_data('ad_host', config_info.get("ad_host", ""))
    pickle_db.set_data('ad_port', config_info.get("ad_port", ""))
    
    pickle_db.set_data('slack_host', config_info.get("slack_host", ""))
    pickle_db.set_data('slack_port', config_info.get("slack_port", ""))
    pickle_db.set_data('slack_token', config_info.get("slack_token", ""))
    pickle_db.set_data('slack_channel', config_info.get("slack_channel", ""))

    pickle_db.set_data('http_host', config_info.get("http_host", ""))
    pickle_db.set_data('http_tls', config_info.get("http_tls", ""))
    pickle_db.set_data('http_port', config_info.get("http_port", ""))

    if config_info.get("http_tls", False):
        update_ssl()

    task_arr = config_info.get("task_array", {})

    pickle_db.set_data('all_tasks', config_info.get("all_tasks", False))
    pickle_db.set_data('task_array', task_arr)

    schedule_suggestions()

    return {'success': True}

def schedule_suggestions():
    '''
        This function creates the scheduled tasks for slack
    '''

    scheduler = BackgroundScheduler()

    all_suggestions = pickle_db.get_data("all_tasks")

    if all_suggestions:
        scheduler.add_job(func=suggestions.suggest_version, trigger="interval", days=30)
        scheduler.add_job(func=suggestions.adoption_stats, trigger="interval", days=30)
        scheduler.add_job(func=suggestions.extant_leases, trigger="interval", days=30)
        scheduler.add_job(func=suggestions.leases_ttl, trigger="interval", days=30)
        scheduler.add_job(func=suggestions.unused_leases, trigger="interval", days=30)
    else:
        sugg_array = pickle_db.get_data("task_array")
        
        for suggestion in sugg_array:
            if suggestion == 1:
                scheduler.add_job(func=suggestions.suggest_version, trigger="interval", days=30)
            elif suggestion == 2:
                scheduler.add_job(func=suggestions.adoption_stats, trigger="interval", days=30)
            elif suggestion == 3:
                scheduler.add_job(func=suggestions.extant_leases, trigger="interval", days=30)
            elif suggestion == 4:
                scheduler.add_job(func=suggestions.leases_ttl, trigger="interval", days=30)
            elif suggestion == 5:
                scheduler.add_job(func=suggestions.unused_leases, trigger="interval", days=time)
            elif suggestion == 6:
                scheduler.add_job(func=suggestions.high_privilege_login, trigger="interval", days=time)


    return True

# Slack Implementation
@app.route('/slack/get-answer', methods=['POST', 'GET'])
def slack_get_answer():
    # Slack bot token
    sl_token = db.get('slack_token')
    slack_client = SlackClient(sl_token)

    # Check if this request is a command
    if request.json == None:
        slack_form = { "event": { "text": "command"}}
    else:
        slack_form = request.json

    # Check if this request is a handshake
    if slack_form.get('challenge', False):
        return {'challenge': slack_form.get('challenge')}

    else:
        # Check if the last event was a bot response and it's from the right channel
        if not slack_form['event'].get('bot_id', False):

            # Check if the message it's a channel join
            if slack_form['event'].get('subtype', "") == "channel_join":
                slack_client.api_call("chat.postMessage",
                                           channel="#vault_aide",
                                           text="Welcome <@" + slack_form['event'].get('user', "") + ">"
                                          )

            # Get message
            elif slack_form['event'].get('text', False):

                res = False

                command = request.args.get("command", "")
                msg = slack_form['event']['text']

                '''
                    Available tasks
                    Version Updates, Adoption Stats, Extant Leases, Admin Creation Alert, 
                    High privilege action, Vault Posture Score, Auth Method Suggestions, Statusserer
                '''

                if command == "version" or msg.lower() == "version":
                    suggestions.suggest_version()
                elif  command == "adoption_stats" or msg.lower() == "adoption stats":
                    suggestions.adoption_stats()
                elif  command == "extant_leases" or msg.lower() == "extant leases":
                    suggestions.extant_leases()
                elif  command == "leases_ttl" or msg.lower() == "leases":
                    suggestions.leases_ttl()
                elif  command == "high_privilege_login":
                    suggestions.high_privilege_login()
                elif  command == "posture_score" or msg.lower() == "score":
                    suggestions.vault_posture_score()
                elif  command == "auth_method" or msg.lower() == "auth method":
                    suggestions.auth_method_suggestion()
                elif  command == "statusserer" or msg.lower() == "statusserer":
                    suggestions.auth_method_suggestion()
                elif msg == "Adoption Details 2":
                    suggestions.adoption_stats_detailed()
                else:
                    res = False

            else:
                # Unknown event
                res = False

        return {"success": True}           

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, use_reloader=False)
