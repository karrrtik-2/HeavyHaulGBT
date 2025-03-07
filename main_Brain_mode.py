from dotenv import load_dotenv
import os
from groq import Groq
from pymongo import MongoClient
import json
from other_func import *  
from predef_list import *
import asyncio
from speak import ContinuousListener, SpeechSynthesizer, delete_stream_audio_files
from filters import *

load_dotenv()
mongo_uri = os.getenv("MONGO_URI")
mongo_client = MongoClient(mongo_uri)
groq_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_key)
db = mongo_client["HeavyHaulDB"]
orders_collection = db["New Orders"]

State_value = None
global_state_value = None

with open("123.txt", "w") as file:
    file.write("Conversation Log\n\n")

with open("queryType_prpt.txt", "r") as file:
    sys_msg = file.read().strip()
    
user_input_history = []
MAX_HISTORY = 4
MAX_PERMIT_HISTORY = 3

def log_conversation(user_input, assistant_response):
    with open("123.txt", "a") as file:
        file.write(f"User input: {user_input}\n")
        file.write(f"Assistant: {assistant_response}\n\n")

def update_user_input_history(user_input):
    user_input_history.append(user_input)
    
    while len(user_input_history) > MAX_HISTORY:
        user_input_history.pop(0)

def get_previous_user_inputs(limit=MAX_HISTORY):
    messages = []
    
    limited_history = user_input_history[-limit:] if limit < len(user_input_history) else user_input_history.copy()
    for input_text in limited_history:
        messages.append({"role": "user", "content": input_text})
    
    return messages

def ask_llm(question):
    messages = [{"role": "system", "content": sys_msg}]
    messages.extend(get_previous_user_inputs())
    messages.append({"role": "user", "content": question})
    
    stream = groq_client.chat.completions.create(
        model="llama-3.3-70b-specdec",
        messages=messages,
        temperature=0.0,
        top_p=1,
        max_tokens=80,
        stream=True
    )
    response = ""
    for chunk in stream:
        response += chunk.choices[0].delta.content or ""
    return response

# Function to generate conversational response
def generate_final_response(user_input, restructured_data):
    data_str = json.dumps(restructured_data, indent=2)
    user_message = f"Order data:\n{data_str}\n\nUser question: {user_input}"
    
    # Prepare system message
    system_message = """
        You are a helpful voice assistant for a HeavyHaul company. 
        Your task is to analyze the provided filtered order data and respond to user queries in a natural, conversational way like you're talking.
        - Give short answers about the order you can see in the data. Don't provide any extra analysis/context from your side.
    """
    
    messages = [{"role": "system", "content": system_message}]
    messages.extend(get_previous_user_inputs())
    messages.append({"role": "user", "content": user_message})
    
    print("Messages sent to LLM:", json.dumps(messages, ensure_ascii=False))
    
    stream = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.0,
        top_p=1,
        max_tokens=200,
        stream=True
    )
    response = ""
    for chunk in stream:
        response += chunk.choices[0].delta.content or ""
    return response

def process_user_query(user_input, order_id, order_document):
    global State_value, global_state_value
    
    print("\n--- STARTING NEW QUERY ---")
    print(f"[STATE TRACKING] Before processing - State_value: {State_value}, global_state_value: {global_state_value}")
    
    update_user_input_history(user_input)
    
    user_input_lower = user_input.lower()
    state_in_input = None
    for state in states:
        if state.lower() in user_input_lower:
            state_in_input = state
            global_state_value = state
            break
    
    if state_in_input:
        print(f"[STATE TRACKING] Found state in user input: {state_in_input}, updated global_state_value")
    else:
        print("[STATE TRACKING] No state found in user input")
    
    response = ask_llm(user_input)
    if 'routeData' in response:
        response = response.replace('routeData', 'state_name')
    print(f"[LLM RESPONSE] Raw response: {response}")
    
    keys_in_response = [key.strip() for key in response.split(",")]
    print(f"[LLM RESPONSE] Parsed keys: {keys_in_response}")
    
    # Process state_name from the response
    state_name_present = False
    state_name_value = None
    
    for item in keys_in_response:
        if 'state_name' in item:
            state_name_present = True
            # Check if it has a value like 'state_name: california'
            if ':' in item:
                parts = item.split(':')
                if len(parts) >= 2 and parts[1].strip():
                    state_name_value = parts[1].strip()
    
    print(f"[STATE TRACKING] state_name in response: {state_name_present}, value: {state_name_value}")
    
    # Update State_value based on the response - UPDATED LOGIC
    previous_state_value = State_value
    if state_name_present and state_name_value:
        State_value = state_name_value
    else:
        # Reset State_value to None if state_name is not present OR has no value
        State_value = None
        
    print(f"[STATE TRACKING] Updated State_value from {previous_state_value} to {State_value}")
    
    # Process dot notation in keys
    processed_keys = []
    for key in keys_in_response:
        if '.' in key:
            parts = key.split('.')
            if parts[0] == 'routeData':
                processed_keys.append(parts[1])
        else:
            processed_keys.append(key)
    
    print(f"[KEYS] Processed keys: {processed_keys}")
    
    if (any(key in route_data_keys for key in processed_keys) or
        any(state in user_input_lower for state in states)) and "state_name" not in processed_keys:
        processed_keys.append("state_name")
        print("[KEYS] Added state_name to processed keys")
        
    if ("past months" in user_input_lower or any(month in user_input_lower for month in months)) and "order_created_date" not in processed_keys:
        processed_keys.append("order_created_date")
        print("[KEYS] Added order_created_date to processed keys")
        
    fetched_data = {}
    for key in processed_keys:
        if key in key_to_function:
            fetched_data[key] = key_to_function[key](order_document)
        else:
            pass
    
    # Determine mentioned_state according to the filtering rules
    mentioned_state = None
    has_permit_info = "permit_info" in processed_keys
    print(f"[PERMIT INFO] permit_info in response: {has_permit_info}")
    
    # Check direct state mention in input first
    if state_in_input:
        mentioned_state = state_in_input
        print(f"[STATE FILTERING] Using state from user input: {mentioned_state}")
    # If no direct mention, check State_value
    elif State_value:
        mentioned_state = State_value
        print(f"[STATE FILTERING] Using State_value: {mentioned_state}")
    # If still no state, check global_state_value but only if permit_info is requested
    elif global_state_value and has_permit_info:
        mentioned_state = global_state_value
        print(f"[STATE FILTERING] Using global_state_value with permit_info: {mentioned_state}")
    else:
        print("[STATE FILTERING] No state to filter by")
            
    restructured_data = restructure_single_result(fetched_data, order_id)
    print("[DATA] Restructured data created")

    if mentioned_state:
        print(f"[STATE FILTERING] Will filter by state: {mentioned_state}")
        restructured_data = filter_by_state(restructured_data, mentioned_state)
    else:
        print("[STATE FILTERING] No filtering applied")
    
    if 'download' in user_input_lower:
        download_messages = []
        print("[PROCESS] Download request detected")
        
        if 'registration' in restructured_data:
            result = download_document(
                restructured_data['registration'],
                'registration',
                order_id
            )
            download_messages.append(result)
            
        if 'invoice' in restructured_data:
            result = download_document(
                restructured_data['invoice'],
                'invoice',
                order_id
            )
            download_messages.append(result)
            
        if download_messages:
            response_text = "\n".join(download_messages)
            # Log the conversation
            log_conversation(user_input, response_text)
            return response_text

    # Process permit info for the specific state
    if has_permit_info and mentioned_state and 'routeData' in restructured_data:
        print(f"[PERMIT PROCESS] Processing permit info for state: {mentioned_state}")
        state_permit_info = None
        state_name = None
        
        # Find the specific state data in the route data
        for route in restructured_data['routeData']:
            if 'state_name' in route and mentioned_state.lower() in route['state_name'].lower():
                state_name = route['state_name']
                if 'permit_info' in route:
                    state_permit_info = route['permit_info']
                break
        
        # If we have both state name and permit info for that state
        if state_name and state_permit_info:
            print(f"[PERMIT PROCESS] Found permit info for state: {state_name}")
            order_dimensions = None
            if order_id:
                order_dimensions = fetch_order_data(order_document)
                if order_dimensions is None:
                    response_text = "Could not fetch order dimensions."
                    log_conversation(user_input, response_text)
                    return response_text
                            
            system_message = (
                'NOTE: Provide concise and direct responses based on the permit information. If the permit_info does not mention any information related to the query, respond with "NO" and specify which field the query is related to from the following: state_name, speed_limit, operating_time, restricted_travel, escorts, signs_flags_lights, miscellaneous, state_info, night_travel, permit_limits, superloads.\n'
                f"Here is the permit information for {state_name}: {state_permit_info}"
            )
                                    
            formatted_query = f"My dimensions: {order_dimensions}\n\n {user_input} (after checking my dimensions) (respond in 1 sentence and dont give unnecessary info or checks)"
            
            messages = [{"role": "system", "content": system_message}]
            
            # For permit_info, use only 3 previous user inputs
            messages.extend(get_previous_user_inputs(MAX_PERMIT_HISTORY))
            
            messages.append({"role": "user", "content": formatted_query})
            
            print("Messages sent to llm for permit:", json.dumps(messages, ensure_ascii=False))
             
            stream = groq_client.chat.completions.create(
                model="llama-3.3-70b-specdec",
                messages=messages,
                temperature=0.0,
                top_p=1,
                max_tokens=300,
                stream=True
            )
            
            response_text = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    response_text += chunk.choices[0].delta.content
            
            print(f"[RESPONSE] Permit response generated: {response_text}")
            log_conversation(user_input, response_text)
            return response_text
        else:
            print(f"[PERMIT PROCESS] No permit info found for state: {mentioned_state}")
    
    print("[PROCESS] Generating final conversational response")
    final_response = generate_final_response(user_input, restructured_data)
    print(f"[RESPONSE] Final response generated: {final_response}")
    
    log_conversation(user_input, final_response)
    print("--- QUERY PROCESSING COMPLETE ---\n")
    return final_response

async def voice_assistant(order_id, order_document):
    # Initialize the continuous listener and speech synthesizer
    continuous_listener = ContinuousListener()
    continuous_listener.start_stop_listener()
    speech_synthesizer = SpeechSynthesizer(continuous_listener)
    
    delete_stream_audio_files()
    
    welcome_msg = f"Voice mode activated for order ID {order_id}. Say 'pixel' followed by your question."
    await speech_synthesizer.text_to_speech(welcome_msg)
    
    log_conversation("System", welcome_msg)
    
    while True:
        query = await continuous_listener.background_listen()
        
        if query.lower() in ["exit", "quit", "bye"]:
            goodbye_msg = "Goodbye!"
            await speech_synthesizer.text_to_speech(goodbye_msg)
            log_conversation("User input", query)
            log_conversation("Assistant", goodbye_msg)
            update_user_input_history(query)
            break
        
        log_conversation("User input", query)
        
        response = process_user_query(query, order_id, order_document)
        
        await speech_synthesizer.text_to_speech(response)

def main():
    global user_input_history, State_value, global_state_value
    user_input_history = []
    State_value = None
    global_state_value = None
    
    print("Welcome to the HeavyHaul LLM Assistant!")
    print(f"[STATE TRACKING] Initialized - State_value: {State_value}, global_state_value: {global_state_value}")
    
    order_id = input("Please enter the order id: ")
    order_document = orders_collection.find_one({"token": order_id})
    
    if order_document is None:
        print("Order ID not found.")
        log_conversation("System", "Order ID not found.")
        return
    
    mode = input("Do you want to use voice mode? (yes/no): ")
    if mode.lower() in ["yes", "y"]:
        asyncio.run(voice_assistant(order_id, order_document))
    else:
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                log_conversation("User input", user_input)
                log_conversation("Assistant", "Goodbye!")
                update_user_input_history(user_input)
                break
            
            response = process_user_query(user_input, order_id, order_document)
            print(f"Assistant: {response}")

if __name__ == "__main__":
    main()