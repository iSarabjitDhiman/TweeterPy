import random
from tweeterpy.constants import Path
from tweeterpy.util import find_nested_key
from tweeterpy.utils.request import RequestClient
from tweeterpy.utils.logging import disable_logger


class TaskHandler:
    def __init__(self, request_client: RequestClient = None):
        self.request_client = request_client

    def _create_task_mapper(self, username, password, verification_input_data):
        # fmt: off  - Turns off formatting for this block of code. Just for the readability purpose.
        task_flow_mapper = {"LoginJsInstrumentationSubtask":{"task_executor": self._get_user_flow_token,"task_parameter":None},
                            "LoginEnterUserIdentifierSSO":{"task_executor": self._get_password_flow_token,"task_parameter":username},
                            "LoginEnterAlternateIdentifierSubtask":{"task_executor": self._handle_suspicious_login,"task_parameter":verification_input_data},
                            "LoginEnterPassword":{"task_executor": self._get_account_duplication_flow_token,"task_parameter":password},
                            "DenyLoginSubtask":{"task_executor": self._check_suspicious_login,"task_parameter":None},
                            "AccountDuplicationCheck":{"task_executor": self._check_account_duplication,"task_parameter":None},
                            "LoginAcid":{"task_executor":self._handle_suspicious_login,"task_parameter":verification_input_data},
                            "LoginTwoFactorAuthChallenge":{"task_executor":self._handle_suspicious_login,"task_parameter":verification_input_data},
                            "LoginSuccessSubtask":{"task_output": "\nPlease Wait... Logging In...\n"}}
        return task_flow_mapper

    def _get_flow_token(self):
        params = {'flow_name': 'login'}
        login_location = random.choice(['splash_screen', 'manual_link'])
        payload = {'input_flow_data': {
            'flow_context': {'debug_overrides': {}, 'start_location': {'location': login_location}, }, },
            'subtask_versions': {'action_list': 2, 'alert_dialog': 1, 'app_download_cta': 1, 'check_logged_in_account': 1,
                                 'choice_selection': 3, 'contacts_live_sync_permission_prompt': 0, 'cta': 7, 'email_verification': 2, 'end_flow': 1,
                                 'enter_date': 1, 'enter_email': 2, 'enter_password': 5, 'enter_phone': 2, 'enter_recaptcha': 1, 'enter_text': 5,
                                 'enter_username': 2, 'generic_urt': 3, 'in_app_notification': 1, 'interest_picker': 3, 'js_instrumentation': 1,
                                 'menu_dialog': 1, 'notifications_permission_prompt': 2, 'open_account': 2, 'open_home_timeline': 1, 'open_link': 1,
                                 'phone_verification': 4, 'privacy_options': 1, 'security_key': 3, 'select_avatar': 4, 'select_banner': 2,
                                 'settings_list': 7, 'show_code': 1, 'sign_up': 2, 'sign_up_review': 4, 'tweet_selection_urt': 1, 'update_users': 1,
                                 'upload_media': 1, 'user_recommendations_list': 4, 'user_recommendations_urt': 1, 'wait_spinner': 3, 'web_modal': 1}}
        return self.request_client.request(Path.TASK_URL, method="POST", params=params, json=payload)

    def _get_javscript_instrumentation_subtask(self):
        params = {'c_name': 'ui_metrics'}
        return self.request_client.request(Path.JAVSCRIPT_INSTRUMENTATION_URL, params=params)

    def _get_user_flow_token(self, flow_token, subtask_id="LoginJsInstrumentationSubtask"):
        payload = {'flow_token': flow_token,
                   'subtask_inputs': [{'subtask_id': subtask_id,
                                      'js_instrumentation': {
                                          'response': '',
                                          'link': 'next_link'}}]}
        return self.request_client.request(Path.TASK_URL, method="POST", json=payload)

    @disable_logger
    def _get_password_flow_token(self, flow_token, subtask_id="LoginEnterUserIdentifierSSO", username=None):
        payload = {'flow_token': flow_token,
                   'subtask_inputs': [{'subtask_id': subtask_id,
                                      'settings_list': {
                                          'setting_responses': [{'key': 'user_identifier', 'response_data': {'text_data': {'result': username}}}],
                                          'link': 'next_link'}}]}
        return self.request_client.request(Path.TASK_URL, method="POST", json=payload)

    @disable_logger
    def _get_account_duplication_flow_token(self, flow_token, subtask_id="LoginEnterPassword", password=None):
        payload = {'flow_token': flow_token,
                   'subtask_inputs': [{'subtask_id': subtask_id,
                                      'enter_password': {'password': password, 'link': 'next_link'}}]}
        return self.request_client.request(Path.TASK_URL, method="POST", json=payload)

    def _check_suspicious_login(self, flow_token, subtask_id="DenyLoginSubtask"):
        payload = {"flow_token": flow_token,
                   "subtask_inputs": [{"subtask_id": subtask_id, "cta": {"link": "next_link"}}]}
        return self.request_client.request(Path.TASK_URL, method="POST", json=payload)

    def _check_account_duplication(self, flow_token, subtask_id="AccountDuplicationCheck"):
        payload = {'flow_token': flow_token,
                   'subtask_inputs': [{'subtask_id': subtask_id, 'check_logged_in_account': {'link': 'AccountDuplicationCheck_false'}}]}
        return self.request_client.request(Path.TASK_URL, method="POST", json=payload)

    def _handle_suspicious_login(self, flow_token, subtask_id="LoginAcid",verification_input_data=None):
        payload = {"flow_token": flow_token,
                   "subtask_inputs": [{"subtask_id": subtask_id, "enter_text": {"text": verification_input_data,"link":"next_link"}}]}
        handle_incorrect_input = True
        while handle_incorrect_input:
            response = self.request_client.request(Path.TASK_URL, method="POST", json=payload, skip_error_checking=True)
            if isinstance(response, dict) and "errors" in response.keys():
                error_message = "\n".join([error['message'] for error in response['errors']])
                payload['subtask_inputs'][0]['enter_text']['text'] = str(input(f"{error_message} - Type again ==> "))
            else:
                handle_incorrect_input = False
        return response

    @disable_logger
    def login(self, username, password, email=None, phone=None, **kwargs):
        response = None
        error_message = None
        tasks_pending = True
        verification_input_data = None
        try:
            task_flow_mapper = self._create_task_mapper(username or email, password, verification_input_data)
            response = self._get_flow_token()
            self._get_javscript_instrumentation_subtask()
            while tasks_pending:
                response_tasks = [task['subtask_id'] for task in response['subtasks']]
                flow_token = response['flow_token']
                tasks = [task_id for task_id in task_flow_mapper.keys() if task_id in response_tasks]
                if tasks:
                    task_id = tasks[0]
                else:
                    missing_task_ids_error = f"\nCouldn't find the following Task Ids:\n{response_tasks}" if response_tasks else ""
                    login_error =  f"{(error_message or '')}{missing_task_ids_error}".strip()
                    raise Exception(login_error)
                task = task_flow_mapper.get(task_id)
                if task:
                    error_message = ("\n".join([ x for x in find_nested_key(response,"text") if x and isinstance(x, str)]) or "").strip()
                    if task_id in ['LoginAcid', 'LoginEnterAlternateIdentifierSubtask', 'LoginTwoFactorAuthChallenge']:
                        input_type = (find_nested_key(response,"keyboard_type") or "").strip().lower()
                        hint_message = (find_nested_key(response,"hint_text") or "").strip().lower()
                        input_message = f"{hint_message} (Input Type - {input_type}) ==> "
                        otp_required = True if hint_message == "confirmation code" and input_type == "text" else False
                        email_verification = True if input_type == "email" or (hint_message == "phone or email" and input_type == "text") else False
                        phone_verification = True if hint_message == "phone number" and input_type == "telephone" else False
                        identity_verification = True if hint_message == "phone or username" and input_type == "text" else False
                        two_fac_auth = True if task_id == "LoginTwoFactorAuthChallenge" else False
                        if input_type and hint_message and error_message:
                            print(f"\n{error_message}\n")
                            verification_input_data = phone if (phone_verification or identity_verification) and phone else email if email_verification and email else str(input(input_message)) if two_fac_auth or otp_required else None
                            if not verification_input_data:
                                raise Exception(error_message)
                            task_flow_mapper[task_id].update({"task_parameter":verification_input_data}) 
                    if task_id == 'LoginSuccessSubtask':
                        tasks_pending = False
                        print(task['task_output'])
                        continue
                    if task['task_parameter'] is None:
                        response = task.get('task_executor')(flow_token,task_id)
                    else:
                        parameter = task.get('task_parameter')
                        response =  task.get('task_executor')(flow_token,task_id,parameter)
                else:
                    print(f"\n{response}")
                    tasks_pending = False
        except Exception as error:
            raise error