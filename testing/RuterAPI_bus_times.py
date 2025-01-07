import requests
from datetime import datetime
import time
from azure.storage.blob import BlobServiceClient
import json
import os
from dotenv import load_dotenv
load_dotenv()


key = os.getenv('key')

credential = key
service = BlobServiceClient(account_url="https://erlingsdatabase.blob.core.windows.net/", credential=credential)
container = 'bustimescontainer'

container_client = service.get_container_client(container)


real_time_url = "https://api.entur.io/journey-planner/v3/graphql"

# GraphQL query 
query = """
{
  trip(
    from: {
      place: "NSR:StopPlace:5620",
      name: "Furuset skole, Oslo"
    },
    to: {
      place: "NSR:StopPlace:59516",
      name: "Helsfyr, Oslo"
    },
    numTripPatterns: 4
  ) {
    tripPatterns {
      startTime
      duration
      walkDistance
      legs {
        mode
        distance
        line {
          id
          publicCode
          authority {
            name
          }
        }
        fromEstimatedCall {
          quay {
            id
            name
          }
          realtime
          aimedDepartureTime
          expectedDepartureTime
          actualDepartureTime
        }
        toEstimatedCall {
          quay {
            id
            name
          }
          aimedDepartureTime
          expectedDepartureTime
          actualDepartureTime
        }
        intermediateEstimatedCalls {
          aimedArrivalTime
          expectedArrivalTime
          actualArrivalTime
          aimedDepartureTime
          expectedDepartureTime
          actualDepartureTime
          quay {
            id
            name
          }
        }
      }
    }
  }
}
"""
headers = {
    "Content-Type": "application/json",
    'ET-Client-Name': 'Erling-Project'
}


def get_data():
  response = requests.post(real_time_url, json={"query": query}, headers=headers)

  if response.status_code == 200:
        
    data = response.json()  # Parse the JSON response
  else:
    print(f"Error: {response.status_code}")
    print(response.text)
  
  return data

bus_times = []
bus_names = {'100': '100 Oslo Bussterminal',
              '110': '110 Oslo Bussterminal',
              '300': '300 Blystadlia',
              '2N' : '2N'}


while True:
    data = get_data()
    bus_times.clear()

    for tripPattern in data['data']['trip']['tripPatterns']:
        for leg in tripPattern['legs']:
            
            line = leg['line']['publicCode']
            
            real_time_departure = leg['fromEstimatedCall']['expectedDepartureTime']
            parsed_time = datetime.fromisoformat(real_time_departure)
            formatted_time = parsed_time.strftime("%H:%M:%S")
            bus_times.append(bus_names[line] + ' ' + formatted_time)
            #bus_times.append(formatted_time)
    
    
    

    






    """json_data = json.dumps(bus_times, indent=4)  # Convert to JSON format with pretty print

    blob_name = "bus_times.json"  
    blob_client = container_client.get_blob_client(blob_name)
    
    blob_client.upload_blob(json_data, overwrite=True)"""

    time.sleep(60)






  