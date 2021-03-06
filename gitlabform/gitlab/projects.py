import json

from gitlabform.gitlab.core import GitLabCore


class GitLabProjects(GitLabCore):

    def get_all_projects(self):
        """
        :param group: group name
        :return: sorted list of ALL projects you have access to, strings "group/project_name"
        """
        result = self._make_requests_to_api("projects?order_by=name&sort=asc", paginated=True)
        return sorted(map(lambda x: x['path_with_namespace'], result))

    def post_deploy_key(self, project_and_group_name, deploy_key):
        # deploy_key has to be like this:
        # {
        #     'title': title,
        #     'key': key,
        #     'can_push': can_push,
        # }
        # ..as documented at: https://docs.gitlab.com/ce/api/deploy_keys.html#add-deploy-key
        self._make_requests_to_api("projects/%s/deploy_keys", project_and_group_name, 'POST', deploy_key,
                                   expected_codes=201)

    def get_deploy_keys(self, project_and_group_name):
        return self._make_requests_to_api("projects/%s/deploy_keys", project_and_group_name)

    def get_deploy_key(self, project_and_group_name, id):
        return self._make_requests_to_api("projects/%s/deploy_keys/%s", (project_and_group_name, id), 'GET')

    def post_secret_variable(self, project_and_group_name, secret_variable):
        # secret_variable has to be like this:
        # {
        #     'key': key,
        #     'value': value,
        # }
        # ..as documented at: https://docs.gitlab.com/ce/api/build_variables.html#create-variable
        self._make_requests_to_api("projects/%s/variables", project_and_group_name, 'POST', secret_variable,
                                   expected_codes=201)

    def put_secret_variable(self, project_and_group_name, secret_variable):
        # secret_variable has to be like this:
        # {
        #     'key': key,
        #     'value': value,
        # }
        # ..as documented at: https://docs.gitlab.com/ce/api/build_variables.html#update-variable
        self._make_requests_to_api("projects/%s/variables/%s", (project_and_group_name, secret_variable['key']),
                                   'PUT', secret_variable)

    def get_secret_variable(self, project_and_group_name, secret_variable_key):
        return self._make_requests_to_api("projects/%s/variables/%s", (project_and_group_name, secret_variable_key))['value']

    def get_secret_variables(self, project_and_group_name):
        return self._make_requests_to_api("projects/%s/variables", project_and_group_name)

    def get_project_settings(self, project_and_group_name):
        return self._make_requests_to_api("projects/%s", project_and_group_name)

    def put_project_settings(self, project_and_group_name, project_settings):
        # project_settings has to be like this:
        # {
        #     'setting1': value1,
        #     'setting2': value2,
        # }
        # ..as documented at: https://docs.gitlab.com/ce/api/projects.html#edit-project
        self._make_requests_to_api("projects/%s", project_and_group_name, 'PUT', project_settings)

    def get_hook_id(self, project_and_group_name, url):
        hooks = self._make_requests_to_api("projects/%s/hooks", project_and_group_name, 'GET')
        for hook in hooks:
            if hook['url'] == url:
                return hook['id']
        return None

    def delete_hook(self, project_and_group_name, hook_id):
        self._make_requests_to_api("projects/%s/hooks/%s", (project_and_group_name, hook_id), 'DELETE')

    def put_hook(self, project_and_group_name, hook_id, url, data):
        data_required = {'url': url}
        data = {**data, **data_required}
        self._make_requests_to_api("projects/%s/hooks/%s", (project_and_group_name, hook_id), 'PUT', data)

    def post_hook(self, project_and_group_name, url, data):
        data_required = {'url': url}
        data = {**data, **data_required}
        self._make_requests_to_api("projects/%s/hooks", project_and_group_name, 'POST', data, expected_codes=201)

    def post_approvals(self, project_and_group_name, data):
        # for this endpoint GitLab still actually wants pid, not "group/project"...
        pid = self._get_project_id(project_and_group_name)
        data_required = {'id': pid}
        data = {**data, **data_required}
        self._make_requests_to_api("projects/%s/approvals", pid, 'POST', data, expected_codes=201)

    def put_approvers(self, project_and_group_name, approvers, approver_groups):
        """
        :param project_and_group_name: "group/project" string
        :param approvers: list of approver user names
        :param approver_groups: list of approver group paths
        """

        # gitlab API expects ids, not names of users and groups, so we need to convert first
        approver_ids = []
        for approver_name in approvers:
            approver_ids.append(self._get_user_id(approver_name))
        approver_group_ids = []
        for group_path in approver_groups:
            approver_group_ids.append(self._get_group_id(group_path))

        # we need to pass data to this gitlab API endpoint as JSON, because when passing as data the JSON converter
        # used by requests lib changes empty arrays into nulls and omits it, which results in
        # {"error":"approver_group_ids is missing"} error from gitlab...
        # TODO: create JSON object directly, omit converting string to JSON
        # for this endpoint GitLab still actually wants pid, not "group/project"...
        pid = self._get_project_id(project_and_group_name)
        data = "{"\
               + '"id":' + str(pid) + ','\
               + '"approver_ids": [' + ','.join(str(x) for x in approver_ids) + '],'\
               + '"approver_group_ids": [' + ','.join(str(x) for x in approver_group_ids) + ']'\
               + "}"
        json_data = json.loads(data)
        self._make_requests_to_api("projects/%s/approvers", pid, 'PUT', data=None, json=json_data)
