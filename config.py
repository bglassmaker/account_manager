import os

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'you-will-never-guess'
    LDAP_HOST = '192.168.56.10'
    LDAP_PORT = 636
    LDAP_USE_SSL = True
    LDAP_BASE_DN = 'dc=TestDomain,dc=local'
    LDAP_USER_DN = 'ou=Users'
    LDAP_GROUP_DN = 'ou=Security Groups'
    LDAP_USER_RDN_ATTR = 'cn'
    LDAP_BIND_AUTHENTICATION_TYPE = 'NTLM'
    LDAP_USER_LOGIN_ATTR = 'userPrincipalName'
