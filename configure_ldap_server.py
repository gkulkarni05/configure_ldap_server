
# This script has been tested on Python 2.7.5
#!/usr/bin/python

import os
import sys
import platform
import math
import os.path
from os import path

# All the configuration files, LDAP base structure files, and files required to import users and groups are defined in variables. These variables should point to correct files.  

# "selinux-policy" needs update due to BUG #1536011

server_packages ="openldap openldap-servers openldap-clients selinux-policy"
hdb_config_file ="/etc/openldap/slapd.d/cn=config/olcDatabase={2}hdb.ldif"
db_config ="/etc/openldap/slapd.d/cn=config/olcDatabase={0}config.ldif"
dc = "dc=example,dc=com"
root_pw ="redhat"
ldap_service ="slapd"
base_struct_file = "/root/base.ldif"
user_add_file = "/root/users.ldif"
group_add_file = "/root/groups.ldif"
schema_cosine = "/etc/openldap/schema/cosine.ldif"
schema_nis = "/etc/openldap/schema/nis.ldif"
schema_inetorgperson = "/etc/openldap/schema/inetorgperson.ldif"
ldapadd_base_cmd = "ldapadd -x -D 'cn=Manager,"+dc+"' "+" -w "+root_pw+" -f %s" 
ldapadd_schema = "ldapadd -Y EXTERNAL -H ldapi:// -f %s"
ldapadd_user = "ldapadd -x -D 'cn=Manager,"+dc+"' "+" -w "+root_pw+" -f %s"
ldapadd_group = "ldapadd -x -D 'cn=Manager,"+dc+"' "+" -w "+root_pw+" -f %s"
ldapsearch_cmd = "ldapsearch -x -D 'cn=Manager,"+dc+"' "+" -b "+dc+" -w "+root_pw


# Definations start here

# Check OS 
def check_os():
    (os,version,release) = platform.linux_distribution()
    if 'Red Hat' in os and math.floor(float(version)) == 7.0:
        print("\033[1;41m OS is %s %s \033[1;m"%(os,version))
    else:
        print("\033[1;41m OS is %s %f, We need Red Hat 7, exiting... \033[1;m"%(os,float(version)))
        sys.exit()

# Install Package
def install_func(package):
    print("\n\033[1;41m Installing %s\033[1;m"%package)
    os.system("yum install -y %s" %(package))

# Check if file exists
def check_exists(file):
    if os.path.isfile(file):
        return "True"
    else:
        return "False"

# Replace stext with rtext in a file
def replace_text_func(filename,stext,rtext):
    with open(filename) as f:
        newfile = f.read().replace(stext,rtext)
    with open(filename, "w") as f:
        f.write(newfile)

# Add configuration parameters in a file
def set_parameter(filename,parameter,value):
    attribute = parameter+": "+value
    if not attribute in open(filename).read():
        file = open(filename, "a")
        file.write(attribute + "\n")
        file.close()

# Check for yes / no
def yesno(question):
    while "the answer is invalid":
        reply = str(raw_input(question+' (y/n): ')).lower().strip()
        if len(reply) != 1:
            continue     
        if reply[0] == 'y':
            return "True"
        if reply[0] == 'n':
            return "False"

# Service operations; other service operations can be added as required
def service_ops(service,operation):
    if operation == "status":
        os.system("systemctl %s %s"%(operation,service))
    elif operation == "start":
        os.system("systemctl %s %s"%(operation,service))
    elif operation == "stop":
        os.system("systemctl %s %s"%(operation,service))
    elif operation == "enable":
        os.system("systemctl %s %s"%(operation,service))
    else:
        print("\033[1;41m Unknown service operation ... \033[1;m \n")

# Add ldap users to system 
def add_sys_users(user_add_file):
    os.system("cat %s | grep '^uid' | cut -d' ' -f2 > /tmp/user" %user_add_file)
    num=0
    user_name=[]
    user_id=[]
    f = open("/tmp/user")
    line = f.readline()
    while line:
        user_name.append(str(line).strip('\n'))
        line=f.readline()
        user_id.append(int((str(line).strip('\n'))))
        line=f.readline()
    f.close()
    while num < len(user_id):
        print("Creating user %s ...\n"%user_name[num])
        os.system("useradd -u %d %s"%(user_id[num],user_name[num]))
        num=num+1

# Execute ldap commands 
def execute_ldap_cmd(cmd,file):
    if check_exists(file):
        print("\n\n\033[1;41m Importing file %s ...\033[1;m\n\n"%file)
        os.system(cmd %file)
        os.system("sleep 2")
    else:
        print("\n\033[1;41m File %s doesn't exists \033[1;m"%file)


### Main code starts here 

# Check OS
check_os()

# Install LDAP server packages
install_func(server_packages)

# Set the required DC
replace_text_func(hdb_config_file,"dc=my-domain,dc=com",dc)

# Set root password
set_parameter(hdb_config_file,"olcRootPW",root_pw)

# Set the admin user and password for config database
set_parameter(db_config,"olcRootDN","cn=config")
set_parameter(db_config,"olcRootPW",root_pw)

# Use slaptest command to verify the configuration file
print("\n\n\033[1;41m 'slaptest -u' command output is as below : \033[1;m\n")
os.system("slaptest -u")

# Start/Enable slapd service if 'slaptest -u' output looks good else exit
answer = yesno("\n\n\033[1;41m Does it looks good ? \033[1;m")
if (answer == 'True'):
    print("\n\n\033[1;41m Configuration successful, starting and enabling %s service ..... \033[1;m \n\n" %ldap_service)
    service_ops(ldap_service,"start")
    service_ops(ldap_service,"enable")
    service_ops(ldap_service,"status")
    os.system("sleep 2")
else:
    print("\n\033[1;41m Exiting ... !\033[1;m \n")
    sys.exit()

# Import the base structure in to the LDAP directory 
execute_ldap_cmd(ldapadd_base_cmd,base_struct_file)

# Import schemas to avoid "Oject class not defined" errors
execute_ldap_cmd(ldapadd_schema,schema_cosine)
execute_ldap_cmd(ldapadd_schema,schema_nis)
execute_ldap_cmd(ldapadd_schema,schema_inetorgperson)

# Create user(s) and group(s) to the system and to the LDAP
print("\033[1;41m Creating the users/groups on the system and adding them to LDAP as per %s and %s respectively ...\033[1;m" %(user_add_file,group_add_file))

answer = yesno("\033[1;41m Do you want to continue ? \033[1;m")

if (answer == "True"): 
    add_sys_users(user_add_file)
    execute_ldap_cmd(ldapadd_user,user_add_file)
    execute_ldap_cmd(ldapadd_group,group_add_file)
else:
    print("\n\n\033[1;41m Users/Groups not added ...\033[1;m")

# ldapsearch output 
print("\n\033[1;41m LDAP structure with Users/Groups :\033[1;m")
os.system(ldapsearch_cmd)
