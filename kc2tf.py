import base64
import json
import time
import requests


def process_realm_roles():
    f = open('realm_dump.json')
    data = json.loads(f.read())
    with open('roles.tf', "w") as f_out:
        for role in data['roles']['realm']:
            if role['name'] not in default_roles:
                f_out.write('resource "keycloak_role" "' + role['name'] + '" {')
                f_out.write('\n\trealm_id = data.keycloak_realm.bcregistry_realm.id')
                f_out.write('\n\tname = "' + role['name'] + '"')
                if 'description' in role:
                    f_out.write('\n\tdescription = "' + repr(role['description']).strip("'").replace('$', '$$') + '"')
                f_out.write('\n}\n')


def process_client_mappers():
    f = open('realm_dump.json')
    data = json.loads(f.read())
    with open('client_mappers.tf', "w") as f_out:
        for client in data['clients']:
            if client['clientId'] not in default_accounts:
                if 'protocolMappers' in client and len(client['protocolMappers']) > 0:
                    for mapper in client['protocolMappers']:
                        if mapper['name'] not in default_mapper_names:
                            f_out.write('resource "keycloak_generic_protocol_mapper" "' + client['clientId'] + '-' + mapper['name'].replace(' ', '-') + '-scope-mapper" {')
                            f_out.write('\n\trealm_id = data.keycloak_realm.bcregistry_realm.id')
                            f_out.write('\n\tclient_id = keycloak_openid_client.' + client['clientId'].lower().replace(' ', '_') + '.id')
                            f_out.write('\n\tprotocol = "' + mapper['protocol'] + '"')
                            f_out.write('\n\tname = "' + mapper['name'] + '"')
                            f_out.write('\n\tprotocol_mapper = "' + mapper['protocolMapper'] + '"')
                            f_out.write('\n\tconfig = {')
                            for config in mapper['config']:
                                f_out.write('\n\t"' + config + '" = "' + mapper['config'][config] +'"')
                            f_out.write('\n\t}')
                            f_out.write('\n}\n')


def process_client_scopes():
    f = open('realm_dump.json')
    data = json.loads(f.read())
    with open('client_default_optional_scopes.tf', "w") as f_out:
        for client in data['clients']:
            if 'bearerOnly' in client:
                if not client['bearerOnly']:
                    if client['clientId'] not in default_accounts:
                        if len(client['defaultClientScopes']) > 0:
                            f_out.write('resource "keycloak_openid_client_default_scopes" "' + client['clientId'] + '_default_scopes" {')
                            f_out.write('\n\trealm_id = data.keycloak_realm.bcregistry_realm.id')
                            f_out.write('\n\tclient_id = keycloak_openid_client.' + client['clientId'].lower().replace(' ', '_') + '.id')
                            f_out.write('\n\tdefault_scopes = [')
                            for scope in client['defaultClientScopes']:
                                f_out.write('\n\t"' + scope + '",')
                            f_out.write('\n\t"email",')
                            f_out.write('\n\t"profile",')
                            if 'service-account' in client['clientId']:
                                f_out.write('\n\t"service-accounts-scope",')
                            f_out.write('\n\t]')
                            f_out.write('\n}\n')
                        if len(client['optionalClientScopes']) > 0:
                            f_out.write('resource "keycloak_openid_client_optional_scopes" "' + client['clientId'] + '_optional_scopes" {')
                            f_out.write('\n\trealm_id = data.keycloak_realm.bcregistry_realm.id')
                            f_out.write('\n\tclient_id = keycloak_openid_client.' + client['clientId'].lower().replace(' ', '_') + '.id')
                            f_out.write('\n\toptional_scopes = [')
                            for scope in client['optionalClientScopes']:
                                f_out.write('\n\t"' + scope + '",')
                            f_out.write('\n\t]')
                            f_out.write('\n}\n')


def process_client_roles():
    f = open('realm_dump.json')
    data = json.loads(f.read())
    with open('client_roles.tf', "w") as f_out:
        for client in data['roles']['client']:
            if client in default_accounts:
                for role in data['roles']['client'][client]:
                    f_out.write('data "keycloak_role" "' + role['name'] + '" {')
                    f_out.write('\n\trealm_id = data.keycloak_realm.bcregistry_realm.id')
                    f_out.write('\n\tclient_id = data.keycloak_openid_client.' + client + '.id')
                    f_out.write('\n\tname = "' + role['name'] + '"')
                    f_out.write('\n}\n')


def handle_subgroups(group, f_out):
    for subgroup in group['subGroups']:
        f_out.write('resource "keycloak_group" "' + subgroup['name'].lower().replace(' ', '_') + '" {')
        f_out.write('\n\trealm_id = data.keycloak_realm.bcregistry_realm.id')
        f_out.write('\n\tname = "' + subgroup['name'] + '"')
        f_out.write('\n\tparent_id = keycloak_group.' + group['name'].lower().replace(' ', '_') + '.id')
        f_out.write('\n}\n')
        if len(subgroup['subGroups']) > 0:
            handle_subgroups(subgroup, f_out)


def process_groups():
    f = open('realm_dump.json')
    data = json.loads(f.read())

    with open('groups.tf', "w") as f_out:
        for group in data['groups']:
            if group['name'] not in default_groups:
                f_out.write('resource "keycloak_group" "' + group['name'].lower().replace(' ', '_') + '" {')
                f_out.write('\n\trealm_id = data.keycloak_realm.bcregistry_realm.id')
                f_out.write('\n\tname = "' + group['name'] + '"')
                f_out.write('\n}\n')
                handle_subgroups(group, f_out)


def process_group_roles():
    f = open('realm_dump.json')
    data = json.loads(f.read())
    with open('group_roles.tf', "w") as f_out:
        for group in data['groups']:
            if len(group['realmRoles']) > 0:
                f_out.write('resource "keycloak_group_roles" "group_roles_' + group['name'].lower().replace(' ', '_') + '" {')
                f_out.write('\n\trealm_id = data.keycloak_realm.bcregistry_realm.id')
                f_out.write('\n\tgroup_id = keycloak_group.' + group['name'].lower().replace(' ', '_') + '.id')
                f_out.write('\n\trole_ids = [')
                for role in group['realmRoles']:
                    f_out.write('\n\t\t\tkeycloak_role.' + role.lower().replace(' ', '_') + '.id,')
                f_out.write('\n\t]')
                f_out.write('\n}\n')
                handle_subgroup_roles(group, f_out)


def handle_subgroup_roles(group, f_out):
    for subgroup in group['subGroups']:
        if len(subgroup['realmRoles']) > 0:
            f_out.write('resource "keycloak_group_roles" "group_roles_' + subgroup['name'].lower().replace(' ', '_') + '" {')
            f_out.write('\n\trealm_id = data.keycloak_realm.bcregistry_realm.id')
            f_out.write('\n\tgroup_id = keycloak_group.' + subgroup['name'].lower().replace(' ', '_') + '.id')
            f_out.write('\n\trole_ids = [')
            for role in subgroup['realmRoles']:
                f_out.write('\n\t\t\tkeycloak_role.' + role.lower().replace(' ', '_') + '.id,')
            f_out.write('\n\t]')
            f_out.write('\n}\n')
        if len(subgroup['subGroups']) > 0:
            handle_subgroup_roles(subgroup, f_out)


def process_clients_to_variable():
    f = open('realm_dump.json')
    data = json.loads(f.read())
    with open('client_vars.tf', "w") as f_out:
        for client in data['clients']:
            if client['clientId'] not in default_accounts:
                f_out.write('variable "' + client['clientId'].lower().replace(' ', '_') + '_client" {')
                f_out.write('\n\ttype = object({')
                f_out.write('\n\t\tid     = string')
                f_out.write('\n\t\tsecret = string')
                f_out.write('\n\t})')
                f_out.write('\n\t\tsensitive   = true')
                if 'description' in client:
                    f_out.write('\n\t\tdescription = "' + client['description'] + '"')
                f_out.write('\n\t}\n')
    with open('client_secrets.tfvars', "w") as f_out:
        for client in data['clients']:
            if client['clientId'] not in default_accounts:
                f_out.write(client['clientId'].lower().replace(' ', '_') + '_client = {')
                f_out.write('\n\t\tid     = "' + client['clientId'] + '"')
                f_out.write('\n\t\tsecret = "' + client['secret'] + '"')
                f_out.write('\n\t}\n')


def write_client(f_out, client):
    f_out.write('resource "keycloak_openid_client" "' + client['clientId'].lower().replace(' ', '_') + '" {')
    f_out.write('\n\trealm_id = data.keycloak_realm.bcregistry_realm.id')
    f_out.write('\n\tclient_id = var.' + client['clientId'].lower().replace(' ', '_') + '_client.id')
    f_out.write('\n\tclient_secret = var.' + client['clientId'].lower().replace(' ', '_') + '_client.secret')
    f_out.write('\n\tenabled = ' + str(client['enabled']).lower())
    bearer = False
    if 'bearerOnly' in client:
        if client['bearerOnly']:
            f_out.write('\n\taccess_type = "BEARER-ONLY"')
            bearer = True
    if (client['standardFlowEnabled'] or client['implicitFlowEnabled']) and not bearer:
        f_out.write('\n\tvalid_redirect_uris = [')
        for uri in client['redirectUris']:
            f_out.write('\n\t\t"' + uri + '",')
        f_out.write('\n\t]')
        f_out.write('\n\tweb_origins = [')
        for uri in client['webOrigins']:
            f_out.write('\n\t\t"' + uri + '",')
        f_out.write('\n\t]')
        if 'rootUrl' in client:
            f_out.write('\n\troot_url = "' + client['rootUrl'].replace('$', '$$') + '"')
        if 'baseUrl' in client:
            f_out.write('\n\tbase_url = "' + client['baseUrl'] + '"')
        if 'standardFlowEnabled' in client:
            f_out.write('\n\tstandard_flow_enabled = ' + str(client['standardFlowEnabled']).lower())
        if 'implicitFlowEnabled' in client:
            f_out.write('\n\timplicit_flow_enabled = ' + str(client['implicitFlowEnabled']).lower())
        if 'directAccessGrantsEnabled' in client:
            f_out.write('\n\tdirect_access_grants_enabled = ' + str(client['directAccessGrantsEnabled']).lower())
    if 'publicClient' in client and not bearer:
        if client['publicClient']:
            f_out.write('\n\taccess_type = "PUBLIC"')
        else:
            f_out.write('\n\taccess_type = "CONFIDENTIAL"')
            f_out.write('\n\tservice_accounts_enabled = ' + str(client['serviceAccountsEnabled']).lower())
    if 'name' in client:
        f_out.write('\n\tname = "' + client['name'].replace('$', '$$') + '"')
    if 'description' in client:
        f_out.write('\n\tdescription = "' + client['description'] + '"')
    if 'fullScopeAllowed' in client:
        f_out.write('\n\tfull_scope_allowed = ' + str(client['fullScopeAllowed']).lower())
    if 'clientAuthenticatorType' in client:
        f_out.write('\n\tclient_authenticator_type = "' + client['clientAuthenticatorType'] + '"')
    if 'consentRequired' in client:
        f_out.write('\n\tconsent_required = ' + str(client['consentRequired']).lower())
    if 'frontchannelLogout' in client:
        f_out.write('\n\tfrontchannel_logout_enabled = ' + str(client['frontchannelLogout']).lower())
    if 'adminUrl' in client:
        f_out.write('\n\tadmin_url = "' + client['adminUrl'] + '"')
    if 'authenticationFlowBindingOverrides' in client:
        f_out.write('\n\tauthentication_flow_binding_overrides {')
        for override_f in client['authenticationFlowBindingOverrides']:
            if client['authenticationFlowBindingOverrides'][override_f] in flow_id_alias:
                f_out.write('\n\t\t' + override_f + '_id = keycloak_authentication_flow.' + flow_id_alias[client['authenticationFlowBindingOverrides'][override_f]] + '.id')
        f_out.write('\n\t\t}')
    f_out.write('\n\t}\n')


def process_clients():
    f = open('realm_dump.json')
    data = json.loads(f.read())
    with open('clients.tf', "w") as f_out:
        for client in data['clients']:
            if client['clientId'] not in default_accounts:
                write_client(f_out, client)


def process_default_clients():
    f = open('realm_dump.json')
    data = json.loads(f.read())
    with open('default_clients.tf', "w") as f_out:
        for client in data['clients']:
            if client['clientId'] in default_accounts:
                f_out.write('data "keycloak_openid_client" "' + client['clientId'].lower().replace(' ', '_') + '" {')
                f_out.write('\n\trealm_id = data.keycloak_realm.bcregistry_realm.id')
                f_out.write('\n\tclient_id = "' + client['clientId'] + '"')
                f_out.write('\n\t}\n')


def process_default_roles():
    with open('default_roles.tf', "w") as f_out:
        for role in default_roles:
            f_out.write('data "keycloak_role" "realm_role_' + role + '" {')
            f_out.write('\n\trealm_id = data.keycloak_realm.bcregistry_realm.id')
            f_out.write('\n\tname = "' + role + '"')
            f_out.write('\n\t}\n')


def process_default_scopes():
    with open('default_scopes.tf', "w") as f_out:
        for scope in default_scopes:
            f_out.write('data "keycloak_openid_client_scope" "default_scope_' + scope + '" {')
            f_out.write('\n\trealm_id = data.keycloak_realm.bcregistry_realm.id')
            f_out.write('\n\tname = "' + scope + '"')
            f_out.write('\n\t}\n')


def process_scope_mappings():
    f = open('realm_dump.json')
    data = json.loads(f.read())
    with open('scope_role_mappers.tf', "w") as f_out:
        for mapper in data['scopeMappings']:
            for role in mapper['roles']:
                f_out.write('resource "keycloak_generic_role_mapper" "' + mapper['clientScope'] + '_' + role + '_mapper" {')
                f_out.write('\n\trealm_id = data.keycloak_realm.bcregistry_realm.id')
                if mapper['clientScope'] in default_scopes:
                    f_out.write('\n\tclient_scope_id = data.keycloak_openid_client_scope.default_scope_' + mapper['clientScope'] + '.id')
                    f_out.write('\n\trole_id = data.keycloak_role.realm_role_' + role + '.id')
                else:
                    f_out.write('\n\tclient_scope_id = keycloak_openid_client_scope.' + mapper['clientScope'] + '.id')
                    f_out.write('\n\trole_id = keycloak_role.' + role + '.id')
                f_out.write('\n\t}\n')


def process_service_account_roles():
    name_prefix = 'service-account-'
    f = open('realm_dump.json')
    data = json.loads(f.read())
    with open('service_accounts.tf', "w") as f_out:
        for user in data['users']:
            if user['username'].startswith(name_prefix):
                if 'clientRoles' in user or 'realmRoles' in user:
                    client_name = user['serviceAccountClientId']
                    client_list.append(client_name)
                if 'realmRoles' in user:
                    for role in user['realmRoles']:
                        if role not in default_roles:
                            f_out.write('resource "keycloak_openid_client_service_account_realm_role" "realm_role_' + user['username'] + '_' + role.lower().replace(' ', '_') + '" {')
                            f_out.write('\n\t\trealm_id = data.keycloak_realm.bcregistry_realm.id')
                            f_out.write('\n\t\trole = keycloak_role.' + role + '.name')
                            f_out.write('\n\t\tservice_account_user_id  = keycloak_openid_client.' + client_name.lower() + '.service_account_user_id')
                            f_out.write('\n\t}\n')
                if 'clientRoles' in user:
                    for client in user['clientRoles']:
                        for role in user['clientRoles'][client]:
                            if client_name.lower() not in default_accounts:
                                f_out.write('resource "keycloak_openid_client_service_account_role" "client_role_' + user['username'] + '_' + role.lower().replace(' ', '_') + '" {')
                                f_out.write('\n\t\tclient_id = data.keycloak_openid_client.' + client + '.id')
                                f_out.write('\n\t\trole = data.keycloak_role.' + role + '.name')
                                f_out.write('\n\t\tservice_account_user_id  = keycloak_openid_client.' + client_name.lower() + '.service_account_user_id')
                                f_out.write('\n\t\trealm_id = data.keycloak_realm.bcregistry_realm.id')
                                f_out.write('\n\t}\n')


def get_client_secret(base_url2, headers, client):
    url = base_url2 + "/clients/" + client['id'] + "/client-secret"
    client_secret = requests.request("GET", url, headers=headers)
    client['secret'] = client_secret.json()['value']


def write_idp_links(user, f_out):
    if 'attributes' in user and 'source' in user['attributes'] and user['attributes']['source'][0] == 'IDIR':
        f_out.write('\n\t\tidentity_provider = keycloak_oidc_identity_provider.idiridp.alias')
        if 'idir_userid' in user['attributes']:
            f_out.write('\n\t\tuser_id = "' + user['attributes']['idir_userid'][0].lower() + '@idir' + '"')
            f_out.write('\n\t\tuser_name = "' + user['attributes']['idir_userid'][0].lower() + '@idir' + '"')
        elif 'idp_userid' in user['attributes']:
            f_out.write('\n\t\tuser_id = "' + user['attributes']['idp_userid'][0].lower() + '@idir' + '"')
            f_out.write('\n\t\tuser_name = "' + user['attributes']['idp_userid'][0].lower() + '@idir' + '"')
    elif 'attributes' in user and  'source' in user['attributes'] and user['attributes']['source'][0] == 'BCEID':
        f_out.write('\n\t\tidentity_provider = keycloak_oidc_identity_provider.bceid.alias')
        if 'bceid_userid' in user['attributes']:
            f_out.write('\n\t\tuser_id = "' + user['attributes']['bceid_userid'][0].lower() + '@bceidboth' + '"')
            f_out.write('\n\t\tuser_name = "' + user['attributes']['bceid_userid'][0].lower() + '@bceidboth' + '"')
        elif 'idp_userid' in user['attributes']:
            f_out.write('\n\t\tuser_id = "' + user['attributes']['idp_userid'][0].lower() + '@bceidboth' + '"')
            f_out.write('\n\t\tuser_name = "' + user['attributes']['idp_userid'][0].lower() + '@bceidboth' + '"')
    elif ('attributes' in user and 'source' in user['attributes'] and user['attributes']['source'][0] == 'BCROS') or 'bcros' in user['username']:
        if 'idp_userid' in user['attributes']:
            f_out.write('\n\t\tidentity_provider = keycloak_oidc_identity_provider.bcros.alias')
            f_out.write('\n\t\tuser_id = "' + user['attributes']['idp_userid'][0].lower() + '"')
            f_out.write('\n\t\tuser_name = "' + user['username'][6:].lower() + '"')
    elif ('attributes' in user and 'source' in user['attributes'] and user['attributes']['source'][0] == 'BCSC') or 'bcsc/' in user['username']:
        f_out.write('\n\t\tidentity_provider = keycloak_oidc_identity_provider.bcsc.alias')
        f_out.write('\n\t\tuser_id = "' + user['username'][5:].upper() + '"')
        f_out.write('\n\t\tuser_name = "' + user['username'][5:].lower() + '"')
    elif 'username' in user and user['username'].endswith('@github'):
        github_base_url = 'https://api.github.com/users/'
        github_base_url += user['username'][:-7]
        response = requests.request("GET", github_base_url)
        response_json = response.json()
        if 'id' in response_json:
            f_out.write('\n\t\tfederated_identity {')
            f_out.write('\n\t\tidentity_provider = keycloak_oidc_identity_provider.github.alias')
            f_out.write('\n\t\tuser_id = "' + str(response_json['id']) + '@githubbcgov' + '"')
            f_out.write('\n\t\tuser_name = "' + str(response_json['id']) + '@githubbcgov' + '"')
            f_out.write('\n\t\t}')


def save_managed_users_to_file(users, groups):
    with open('users.tf', 'w') as f_out:
        for user2 in users:
            if ('attributes' in user2 and 'source' in user2['attributes']) or 'github' in user2['username']:
                username = user2['username']
                if '\\' in username:
                    res = username.split('\\', 1)
                    username = res[1] + '@' + res[0]

                f_out.write('resource "keycloak_user" "' + username.replace('@', '_').replace('\\', '_').replace('.', '_').replace('/', '_') + '" {')
                f_out.write('\n\t\trealm_id = data.keycloak_realm.bcregistry_realm.id')
                f_out.write('\n\t\tusername = "' + username + '"')
                f_out.write('\n\t\tenabled = ' + str(user2['enabled']).lower())
                if 'firstName' in user2:
                    f_out.write('\n\t\tfirst_name = "' + user2['firstName'] + '"')
                if 'lastName' in user2:
                    f_out.write('\n\t\tlast_name = "' + user2['lastName'] + '"')
                if 'attributes' in user2:
                    new_att = {}
                    for att, val in user2['attributes'].items():
                        new_att[att] = val[0]
                    f_out.write('\n\t\tattributes = ' + json.dumps(new_att))
                    if 'source' in user2['attributes'] and user2['attributes']['source'][0] in ['BCEID', 'IDIR', 'BCROS', 'BCSC']:
                        f_out.write('\n\t\tfederated_identity {')
                        write_idp_links(user2, f_out)
                        f_out.write('\n\t\t}')
                elif 'username' in user2 and user2['username'].endswith('@github'):
                    write_idp_links(user2, f_out)
                f_out.write('\n\t}\n')

    with open('memberships.tf', 'w') as f_out:
        for group, users in groups.items():
            f_out.write('resource "keycloak_group_memberships" "' + group.replace(' ', '_').lower() + '_group_members" {')
            f_out.write('\n\t\trealm_id = data.keycloak_realm.bcregistry_realm.id')
            f_out.write('\n\t\tgroup_id = keycloak_group.' + group.replace(' ', '_').lower() +'.id')
            f_out.write('\n\t\t members  = [')
            for user3 in users:
                if ('attributes' in user3 and 'source' in user3['attributes']) or 'github' in user3['username']:
                    username = user3['username']
                    if '\\' in username:
                        res = username.split('\\', 1)
                        username = res[1] + '@' + res[0]
                    f_out.write('\n\t\t\tkeycloak_user.' + username.replace('@', '_').replace('\\', '_').replace('.', '_').replace('/', '_') + '.username,')
            f_out.write('\n\t\t]')
            f_out.write('\n\t}\n')


def process_all_users_in_group(base_url2, headers, group, groups):
    name_prefix = 'service-account-'
    url = base_url2 + f'/groups/{group["id"]}/members?max=1000000'
    response = requests.request("GET", url, headers=headers)
    for member in response.json():
        if not member['username'].startswith(name_prefix):
            try:
                if member['username'] not in groups:
                    groups[member['username']] = [group['path']]
                else:
                    groups[member['username']].append(group['path'])
            except AttributeError:
                print(member)
    if group['subGroups']:
        for children in group['subGroups']:
            process_all_users_in_group(base_url2, headers, children, groups)


def export_data(client, token, base_url, realm):
    start = time.time()
    url = base_url + "/auth/realms/" + realm + "/protocol/openid-connect/token"
    print('...')
    payload = "grant_type=client_credentials"
    auth_str = client + ":" + token
    basic_hash = base64.b64encode(auth_str.encode()).decode()
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {basic_hash}'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    token = response.json()['access_token']

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }

    base_url2 = base_url + "/auth/admin/realms/" + realm

    # EXPORT DB
    url = base_url2 + "/partial-export?exportClients=true&exportGroupsAndRoles=true"
    response = requests.request("POST", url, headers=headers)
    print(response.status_code)
    response_json = response.json()

    print("exported db")
    stop = time.time()
    print(stop-start)

    # PULL CLIENT SECRETS
    for client in response_json['clients']:
        url = base_url2 + "/clients/" + client['id'] + "/client-secret"
        client_secret = requests.request("GET", url, headers=headers)
        if 'value' in client_secret.json():
            client['secret'] = client_secret.json()['value']

    print("collected client secrets")
    stop = time.time()
    print(stop-start)

    print("pulled groups")
    url = base_url2 + "/groups?max=1000"
    response = requests.request("GET", url, headers=headers)

    dump_json = response.json()

    ix = 0
    max_val = 10000
    users_json = []

    print("processing users...")
    while True:
        url = base_url2 + "/users?first=" + str(ix*max_val) + "&max=" + str(max_val)
        user_resp = requests.request("GET", url, headers=headers)
        if user_resp.status_code == 200:
            ix += 1
            res_json = user_resp.json()
            if len(res_json) == 0:
                break
            else:
                users_json.extend(res_json)
                print(ix*max_val)

    print('number of users before get users api call:')
    print(len(response_json['users']))

    response_json['users'].extend(users_json)
    print('number of users after get users api call:')
    print(len(response_json['users']))

    user_groups = {}
    for group in dump_json:
        process_all_users_in_group(base_url2, headers, group, user_groups)

    print("processed group memberships")
    stop = time.time()
    print(stop - start)

    for user in response_json['users']:
        if user['username'] in user_groups:
            user['groups'] = user_groups[user['username']]
    print("processed user roles")
    stop = time.time()
    print(stop - start)

    with open('realm_dump.json', 'w') as f:
        json.dump(response_json, f, ensure_ascii=False, indent=4)
    print('realm exported')


def process_authentications():
    f = open('realm_dump.json')
    data = json.loads(f.read())

    execution_config_map = {}
    subflows = {}
    last_exec_step = ''
    with open('authflows.tf', "w") as f_out:
        for flow in data['authenticationFlows']:
            exec_step = 0
            flow_id = 'flow_' + flow['alias'].lower().replace(' ', '_')
            flow_id_alias[flow['id']] = flow_id
            if flow['alias'] not in default_flows:
                if flow['alias'] in subflows:
                    f_out.write('resource "keycloak_authentication_subflow" "' + flow_id + '" {')
                    f_out.write('\n\t\trealm_id = data.keycloak_realm.bcregistry_realm.id')
                    f_out.write('\n\t\talias = "' + flow['alias'] + '"')
                    f_out.write('\n\t\tparent_flow_alias = "' + subflows[flow['alias']][1] + '"')
                    f_out.write('\n\t\trequirement = "' + subflows[flow['alias']][2] + '"')
                    f_out.write('\n\t\tdescription = "' + flow['description'] + '"')
                    f_out.write('\n\t depends_on = [')
                    f_out.write('\n\t\tkeycloak_authentication_execution.flow_' + subflows[flow['alias']][0])
                    f_out.write('\n\t ]')
                    f_out.write('\n\t}\n')
                else:
                    f_out.write('resource "keycloak_authentication_flow" "' + flow_id + '" {')
                    f_out.write('\n\t\trealm_id = data.keycloak_realm.bcregistry_realm.id')
                    f_out.write('\n\t\talias = "' + flow['alias'] + '"')
                    f_out.write('\n\t\tdescription = "' + flow['description'] + '"')
                    f_out.write('\n\t}\n')
                if flow['alias'] in subflows or flow['alias'] not in default_flows:
                    for auth_step in flow['authenticationExecutions']:
                        if not 'flowAlias' in auth_step:
                            exec_step += 1
                            f_out.write('resource "keycloak_authentication_execution" "' + flow_id + '_execution_' + str(exec_step) + '" {')
                            f_out.write('\n\t\trealm_id = data.keycloak_realm.bcregistry_realm.id')
                            if flow['alias'] in subflows:
                                f_out.write('\n\t\tparent_flow_alias = keycloak_authentication_subflow.' + flow_id + '.alias')
                            else:
                                f_out.write('\n\t\tparent_flow_alias = keycloak_authentication_flow.' + flow_id + '.alias')
                            f_out.write('\n\t\tauthenticator = "' + auth_step['authenticator'] + '"')
                            f_out.write('\n\t\trequirement = "' + auth_step['requirement'] + '"')
                            if exec_step > 1:
                                f_out.write('\n\t depends_on = [')
                                f_out.write('\n\t\tkeycloak_authentication_execution.flow_' + last_exec_step)
                                f_out.write('\n\t ]')
                            f_out.write('\n\t}\n')
                            last_exec_step = flow['alias'].lower().replace(' ', '_') + '_execution_' + str(exec_step)
                            if 'authenticatorConfig' in auth_step:
                                if not auth_step['authenticatorConfig'] in execution_config_map:
                                    execution_config_map[auth_step['authenticatorConfig']] = []
                                execution_config_map[auth_step['authenticatorConfig']].append(flow_id + '_execution_' + str(exec_step))
                        else:
                            subflows[auth_step['flowAlias']] = [last_exec_step, flow['alias'], auth_step['requirement']]
    with open('authconfigs.tf', "w") as f_out:
        for config in data['authenticatorConfig']:
            if config['alias'] in execution_config_map:
                for exec_step in execution_config_map[config['alias']]:
                    f_out.write('resource "keycloak_authentication_execution_config" "config_' + exec_step + '" {')
                    f_out.write('\n\t\trealm_id = data.keycloak_realm.bcregistry_realm.id')
                    f_out.write('\n\t\talias = "' + config['alias'] + '"')
                    f_out.write('\n\t\texecution_id = keycloak_authentication_execution.' + exec_step + '.id')
                    f_out.write('\n\t\tconfig = {')
                    for c in config['config']:
                        f_out.write('\n\t\t"' + c + '" = "' + config['config'][c] + '"')
                    f_out.write('\n\t\t}')
                    f_out.write('\n\t}\n')


def process_scope_mappers():
    f = open('realm_dump.json')
    data = json.loads(f.read())

    with open('client_scope_mappers.tf', "w") as f_out:
        for scope in data['clientScopes']:
            if scope['name'] in extra_scopes and 'protocolMappers' in scope:
                for mapper in scope['protocolMappers']:
                    f_out.write('resource "keycloak_generic_protocol_mapper" "scope_' + scope['name'] + '_mapper_' + mapper['name'] + '" {')
                    f_out.write('\n\trealm_id = data.keycloak_realm.bcregistry_realm.id')
                    f_out.write('\n\tclient_scope_id = keycloak_openid_client_scope.' + scope['name'] + '.id')
                    f_out.write('\n\tprotocol = "' + mapper['protocol'] + '"')
                    f_out.write('\n\tname = "' + mapper['name'] + '"')
                    f_out.write('\n\tprotocol_mapper = "' + mapper['protocolMapper'] + '"')
                    f_out.write('\n\tconfig = {')
                    for config in mapper['config']:
                        f_out.write('\n\t"' + config + '" = "' + mapper['config'][config] + '"')
                    f_out.write('\n\t}')
                    f_out.write('\n}\n')


def main(client, client_creds, kc_url, realm):
    # export realm contents to a .json file
    export_data(client, client_creds, kc_url, realm)
    # create terraform config files that need from the exported realm's .json
    process_realm_roles()
    process_groups()
    process_authentications()
    process_scope_mappers()
    process_group_roles()
    process_service_account_roles()
    process_clients_to_variable()
    process_clients()
    process_default_clients()
    process_client_roles()
    process_default_roles()
    process_default_scopes()
    process_scope_mappings()
    process_client_scopes()
    process_client_mappers()


if __name__ == '__main__':

    flow_id_alias = {}
    default_accounts = ['account', 'account-console', 'admin-cli', 'broker', 'realm-admin-cli', 'realm-management',
                        'realm-viewer-cli', 'security-admin-console']
    default_groups = ['Realm Administrator']
    default_roles = ['offline_access', 'uma_authorization']
    default_scopes = ['acr', 'web-origins', 'profile', 'roles', 'role_list', 'email', 'address', 'phone',
                      'offline_access', 'microprofile-jwt']

    default_mapper_names = ['Client ID', 'Client IP Address', 'Client Host']
    default_flows = ['browser', 'direct grant', 'registration', 'reset credentials', 'clients', 'first broker login',
                     'docker auth', 'http challenge', 'saml ecp', 'registration form', 'forms',
                     'Handle Existing Account', 'Verify Existing Account by Re-authentication',
                     'Verify Existing Account by Re-authentication - auth-otp-form - Conditional']
    extra_scopes = ['namex-scope', 'argocd-groups'] # for now manually create these
    client_list = []
