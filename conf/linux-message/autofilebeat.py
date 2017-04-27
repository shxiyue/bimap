import yaml

f= open('filebeat.yml')

fb = yaml.load(f)

path = {'input_type': 'log', 'document_type': 'message', 'paths': ['/var/log/messages']}

fb['filebeat.prospectors'].append(path)
print fb

ww = open('abc.yml','w')
print yaml.dump(fb,ww,default_flow_style = False,)
f.close()
ww.close()
