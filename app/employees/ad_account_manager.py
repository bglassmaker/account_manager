import ldap3
import logging
from app.employees.employee import Employee
try:
    from flask import _app_ctx_stack as stack
except ImportError:  # pragma: no cover
    from flask import _request_ctx_stack as stack

log = logging.getLogger(__name__)

#_base_ou = "ou=DecisionPointCenter,dc=DecisionPointCenter,dc=local"
_base_ou = "ou=TestDomain,dc=testdomain,dc=local"

class ADAccountManager():
    
    def __init__(self, app=None):
        self.config = {}
        self._ad_server_pool = ldap3.ServerPool(
            [],
            ldap3.FIRST,
            active=1,
            exhaust=10
        )

        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        app.ad_account_manager = self

        servers = list(self._ad_server_pool)
        for s in servers:
            self._ad_server_pool.remove(s)
        self.init_config(app.config)

        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:  # pragma: no cover
            app.teardown_request(self.teardown)

        self.app = app

    def init_config(self, config):
        self.config.update(config)

    def _contextualise_connection(self, connection):
        """
        Add a connection to the appcontext so it can be freed/unbound at
        a later time if an exception occured and it was not freed.

        Args:
            connection (ldap3.Connection): Connection to add to the appcontext

        """

        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'ldap3_manager_connections'):
                ctx.ldap3_manager_connections = [connection]
            else:
                ctx.ldap3_manager_connections.append(connection)

    def _decontextualise_connection(self, connection):
        """
        Remove a connection from the appcontext.

        Args:
            connection (ldap3.Connection): connection to remove from the
                appcontext

        """

        ctx = stack.top
        if ctx is not None and connection in ctx.ldap3_manager_connections:
            ctx.ldap3_manager_connections.remove(connection)

    def teardown(self, exception):
        """
        Cleanup after a request. Close any open connections.
        """

        ctx = stack.top
        if ctx is not None:
            if hasattr(ctx, 'ldap3_manager_connections'):
                for connection in ctx.ldap3_manager_connections:
                    self.destroy_connection(connection)
            if hasattr(ctx, 'ldap3_manager_main_connection'):
                log.debug(
                    "Unbinding a connection used within the request context.")
                ctx.ldap3_manager_main_connection.unbind()
                ctx.ldap3_manager_main_connection = None
  
    def _make_connection(self, user:None, bind_user:None, bind_password:None, contextualise=True):
        if user and (bind_user or bind_password):
            log.error('Please only provide a user or bind user')
            raise ValueError('Please only provide a user or bind user, not both.')
        log.debug('Opening connection with {}.'.format(bind_user))
        connection = ldap3.Connection(
            self.ad_server, 
            user= user.dn or bind_user, 
            password= user.password or bind_password,
            client_strategy=ldap3.SYNC,
            raise_exceptions=True
        )

        if contextualise:
            self._contextualise_connection(connection)
        return connection

    def destroy_connection(self, connection):
        """
        Destroys a connection. Removes the connection from the appcontext, and
        unbinds it.

        Args:
            connection (ldap3.Connection):  The connnection to destroy
        """

        log.debug("Destroying connection at <{0}>".format(hex(id(connection))))
        self._decontextualise_connection(connection)
        self.destroy_connection(connection)
    
    def get_ad_user(self, user, username:str):
        
        connection = self._make_connection(user=user)
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
        self.destroy_connection(connection)
        return response
    
    def reset_ad_password(self, user, employee) -> bool:

        connection = self._make_connection(user=user)
        connection.bind()
        
        employee.password = employee._random_password(8)

        connection.extend.microsoft.modify_password(employee.dn, employee.password)
        connection.modify(employee.dn, {'pwdLastSet': ('MODIFY_REPLACE', [0])})
        result = connection.result
        self.destroy_connection(connection)
        if result['result'] > 0:
            log.error(result['description'])
            return False
        return True

    def unlock_ad_account(self, user, employee) -> bool:
        connection = self._make_connection(user=user)
        connection.bind()

        connection.extend.microsoft.unlock_account(employee.dn)
        result = connection.result
        self.destroy_connection(connection)
        
        if result['result'] > 0:
            log.error(result['description'])
            return False
        return True

    def suspend_ad_account(self, user, employee) -> bool:
        connection = self._make_connection(user=user)
        connection.bind()

        disabled_path = "ou=Disabled Users,{}".format(_base_ou)
        #disable user
        connection.modify(employee.dn, {'userAccountControl': [('MODIFY_REPLACE', 514)]})
        #move user to disabled
        connection.modify_dn(employee.dn, 'cn={}'.format(employee.full_name), new_superior=disabled_path)
        result = connection.result
        self.destroy_connection(connection)
        if result['result'] > 0:
            log.error(result)
            return False
        return True
    
    def enable_ad_account(self, user, employee) -> bool:
        connection = self._make_connection(user=user)
        connection.bind()
            
        enabled_path = "ou=Domain Users,ou={} Office,{}".format(employee.location, _base_ou)
        #Enable user
        connection.modify(employee.dn, {'userAccountControl': [('MODIFY_REPLACE', 512)]})
        #move user to DN
        connection.modify_dn(employee.dn, 'cn={}'.format(employee.full_name), new_superior=enabled_path)
        result = connection.result
        self.destroy_connection(connection)
        if result['result'] > 0:
            log.debug(result)
            return False
        return True
    
    def create_ad_account(self, user, employee):
        connection = self._make_connection(user=user)
        connection.bind()

        if self._check_if_username_exists(employee):
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
        
        self.destroy_connection(connection)
        return response
    
    def _check_if_username_exists(self, user, employee) -> bool:
        connection = self._make_connection(user=user)
        connection.bind()
        search = connection.search(
            search_base=_base_ou, 
            search_filter='(sAMAccountName={})'.format(employee.username)
            )
        self.destroy_connection(connection)
        return search
