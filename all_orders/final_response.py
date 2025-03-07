from groq import Groq
import os
from dotenv import load_dotenv
import json
from pymongo import MongoClient
import ast

load_dotenv()
mongo_uri = os.getenv("MONGO_URI")
mongo_client = MongoClient(mongo_uri)
groq_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_key)
db = mongo_client["HeavyHaulDB"]
orders_collection = db["New Orders"]
states_collection = db["All States"]

def save_conversation(user_message, assistant_message):
    conversation = {
        "user": {
            "role": "user",
            "content": user_message
        },
        "assistant": {
            "role": "assistant",
            "content": assistant_message
        }
    }
    with open("123786.txt", "a") as file:
        file.write(json.dumps(conversation, indent=2) + "\n\n")

def replace_order_ids_with_tokens(data_results):
    if isinstance(data_results, str):
        try:
            data_results = ast.literal_eval(data_results)
        except Exception:
            return data_results

    if isinstance(data_results, dict):
        if 'order_id' in data_results:
            order = orders_collection.find_one({'id': data_results['order_id']})
            if order and 'token' in order:
                data_results['order_id'] = order['token']
        for key, value in data_results.items():
            if isinstance(value, (dict, list)):
                replace_order_ids_with_tokens(value)
    elif isinstance(data_results, list):
        for item in data_results:
            if isinstance(item, dict) and 'order_id' in item:
                order = orders_collection.find_one({'id': item['order_id']})
                if order and 'token' in order:
                    item['order_id'] = order['token']
            elif isinstance(item, (dict, list)):
                replace_order_ids_with_tokens(item)
    
    return data_results

def fetch_order_data(order_id):
    try:
        query = {"id": order_id}
        result = orders_collection.find_one(query)
        print(f"here is the result from oreder: {result}")
        if result:
            overall_order_data = result.get("order", {}).get("OverallOrderData", {})
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

def generate_response(user_query, data_results, has_permit_info=False, state_name=None, permit_info=None, current_order_id=None, order_position=None):
    data_results = replace_order_ids_with_tokens(data_results)
    print(f"here is the order id current:{current_order_id}")
    
    if has_permit_info and state_name and permit_info:
        order_dimensions = None
        if current_order_id:
            order_dimensions = fetch_order_data(current_order_id)
            if order_dimensions is None:
                return "Could not fetch order dimensions."
        system_message = (
            'NOTE: Provide concise and direct responses based on the permit information. If the permit_info does not mention any information related to the query, respond with "NO" and specify which field the query is related to from the following: state_name, speed_limit, operating_time, restricted_travel, escorts, signs_flags_lights, miscellaneous, state_info, night_travel, permit_limits, superloads.\n'
            f"Here is the permit information for {state_name}: {permit_info}"
        )
                                
        formatted_query = f"My dimensions: {order_dimensions}\n\n {user_query} (after checking my dimensions) (respond in 1 sentence and dont give unnecessary info or checks)"
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": formatted_query}
        ]
        
        print("Messages sent to LLM:", json.dumps(messages, ensure_ascii=False))
         
        stream = groq_client.chat.completions.create(
            model="llama-3.3-70b-specdec",
            messages=messages,
            temperature=0.0,
            top_p=1,
            max_tokens=1024,
            stream=True
        )
        
        response_text = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                response_text += chunk.choices[0].delta.content
        
        print(f"here is the response from 1 LLM: {response_text} \n")
        if "NO" in response_text:
            state_doc = states_collection.find_one({"state_name": state_name})
            if state_doc and 'info' in state_doc:
                info = state_doc['info']
                relevant_info = {
                    'state_name': state_name,
                    'speed_limit': info.get('speed_limit'),
                    'operating_time': info.get('operating_time'),
                    'restricted_travel': info.get('restricted_travel'),
                    'escorts': info.get('escorts'),
                    'signs_flags_lights': info.get('signs_flags_lights'),
                    'miscellaneous': info.get('miscellaneous'),
                    'state_info': info.get('state_info'),
                    'night_travel': info.get('night_traver'),
                    'permit_limits': info.get('permit_limits'),
                    'superloads': info.get('superloads')
                }

                fields_to_search = [
                    'state_name', 'speed_limit', 'operating_time', 'restricted_travel',
                    'escorts', 'signs_flags_lights', 'miscellaneous', 'state_info',
                    'night_travel', 'permit_limits', 'superloads'
                ]

                found_fields = [
                    field for field in fields_to_search
                    if field.lower() in response_text.lower()
                ]
                if found_fields:
                    filtered_info = {
                        key: value for key, value in relevant_info.items()
                        if key in found_fields and value is not None
                    }
                else:
                    filtered_info = relevant_info

                new_system_message = (
                    f'Based on the following state regulations. Respond like you are talking to me and \n'
                    f'here is State information for {state_name}: {json.dumps(filtered_info)}\n\n'
                    f'My dimensions: {order_dimensions}\n'
                    f'{user_query} (respond in 1 sentence and don’t give unnecessary info or checks)'
                )

                new_messages = [
                    {"role": "system", "content": new_system_message},
                    {"role": "user", "content": ""}  # Empty user input
                ]

                print("New state Messages sent to LLM:", json.dumps(new_messages, ensure_ascii=False))

                new_stream = groq_client.chat.completions.create(
                    model="llama-3.3-70b-specdec",
                    messages=new_messages,
                    temperature=0.0,
                    top_p=1,
                    max_tokens=1024,
                    stream=True
                )

                
                new_response_text = ""
                for chunk in new_stream:
                    if chunk.choices[0].delta.content is not None:
                        new_response_text += chunk.choices[0].delta.content
                save_conversation(formatted_query, new_response_text)
                return new_response_text
            
        save_conversation(formatted_query, response_text)
        return response_text
        
    else:
        print("i am using llama3.3 70B\n")
        system_message = """You are a helpful assistant for a transportation company. 
            Your task is to analyze the provided filtered order data and respond to user queries in a natural, conversational way like you're talking.
            - Give short answers about the order(s) you can see in the data. Don't provide any extra analysis/context from your side.
            - Respond directly to the user's question without mentioning data structure"""
        
        
        user_message = f"{user_query}\nOrder Data: {data_results}"
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        with open("123.txt","a") as logfile:
            logfile.write(f"Data fed to LLM: {messages}")
            logfile.write(json.dumps(messages, indent=2))
            logfile.write("\n\n")
        
        print("Messages sent to LLM:", json.dumps(messages, ensure_ascii=False))
        
        stream = groq_client.chat.completions.create(
            model="qwen-2.5-32b",
            messages=messages,
            temperature=0.0,
            top_p=1,
            max_tokens=300,
            stream=True
        )

        response = ""
        for chunk in stream:
            response += chunk.choices[0].delta.content or ""

        save_conversation(user_message, response)
        return response
    
    