import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'you-will-never-guess'
    LDAP_HOST = '192.168.56.10'
    #LDAP_PORT = 636
    #LDAP_USE_SSL = True
    LDAP_BASE_DN = 'dc=testdomain,dc=local'
    LDAP_USER_DN = 'ou=TestDomain'
    # LDAP_GROUP_DN = 'ou=Security Groups'
    LDAP_USER_RDN_ATTR = 'cn'
    #LDAP_BIND_AUTHENTICATION_TYPE = 'NTLM'
    LDAP_USER_LOGIN_ATTR = 'sAMACCOUNTName'
    LDAP_BIND_USER_DN = os.environ.get('ADUSERTEST')
    LDAP_BIND_USER_PASSWORD = os.environ.get('ADPASSWORDTEST')
    #LDAP_BIND_DIRECT_CREDENTIALS = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
