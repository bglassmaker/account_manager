import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'you-will-never-guess'
    # LDAP Settings
    LDAP_HOST = 'testdomain.local'
    LDAP_BASE_DN = 'dc=testdomain,dc=local'
    LDAP_USER_DN = 'ou=TestDomain'
    # LDAP_GROUP_DN = 'ou=Security Groups'
    LDAP_USER_RDN_ATTR = 'cn'
    LDAP_USER_LOGIN_ATTR = 'sAMACCOUNTName'
    LDAP_BIND_USER_DN = os.environ.get('ADUSERTEST')
    LDAP_BIND_USER_PASSWORD = os.environ.get('ADPASSWORDTEST')

