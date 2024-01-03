import os
import re
import xml.etree.ElementTree as ET

# dir_path = './'

# # list to store files
# res = []

# # Iterate directory
# for path in os.listdir(dir_path):
#     # check if current path is a file
#     if os.path.isfile(os.path.join(dir_path, path)):
#         res.append(path)
# print(res)

def get_precondition(query):
    precon = '<preConditions  onFail="MARK_RAN">\n\t\t\t<sqlCheck  expectedResult="0">'+query+'</sqlCheck>\n\t\t</preConditions>'
    return precon

def add_controller(obj_type,obj_name):
    if os.path.exists('./'+obj_type+'/controller.xml'):
        with open(obj_type+'/controller.xml',"r+") as file:
            filedata = file.read()
            if '"'+obj_name+'.xml"' not in filedata:
                file.close()
                with open(obj_type+'/controller.xml',"r") as file2:
                    filedata2 = file2.readlines()
                    if filedata2 is None:
                        file2.write('\t<include relativeToChangelogFile="true" file="'+obj_name+'.xml" />\n') 
                        file2.close()
                    else:
                        output = []
                        for line in filedata2:
                            if '</databaseChangeLog>' in line:
                                output.append('\t<include relativeToChangelogFile="true" file="'+obj_name+'.xml" />\n')
                            output.append(line)
                        file2.close()
                        with open(obj_type+'/controller.xml',"w") as file2:
                                file2.writelines(output)
    else:
        with open(obj_type+'/controller.xml',"w") as file:
            file.write('\t<include relativeToChangelogFile="true" file="'+obj_name+'.xml" />\n')
            file.close()

def preparefile(file_path,schema,author):
    if file_path == 'data.xml':
        changeLog = ET.parse(file_path)
        root = changeLog.getroot()
        changeset = root[0]
        obj_name=''
        for idx, x in enumerate(changeset):
            new_changeset = ET.Element('changeSet')
            new_changeset.set('author','VAI')
            idx_str = str(idx+1)
            obj_name=x.get('tableName').lower()
            new_changeset.set('id',x.get('tableName').lower()+'-'+idx_str)
            precon = ET.SubElement(new_changeset,'preConditions')
            precon.set('onFail','MARK_RAN')
            sqlcheck = ET.SubElement(precon,'sqlCheck')
            sqlcheck.set('expectedResult','0')
            prop_name = ''
            service_name = ''
            provider_name = ''
            for child in x:
                if child.attrib['name'] in ('CATEGORY_ID','CRT_TS','CRT_BY','UPD_TS','UPD_BY'):
                    x.remove(child)
                if child.attrib['name'] == 'KEY':
                    prop_name = 'and KEY=\''+child.get('value')+'\' ' if child.get('value') is not None else ''
                # if child.attrib['name'] == 'SERVICE':
                #     service_name = 'and SERVICE=\''+child.get('value')+'\' ' if child.get('value') is not None else ''
                # if child.attrib['name'] == 'PROVIDER':
                #     provider_name = 'and PROVIDER=\''+child.get('value')+'\' ' if child.get('value') is not None else ''
            sqlcheck.text = 'select count(*) from '+x.get('tableName')+' where 1=1 '+prop_name+service_name+provider_name
            new_changeset.append(x)
            root.append(new_changeset)
        root.remove(changeset)
        changeLog.write('temp.xml')    
        with open('temp.xml',"r") as file:
            filedata = file.read()

            filedata_new = re.sub('(\s)+</changeSet>','\n\t</changeSet>',filedata)
            filedata_new = re.sub('<preConditions','\n\t\t<preConditions',filedata_new)
            filedata_new = re.sub('<sqlCheck','\n\t\t\t<sqlCheck',filedata_new)
            filedata_new = re.sub('</preConditions>','\n\t\t</preConditions>',filedata_new)
            filedata_new = re.sub('<ns0:insert','\n\t\t<ns0:insert',filedata_new)
            filedata_new = re.sub('><changeSet','>\n\t<changeSet',filedata_new)
            filedata_new = re.sub('ns0:','',filedata_new)
            obj_type='seed'
            if not os.path.exists(obj_type):
                os.mkdir(obj_type)
            new_file = open(obj_type+'/'+obj_name+'.xml','w')
            new_file.write('<?xml version="1.1" encoding="UTF-8" standalone="no"?>\n')
            new_file.write(filedata_new)
            new_file.close()
            file.close()
            add_controller(obj_type,obj_name)
        os.remove('data.xml')    
        os.remove('temp.xml')   
            
    elif file_path != 'controller.xml':
        split_name = file_path.split('_')
        obj_type = ''
        for idx, name in enumerate(split_name):
            if '.xml' in name:
                obj_type = name.split('.')[0]
                if obj_type in ('body','spec'):
                    if split_name[idx-1] == 'type':
                        obj_type = 'type_'+obj_type
                    else:
                        obj_type = 'package_'+obj_type

        obj_name = file_path.split('_'+obj_type)[0]
        if obj_type == 'constraint':
            if 'ref_constraint' in file_path:
                obj_type = 'ref_constraint'
                obj_name = re.sub('_ref','',obj_name)
        with open(file_path,"r") as file:
            filedata = file.read()
            
            if 'constraint' in obj_type:
                filedata_new = re.sub('id="(\w|\d)+"','id="constraint-'+obj_name+'"',filedata)
            else:
                filedata_new = re.sub('id="(\w|\d)+"','id="'+obj_type+'-'+obj_name+'"',filedata)
            filedata_new = re.sub('author="(\w|\d|\(|\)|-)+"','author="'+author+'"',filedata_new)
            filedata_new = re.sub('ownerName="(\w|\d)+"','ownerName="'+author+'" replaceIfExists="true"',filedata_new)
            filedata_new = re.sub('"'+schema+'".','',filedata_new)
            filedata_new = re.sub('failOnError="false" ','failOnError="true" runOnChange="true" ',filedata_new)

            if obj_type == 'trigger':
                filedata_new = re.sub('ALTER TRIGGER (\w|\d|\(|\)|-|\")+ ENABLE','',filedata_new)
            if obj_type == 'table' or obj_type=='index' or obj_type=='view' or obj_type=='sequence':
                filedata_new = re.sub('(\s)+<SCHEMA>'+schema+'</SCHEMA>','',filedata_new)
                filedata_new = re.sub('(\s)+<START_WITH>(\d+)</START_WITH>','',filedata_new)
                filedata_new = re.sub('(\s)+<TABLESPACE>(\w+)</TABLESPACE>','',filedata_new)
            if obj_type == 'table':
                filedata_new = re.sub('<n0:createSxmlObject',get_precondition('select count(*) from user_tables where table_name = upper(\''+obj_name+'\');')+'\n\t\t<n0:createSxmlObject',filedata_new)
            if obj_type == 'constraint':
                filedata_new = re.sub('<n0:createOracleConstraint',get_precondition('select count(*) from user_cons_columns where upper(constraint_name)=upper(\''+obj_name+'\');')+'\n\t\t<n0:createOracleConstraint',filedata_new)
            if obj_type == 'ref_constraint':
                filedata_new = re.sub('<n0:createOracleRefConstraint',get_precondition('select count(*) from user_cons_columns where upper(constraint_name)=upper(\''+obj_name+'\');')+'\n\t\t<n0:createOracleRefConstraint',filedata_new)
                obj_type = 'constraint'
            if obj_type == 'index':
                filedata_new = re.sub('<n0:createSxmlObject',get_precondition('SELECT COUNT(*) FROM user_indexes WHERE upper(index_name) = upper(\''+obj_name+'\');')+'\n\t\t<n0:createSxmlObject',filedata_new)
            if obj_type == 'sequence':
                filedata_new = re.sub('<n0:createSxmlObject',get_precondition('SELECT COUNT(*) FROM user_sequences WHERE upper(sequence_name) = upper(\''+obj_name+'\');')+'\n\t\t<n0:createSxmlObject',filedata_new)
            
            if not os.path.exists(obj_type):
                os.mkdir(obj_type)
            new_file = open(obj_type+'/'+obj_name+'.xml','w')
            new_file.write(filedata_new)
            new_file.close()
            file.close()
            add_controller(obj_type,obj_name)
        os.remove(file_path)


def iterate_files(files_path,from_schema,to_schema):
    for path in os.listdir(files_path):
        #check if current path is a file
        if os.path.isfile(os.path.join(files_path, path)) and '.xml' in path:
            preparefile(path,from_schema,to_schema)


def console_menu():
    print('=====================================================',)
    print('.')
    print('.          VISCOSITY LB CLASSIFICATION TOOL          ',)
    print('.')
    print('=====================================================',)
    print('FROM_SCHEMA: ', end='' )
    schema = input()
    print('TO_SCHEMA: ', end='' )
    to_schema = input()
    schema      = 'SCHEMA' if schema is None else schema
    to_schema   = 'VAI' if to_schema is None else to_schema
    iterate_files('./',schema,to_schema)

console_menu()
#iterate_files('./')
