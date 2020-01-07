from O365.utils import ApiComponent
from O365 import Account

class User(ApiComponent): 
    '''
    Office 365
    '''

    endpoints = {
        # endpoints for user controls
        'user': '/users/{id}',
        'users': '/users', 
    }

    def __init__(self, *, parent=None, con=None, **kwargs):
        if parent and con:
            raise ValueError('Need a parent or a connection but not both')
        self.con = parent.con if parent else con

        # Choose the main_resource passed in kwargs over the parent main_resource
        main_resource = kwargs.pop('main_resource', None) or (
            getattr(parent, 'main_resource', None) if parent else None)

        super().__init__(protocol=parent.protocol if parent else kwargs.get('protocol'), main_resource=main_resource)

        cloud_data = kwargs.get(self._cloud_data_key, {})

        self.object_id = cloud_data.get('id')
        self.account_enabled = cloud_data.get('accountEnabled')
        self.assigned_licenses = cloud_data.get('assignedLicenses')
        self.assigned_license_status = cloud_data.get('licenseAssignmentStates') #read only
        self.department = cloud_data.get('department')
        self.job_title = cloud_data.get('jobTitle')
        self.full_name = cloud_data.get('displayName')
        self.first_name = cloud_data.get('givenName')
        self.last_name = cloud_data.get('surname')
        self.user_principal_name = cloud_data.get('userPrincipalName')
        self.email = cloud_data.get('mail') #read only
        self.mailNickname = cloud_data.get('mailNickname')
        self.email_alias = cloud_data.get('otherMails')
        self.show_in_address_boot = cloud_data.get('showInAddressList')
        self.user_type = cloud_data.get('userType')

    def create_o365_account(self, employee):
        """ Creates a user

        :return: a new User
        :rtype: User
        """
        url = self.build_url(self._endpoints.get('users'))

        data={
            'givenName': employee.first_name, 
            'surname': employee.last_name,
            'displayName': employee.full_name, 
            'mailNickname': employee.username,
            'userPrincipalName': employee.email_address, 
            'accountEnabled': True,
            'jobTitle': employee.job_title,
            'department': employee.department,
            'passwordProfile': {
                "forceChangePasswordNextSignIn": True,
                "password": employee.password
            }
        }
    
        response = self.con.post(url, data)

        if not response:
            return None
        
        return response.json()

    def update_o365_account_status(self, user_principal_name, account_enabled):
        if not user_principal_name:
            raise ValueError("Please provide a valid username")
        if not account_enabled:
            raise ValueError("Please provide a valid account status")

        data = {
            'accountEnabled': account_enabled
        }

        url = self.build_url(self._endpoints.get('user')).format(id=user_principal_name)
        response = self.con.post(url, data)

        if not response:
            return None
        
        return response.json()
   
    def get_o365_user(self, user_principal_name):
        """ Get single user

        :return: Single User
        :rtype: User
        """
        if not user_principal_name:
            raise ValueError('This requires a UserID')

        url = self.build_url(self._endpoints.get('user')).format(id=user_principal_name)
        
        response = self.con.get(url)

        if not response:
            return None
        
        data = response.json()

        return data