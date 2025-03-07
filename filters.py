import requests
from datetime import datetime
import os
from dotenv import load_dotenv
import os
from groq import Groq
from pymongo import MongoClient
from other_func import *  
from predef_list import *
import requests
from datetime import datetime
from filters import *

# Load environment variables
load_dotenv()
mongo_uri = os.getenv("MONGO_URI")
mongo_client = MongoClient(mongo_uri)
groq_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_key)
db = mongo_client["HeavyHaulDB"]
orders_collection = db["New Orders"]

def download_document(url, doc_type, order_id):
    if not url:
        return f"No {doc_type} URL available"
    
    # Create docs directory if it doesn't exist
    docs_dir = "docs"
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Get file extension from URL or default to .pdf
        file_extension = os.path.splitext(url)[1] or '.pdf'
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{order_id}_{doc_type}_{timestamp}{file_extension}"
        filepath = os.path.join(docs_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return f"{doc_type} document downloaded successfully"
    except Exception as e:
        return f"Error downloading {doc_type}: {str(e)}"
    

def restructure_single_result(fetched_data, order_id):
    restructured_result = {"order_id": order_id}
    route_data = []
    list_length = 0
    
    # Get the maximum length of any list in fetched_data
    for key in route_data_keys:
        if key in fetched_data and isinstance(fetched_data[key], list):
            list_length = max(list_length, len(fetched_data[key]))
    
    # Build route_data array
    for i in range(list_length):
        state_data = {}
        if "state_name" in fetched_data and isinstance(fetched_data["state_name"], list) and i < len(fetched_data["state_name"]):
            state_data["state_name"] = fetched_data["state_name"][i]
        for key in route_data_keys:
            if key != "state_name" and key in fetched_data and isinstance(fetched_data[key], list) and i < len(fetched_data[key]):
                state_data[key] = fetched_data[key][i]
        if state_data:
            route_data.append(state_data)
    
    if route_data:
        restructured_result["routeData"] = route_data
    
    # Add remaining non-route data
    for key, value in fetched_data.items():
        if key not in route_data_keys and key != "order_id":
            restructured_result[key] = value
            
    return restructured_result

def filter_by_state(restructured_data, state_name):
    if 'routeData' not in restructured_data:
        print(f"[STATE FILTER] No routeData to filter for state: {state_name}")
        return restructured_data

    filtered_route_data = []
    state_name_lower = state_name.lower()
    
    print(f"[STATE FILTER] Filtering routeData for state: {state_name}")
    for route in restructured_data['routeData']:
        if 'state_name' in route and state_name_lower in route['state_name'].lower():
            filtered_route_data.append(route)
            print(f"[STATE FILTER] Found matching state: {route['state_name']}")
    
    filtered_data = restructured_data.copy()
    if filtered_route_data:
        filtered_data['routeData'] = filtered_route_data
        print(f"[STATE FILTER] Filtered down to {len(filtered_route_data)} state entries")
    else:
        print(f"[STATE FILTER] No matching states found for {state_name}")
    
    return filtered_data

def fetch_order_data(order_document):
    try:
        if order_document:
            overall_order_data = order_document.get("order", {}).get("OverallOrderData", {})
            excluded_keys = ["orderId", "truckID", "trailerId", "overalltrucktrailer"]
            filtered_overall_order_data = {
                key: value for key, value in overall_order_data.items() if key not in excluded_keys
            }
            
            renamed_data = {}
            for key, value in filtered_overall_order_data.items():
                if key.lower() == "overalllength":
                    renamed_data["length"] = value
                elif key.lower() == "overallwidth":
                    renamed_data["width"] = value
                elif key.lower() == "overallheight":
                    renamed_data["height"] = value
                elif key.lower() == "overallweight":
                    renamed_data["weight"] = value
                else:
                    renamed_data[key] = value

            return renamed_data
        else:
            return None

    except Exception as e:
        return None