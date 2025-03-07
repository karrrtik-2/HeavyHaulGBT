from dotenv import load_dotenv
import os
from groq import Groq
from pymongo import MongoClient
from other_func import *
from predef_list import states, route_data_keys, months
from datetime import datetime, timedelta

load_dotenv()
mongo_uri = os.getenv("MONGO_URI")
mongo_client = MongoClient(mongo_uri)
groq_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_key)
db = mongo_client["HeavyHaulDB"]
orders_collection = db["New Orders"]
users_collection = db["All Users"]

def restructure_results(results):
    #print(f"here is before restrcuture results:{results}")
    # Convert to string to easily find and remove empty dictionaries
    results_str = str(results)
    results_str = results_str.replace(" {},", "")
    # Convert back to Python object
    results = eval(results_str)
    restructured_results = []

    for result in results:
        restructured_result = {"order_id": result["order_id"]}  
        route_data = []

        if any(key in result for key in route_data_keys):
            list_length = len(next((result[key] for key in route_data_keys if key in result), []))

            for i in range(list_length):
                state_data = {}
                # Ensure state_name comes first
                if "state_name" in result and i < len(result["state_name"]):
                    state_data["state_name"] = result["state_name"][i]
                # Add other keys
                for key in route_data_keys:
                    if key != "state_name" and key in result and i < len(result[key]):
                        state_data[key] = result[key][i]
                route_data.append(state_data)

            # Add the routeData list to the result if it's not empty
            if route_data:
                restructured_result["routeData"] = route_data

        # Process non-routeData keys
        for key, value in result.items():
            if key not in route_data_keys and key != "order_id":
                restructured_result[key] = value

        restructured_results.append(restructured_result)

    return restructured_results

def filter_results_by_date(results, intent_results):
    if not results:
        return results

    today = datetime.today()
    past_months = intent_results.get("Past months")
    month_name = intent_results.get("Month name")

    # If no date-related information in intent, return results as they are
    if not past_months and not month_name:
        return results

    if past_months:
        try:
            # Convert past_months to integer and calculate the date range
            months_back = int(past_months)
            # Calculate start date by going back the specified number of months
            start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=30 * (months_back - 1))
            # End date will be today
            end_date = today
        except (ValueError, TypeError):
            print(f"Invalid past months value: {past_months}")
            return results
    elif month_name:
        # Handle specific month filtering
        try:
            month_index = months.index(month_name.lower()) + 1
            current_year = today.year
            current_month = today.month

            # If the target month is in the future for this year, use previous year
            if month_index > current_month:
                start_date = datetime(current_year - 1, month_index, 1)
                end_date = (datetime(current_year - 1, month_index + 1, 1) if month_index < 12 
                           else datetime(current_year, 1, 1)) - timedelta(days=1)
            else:
                start_date = datetime(current_year, month_index, 1)
                end_date = (datetime(current_year, month_index + 1, 1) if month_index < 12 
                           else datetime(current_year + 1, 1, 1)) - timedelta(days=1)
        except ValueError:
            print(f"Invalid month name: {month_name}")
            return results

    # Print the date range for debugging
    print(f"Filtering orders between: {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')}")

    # Filter results based on order_created_date
    filtered_results = []
    for result in results:
        if "order_created_date" in result:
            order_date_str = result["order_created_date"]
            try:
                order_date = datetime.strptime(order_date_str, "%Y-%m-%d %H:%M:%S")
                if start_date <= order_date <= end_date:
                    filtered_results.append(result)
            except ValueError:
                print(f"Skipping invalid date format: {order_date_str}")
                continue

    return filtered_results

def append_order_status_counts(filtered_results):
    if not filtered_results:
        return filtered_results
        
    counts = {}
    # First check for order_status
    if filtered_results and "order_status" in filtered_results[0]:
        total_open_orders = 0
        total_closed_orders = 0
        
        for order in filtered_results:
            if "order_status" in order:
                if order["order_status"].lower() == "open":
                    total_open_orders += 1
                elif order["order_status"].lower() in ["closed", "completed"]:
                    total_closed_orders += 1
                    
        if total_open_orders > 0:
            counts["total_open_orders"] = total_open_orders
        if total_closed_orders > 0:
            counts["total_closed_orders"] = total_closed_orders
    
    # Only check for order_id if order_status was not present
    elif filtered_results and 'order_id' in filtered_results[0]:
        total_orders = len([order for order in filtered_results if 'order_id' in order])
        if total_orders > 1:  # Only add if more than one order exists
            counts["if asked count or how many then answer"] = total_orders

    # Insert the counts dictionary at the top of the results if any counts exist
    if counts:
        filtered_results.insert(0, counts)

    return filtered_results

def filter_by_last_time(results, intent_results):
    if not results:
        return results
        
    last_time = intent_results.get("Last time/Recently")
    
    if last_time != "YES":
        return results
        
    actual_results = results
    if results and isinstance(results[0], dict) and any(key.startswith('total_') for key in results[0].keys()):
        actual_results = results[1:]
        
    if not actual_results:
        return results
        
    largest_order = max(actual_results, key=lambda x: int(x.get('order_id', 0)))
    
    if len(results) > len(actual_results):
        return [results[0], largest_order]
    
    return [largest_order]

def filter_by_key_value(filtered_results, key_with_value):
    if not key_with_value:
        return filtered_results
        
    def convert_to_feet(value_dict):
        if isinstance(value_dict, dict) and 'feet' in value_dict and 'inch' in value_dict:
            feet = float(value_dict['feet'])
            inches = float(value_dict['inch'])
            return feet + (inches / 12)
        return float(value_dict)
        
    def compare_values(actual_value, comparison_value):
        try:
            # Special handling for state_name
            if isinstance(actual_value, str) and isinstance(comparison_value, str):
                return actual_value.lower() == comparison_value.lower()

            # Convert actual value to feet if it's a dimension
            if isinstance(actual_value, dict):
                actual_feet = convert_to_feet(actual_value)
            else:
                actual_feet = float(actual_value)
            
            # Extract operator and value
            operator = '='
            for op in ['>=', '<=', '>', '<', '=']:
                if comparison_value.startswith(op):
                    operator = op
                    value = float(comparison_value.replace(op, '').strip())
                    break
            else:
                value = float(comparison_value.strip())
            
            # Perform comparison based on operator
            if operator == '>':
                return actual_feet > value
            elif operator == '<':
                return actual_feet < value
            elif operator == '>=':
                return actual_feet >= value
            elif operator == '<=':
                return actual_feet <= value
            else:  # operator == '='
                return actual_feet == value
                
        except (ValueError, TypeError):
            # If values can't be converted to float, do string comparison
            return str(actual_value).lower() == str(comparison_value.strip('><=').strip()).lower()
    
    filtered_data = []
    for result in filtered_results:
        match = True
        for key, comparison_value in key_with_value.items():
            # Handle dimension keys
            dimension_keys = ['overallwidth/wide', 'overallheight/tall', 'overalllength/long']
            
            if key == 'state_name':
                if 'routeData' in result:
                    state_match = False
                    for route in result['routeData']:
                        if 'state_name' in route and compare_values(route['state_name'].split(' - ')[0], comparison_value):
                            state_match = True
                            break
                    if not state_match:
                        match = False
                        break
            elif key in result:
                if not compare_values(result[key], comparison_value):
                    match = False
                    break
            elif 'routeData' in result and any(key in route for route in result['routeData']):
                route_match = False
                for route in result['routeData']:
                    if key in route and compare_values(route[key], comparison_value):
                        route_match = True
                        break
                if not route_match:
                    match = False
                    break
            else:
                match = False
                break
        
        if match:
            filtered_data.append(result)
            
    return filtered_data

def filter_results_by_state(results, user_input):
    #print(f"here are the results before state filter:{results}")
    user_input_lower = user_input.lower()

    target_states = [state for state in states if state in user_input_lower]

    if not target_states:
        return results

    states_in_results = set()
    for result in results:
        if "routeData" in result:
            for state_data in result["routeData"]:
                state_name = state_data.get("state_name", "").split(" - ")[0].lower()
                if state_name in target_states:
                    states_in_results.add(state_name)

    if not states_in_results:
        return results

    # Filter results to include only the target states
    filtered_results = []
    for result in results:
        if "routeData" in result:
            filtered_route_data = [
                state_data for state_data in result["routeData"]
                if state_data.get("state_name", "").split(" - ")[0].lower() in target_states
            ]
            if filtered_route_data:
                # Create a new result dictionary with filtered routeData
                filtered_result = {
                    "order_id": result["order_id"],
                    "routeData": filtered_route_data
                }
                # Include other non-routeData keys if they exist
                for key, value in result.items():
                    if key not in ["order_id", "routeData"]:
                        filtered_result[key] = value
                filtered_results.append(filtered_result)

    #print(f"here are the final results: {filtered_results}")
    return filtered_results

def filter_by_order_status(results, intent_results):
    if not results:
        return results

    open_order = intent_results.get("Open/Active/Live order")
    closed_order = intent_results.get("Closed/Completed order")

    # If neither status is specified in intent, return results as they are
    if open_order != "YES" and closed_order != "YES":
        return results

    # Filter results based on order_status
    filtered_results = []
    for result in results:
        # If order_status is not present, include the result
        if "order_status" not in result:
            filtered_results.append(result)
        else:
            order_status = result["order_status"].lower()
            if (open_order == "YES" and order_status == "open") or \
               (closed_order == "YES" and order_status in ["closed", "completed"]):
                filtered_results.append(result)

    return filtered_results