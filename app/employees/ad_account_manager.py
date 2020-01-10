import os
import ldap3
import logging
from app.employees.employee import Employee

log = logging.getLogger(__name__)

#_base_ou = 'ou=DecisionPointCenter,dc=DecisionPointCenter,dc=local'
_base_ou = 'ou=TestDomain,dc=testdomain,dc=local'
_ad_server = 'testdomain.local'

  
def _make_connection(user:None, bind_user:None, bind_password:None):
    if user and (bind_user or bind_password):
        log.error('Please only provide a user or bind user')
        raise ValueError('Please only provide a user or bind user, not both.')
    log.debug('Opening connection with {}.'.format(bind_user))
    connection = ldap3.Connection(
        _ad_server, 
        user= user.dn or bind_user, 
        password= user.password or bind_password,
        client_strategy=ldap3.SYNC,
        raise_exceptions=True
    )

def get_ad_user(user, username:str):
    
    connection = _make_connection(user=user)
    connection.bind()
    
    connection.search(
        search_base=_base_ou, 
        search_filter='(sAMAccountName={})'.format(username), 
        attributes=['givenName', 'sn', 'userAccountControl','mail','sAMAccountName','physicalDeliveryOfficeName'])
    
    response = None
    if len(connection.response) == 0:
        log.error('Could not get user with username : {}'.format(username))
    else:
        response = connection.response[0]  

        employee = Employee(
            first_name = response['attributes']['givenName'],
            last_name = response['attributes']['sn'],
            dn = response['dn'],
            user_account_control = response['attributes']['userAccountControl'],
            email = response['attributes']['mail'],
            username = response['attributes']['sAMAccountName'],
            location = response['attributes']['physicalDeliveryOfficeName']
        )
        response = employee
    connection.unbind()
    return response

def reset_ad_password(user, employee) -> bool:

    connection = _make_connection(user=user)
    connection.bind()
    
    employee.password = employee._random_password(8)

    connection.extend.microsoft.modify_password(employee.dn, employee.password)
    connection.modify(employee.dn, {'pwdLastSet': ('MODIFY_REPLACE', [0])})
    result = connection.result
    connection.unbind()
    if result['result'] > 0:
        log.error(result['description'])
        return False
    return True

def unlock_ad_account(user, employee) -> bool:
    connection = _make_connection(user=user)
    connection.bind()

    connection.extend.microsoft.unlock_account(employee.dn)
    result = connection.result
    connection.unbind()
    
    if result['result'] > 0:
        log.error(result['description'])
        return False
    return True

def suspend_ad_account(user, employee) -> bool:
    connection = _make_connection(user=user)
    connection.bind()

    disabled_path = "ou=Disabled Users,{}".format(_base_ou)
    #disable user
    connection.modify(employee.dn, {'userAccountControl': [('MODIFY_REPLACE', 514)]})
    #move user to disabled
    connection.modify_dn(employee.dn, 'cn={}'.format(employee.full_name), new_superior=disabled_path)
    result = connection.result
    connection.unbind()
    if result['result'] > 0:
        log.error(result)
        return False
    return True

def enable_ad_account(user, employee) -> bool:
    connection = _make_connection(user=user)
    connection.bind()
        
    enabled_path = "ou=Domain Users,ou={} Office,{}".format(employee.location, _base_ou)
    #Enable user
    connection.modify(employee.dn, {'userAccountControl': [('MODIFY_REPLACE', 512)]})
    #move user to DN
    connection.modify_dn(employee.dn, 'cn={}'.format(employee.full_name), new_superior=enabled_path)
    result = connection.result
    connection.unbind()
    if result['result'] > 0:
        log.debug(result)
        return False
    return True

def create_ad_account(user, employee):
    connection = _make_connection(user=user)
    connection.bind()

    if _check_if_username_exists(employee):
        raise ValueError("Username already exists")

    response = None
    log.debug('Adding user {}'.format(employee.dn))
    connection.add(
        employee.dn, 
        ['person', 'user'], 
        {
            'sAMAccountName': employee.username, 
            'userPrincipalName': employee.username + '@testdomain.local', 
            'givenName': employee.first_name, 
            'sn': employee.last_name, 
            'displayName': employee.full_name,
            'mail': employee.email_address,
            'company': 'Decision Point Center',
            'department': employee.department,
            'title': employee.job_title,
            'physicalDeliveryOfficeName': employee.location        
        })
    
    if connection.result > 0:
        log.error('User could not be created for {}.'.format(employee.dn))
        response = connection.result
    else:
        log.debug('User {} created.'.format(employee.dn))
        response = connection.response # set response to initial add response
        connection.extend.microsoft.modify_password(employee.dn, employee.password)
        if connection.result > 0:
            log.error('Password could not be set for {}'.format(employee.dn))
            response = connection.result
        else: 
            log.debug('Password set for {}.'.format(employee.dn))           
            connection.modify(employee.dn, {'userAccountControl': ('MODIFY_REPLACE', [512])})
            if connection.result > 0:
                log.error('Account could not be activated for {}'.format(employee.dn))
                response = connection.result
            else:
                log.debug('Account activated for {}.'.format(employee.dn))
                connection.modify(employee.dn, {'pwdLastSet': ('MODIFY_REPLACE', [0])})
                if connection.result > 0:
                    log.error('Account not set to force password change for {}'.format(employee.dn))
                    response = connection.result
                else:
                    log.debug('Account set to force password change for {}.'.format(employee.dn))
    
    connection.unbind()
    return response

def _check_if_username_exists(user, employee) -> bool:
    connection = _make_connection(user=user)
    connection.bind()
    search = connection.search(
        search_base=_base_ou, 
        search_filter='(sAMAccountName={})'.format(employee.username)
        )
    connection.unbind()
    return search
