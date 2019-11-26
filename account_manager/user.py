import logging
import warnings
import json
from pathlib import Path
from time import sleep
from urllib.parse import urlparse, quote

from O365.utils import ApiComponent, Pagination

# class Users(ApiComponent):
#     _endpoints = {
#         # endpoints for user controls
#         'users': '/users'
#     }

#     def __init__(self, *,parent=None, con=None, **kwargs):

#         if parent and con:
#             raise ValueError('Need a parent or a connection but not both')
#         self.con = parent.con if parent else con
#         self.parent = parent if isinstance(parent, User) else None

#         super().__init(
#             protocol = kwargs.get('protocol')
#         ) 

#         cloud_data = kwargs.get(self._cloud_data_key, {})

#         def get_users(self):


class User(ApiComponent):
    """ A user representation. """

    _endpoints = {
        # endpoints for user controls
        'user': '/users/{id}',
        'users': '/users', 
    }

    def __init__(self, *, parent=None, con=None, **kwargs):
        """ Create a user representation

        :param parent: parent for this operation
        :type parent: User
        :param Connection con: connection to use if no parent specified
        :param Protocol protocol: protocol to use if no parent specified
        (kwargs)
        :param str main_resource: use this resource instad of parent resource
        (kwargs)
        """
        if parent and con:
            raise ValueError('Need a parent or a connection but not both')
        self.con = parent.con if parent else con
        self.parent = parent if isinstance(parent, User) else None

        # Choose the main_resource passed in kwargs over parent main_resource
        main_resource = kwargs.pop('main_resource', None) or (
            getattr(parent, 'main_resource', None) if parent else None)
        super().__init__(
            protocol=parent.protocol if parent else kwargs.get('protocol'),
            main_resource=main_resource
        )

        cloud_data = kwargs.get(self._cloud_data_key, {})

        # self.name = cloud_data.get(self._cc('name'), '') there is no name
        self.user_id = cloud_data.get(self._cc('id'), None)
        self.account_enabled = cloud_data.get(self._cc('accountEnabled'), False)
        self.assigned_licenses = cloud_data.get(self._cc('assignedLicenses'))
        self.department = cloud_data.get(self._cc('department'), '')
        self.job_title = cloud_data.get(self._cc('jobTitle'), '')
        self.display_name = cloud_data.get(self._cc('displayName'), '')
        self.first_name = cloud_data.get(self._cc('givenName'), '')
        self.last_name = cloud_data.get(self._cc('surname'), '')
        self.email_address = cloud_data.get(self._cc('mailNickname'), '')
        self.user_type = cloud_data.get(self._cc('userType'), '')
        self.user_principal_name = cloud_data.get(self._cc('userPrincipalName'), '')

    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return 'User: {}'.format(self.display_name or self.email_address or 'No User')
    
    def __eq__(self, other):
        return self.user_id == other.user_id
    
    def get_users(self):
        """ Get list of all users

        :return: List of all users
        :rtype: JSON
        """

        url = self.build_url(self._endpoints.get('users'))

        response = self.con.get(url)

        #users = parse

        if not response:
            return None

        data = response.json()['value']
        users = []

        # maybe the actual response without json just drops in to user? for d in data: user=User(response) users.append(user)? that be cool... thats not
        # cause you cant itterate over that object. Look into how cloud_data works. Else the below will work too.
        for u in data:
            user = User()
            user.user_id = u['id']
            user.account_enabled = u['accountEnabled']
            user.assigned_licenses = u['assignedLicenses']
            user.department = u['department']
            user.job_title = u['jobTitle']
            user.display_name = u['displayName']
            user.first_name = u['givenName']
            user.last_name = u['surname']
            # user.email_address = u

            users.append(user)





        return users

    def get_user(self):
        """ Get single user

        :return: Single User
        :rtype: User
        """

        url = self.build_url(self._endpoints.get('user'))
        pass

    def new_user(self, first_name, last_name, account_enabled=False):
        """ Creates a user

        :return: a new User
        :rtype: User
        """
        if not first_name or last_name:
            return None

        url = self.build_url(self._endpoints.get('users'))

        display_name = first_name + ' ' + last_name
        mail_nickname = first_name[0].lower() + last_name.lower() + "@decisionpointcenter.com"
        user_principal_name = mail_nickname
        
        response = self.con.post(url, data={self._cc('givenName'): first_name, self._cc('surname'): last_name,
                                            self._cc('displayName'): display_name, self._cc('mailNickname'): mail_nickname,
                                            self._cc('userPrincipalName'): user_principal_name, self._cc('accountEnabled'): account_enabled
        })

        if not response:
            return None
        
        data = response.json()

    def update(self):
        """ Updates this user. 

        :return: Success/Failure
        :rtype: bool
        """

        if not self.user_id:
            return False

        url = self.build_url(self._endpoints.get('user'))


    # This needs to be made to convert data to JSON to send to Microsoft for this class 
    def to_api_data(self):
        """ Returns a dict to communicate with the server
        :rtype: dict
        """
        data = []
        for attendee in self.__attendees:
            if attendee.address:
                att_data = {
                    self._cc('emailAddress'): {
                        self._cc('address'): attendee.address,
                        self._cc('name'): attendee.name
                    },
                    self._cc('type'): self._cc(attendee.attendee_type.value)
                }
                data.append(att_data)
        return data


#add user 
#block user login
#create user backup data through content search
#download backup data through export of content search (don't think this is possible)

