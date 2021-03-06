import extruct
import requests
import pprint
from w3lib.html import get_base_url

from woqlclient import WOQLClient, WOQLQuery
from dateutil.parser import *

# settings for WOQLClient
server_url = "http://localhost:6363"
key = "root"
dbId = "schema_tutorial"

# Script tags and pretty print
pp = pprint.PrettyPrinter(indent=2)
r = requests.get("https://events.terminusdb.com/london/2020/02/11/london-1st-graph.html")
base_url = get_base_url(r.text, r.url)
data = extruct.extract(r.text, base_url, syntaxes=['microdata'])

pp.pprint(data)

execution_queue=[] #this stores all woql queries before passing to client for update

def extract_data(data, id='event/'):
    """Recursive function to craw through the data and create WOQLQuery objects"""

    if type(data) == dict:
        data_type = data['type']
        WOQLObj = WOQLQuery().insert('doc:'+id, data_type)
        if data_type == 'http://schema.org/DateTime':
            date_value = {"@value" : data['value'], "@type" : "xsd:dateTime"}
            execution_queue.append(WOQLObj.property(data_type+'Value', date_value))
            return
        for prop in data['properties']:
            extract_data(data['properties'][prop], id+prop+'/')
            WOQLObj = WOQLObj.property('http://schema.org/'+prop, 'doc:'+id+prop+'/')
        execution_queue.append(WOQLObj)
    else:
        if '://' in data:
            data_type = 'http://schema.org/URL'
        else:
            data_type = 'http://schema.org/Text'
        WOQLObj = WOQLQuery().insert('doc:'+id, data_type)
        data_obj = {"@value" : data, "@type" : "xsd:string"}
        execution_queue.append(WOQLObj.property(data_type+'Value',data_obj))

extract_data(data['microdata'][0])

client = WOQLClient()
client.connect(server_url, key)
client.update(WOQLQuery().when(True).woql_and(*execution_queue).json(), dbId)
