from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
from dotenv import load_dotenv
import os
from groq import Groq
from pymongo import MongoClient
import json
from other_func import *  
from predef_list import *
from filters import *
import time
import edge_tts

# Load environment variables
load_dotenv()
mongo_uri = os.getenv("MONGO_URI")
mongo_client = MongoClient(mongo_uri)
groq_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_key)
db = mongo_client["HeavyHaulDB"]
orders_collection = db["New Orders"]

# Load system prompt
with open("queryType_prpt.txt", "r", encoding="utf-8") as file:
    sys_msg = file.read().strip()

user_input_history = []
MAX_HISTORY = 4
MAX_PERMIT_HISTORY = 3

app = FastAPI(title="HeavyHaul Chatbot API", description="API for the HeavyHaul LLM Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_index():
    return FileResponse("static/index.html")

# Voice for Edge TTS
VOICE = "en-US-JennyNeural"

# Function to convert text to audio using Edge TTS
async def text_to_speech(text):
    communicate = edge_tts.Communicate(text, VOICE)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# Define data models
class ChatRequest(BaseModel):
    order_id: str
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    audio_endpoint: str

class SpeakRequest(BaseModel):
    text: str

# Class for audio response with base64 encoding
class AudioResponse(BaseModel):
    audio_data: str  # Base64 encoded audio data
    mime_type: str = "audio/mp3"

# Session storage
sessions = {}

class Session:
    def __init__(self, order_id):
        self.order_id = order_id
        self.order_document = None
        self.user_input_history = []
        self.State_value = None
        self.global_state_value = None
        
        # Initialize conversation log
        os.makedirs("logs", exist_ok=True)
        with open(f"logs/{order_id}.txt", "w", encoding="utf-8") as file:
            file.write("Conversation Log\n\n")
            
        # Fetch order document
        self.order_document = orders_collection.find_one({"token": order_id})
        if not self.order_document:
            raise ValueError(f"Order ID {order_id} not found")

    def log_conversation(self, user_input, assistant_response):
        with open(f"logs/{self.order_id}.txt", "a", encoding="utf-8") as file:
            file.write(f"User input: {user_input}\n")
            file.write(f"Assistant: {assistant_response}\n\n")

    def update_user_input_history(self, user_input):
        self.user_input_history.append(user_input)
        
        while len(self.user_input_history) > MAX_HISTORY:
            self.user_input_history.pop(0)

    def get_previous_user_inputs(self, limit=MAX_HISTORY):
        messages = []
        
        limited_history = self.user_input_history[-limit:] if limit < len(self.user_input_history) else self.user_input_history.copy()
        for input_text in limited_history:
            messages.append({"role": "user", "content": input_text})
        
        return messages
    
    def ask_llm(self, question):
        messages = [{"role": "system", "content": sys_msg}]
        messages.extend(self.get_previous_user_inputs())
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

    def generate_final_response(self, user_input, restructured_data):
        data_str = json.dumps(restructured_data, indent=2)
        user_message = f"Order data:\n{data_str}\n\nUser question: {user_input}"
        
        # Prepare system message
        system_message = """
            You are a helpful voice assistant for a HeavyHaul company. 
            Your task is to analyze the provided filtered order data and respond to user queries in a natural, conversational way like you're talking.
            - Give answer about the order you can see in the data based on the query asked. Don't provide any extra analysis/context from your side.
        """
        
        messages = [{"role": "system", "content": system_message}]
        messages.extend(self.get_previous_user_inputs())
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

    def process_user_query(self, user_input):
        print("\n--- STARTING NEW QUERY ---")
        print(f"[STATE TRACKING] Before processing - State_value: {self.State_value}, global_state_value: {self.global_state_value}")
        
        self.update_user_input_history(user_input)
        
        user_input_lower = user_input.lower()
        state_in_input = None
        for state in states:
            if state.lower() in user_input_lower:
                state_in_input = state
                self.global_state_value = state
                break
        
        if state_in_input:
            print(f"[STATE TRACKING] Found state in user input: {state_in_input}, updated global_state_value")
        else:
            print("[STATE TRACKING] No state found in user input")
        
        response = self.ask_llm(user_input)
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
        previous_state_value = self.State_value
        if state_name_present and state_name_value:
            self.State_value = state_name_value
        else:
            # Reset State_value to None if state_name is not present OR has no value
            self.State_value = None
            
        print(f"[STATE TRACKING] Updated State_value from {previous_state_value} to {self.State_value}")
        
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
                fetched_data[key] = key_to_function[key](self.order_document)
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
        elif self.State_value:
            mentioned_state = self.State_value
            print(f"[STATE FILTERING] Using State_value: {mentioned_state}")
        # If still no state, check global_state_value but only if permit_info is requested
        elif self.global_state_value and has_permit_info:
            mentioned_state = self.global_state_value
            print(f"[STATE FILTERING] Using global_state_value with permit_info: {mentioned_state}")
        else:
            print("[STATE FILTERING] No state to filter by")
                
        restructured_data = restructure_single_result(fetched_data, self.order_id)
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
                    self.order_id
                )
                download_messages.append(result)
                
            if 'invoice' in restructured_data:
                result = download_document(
                    restructured_data['invoice'],
                    'invoice',
                    self.order_id
                )
                download_messages.append(result)
                
            if download_messages:
                response_text = "\n".join(download_messages)
                # Log the conversation
                self.log_conversation(user_input, response_text)
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
                if self.order_id:
                    order_dimensions = fetch_order_data(self.order_document)
                    if order_dimensions is None:
                        response_text = "Could not fetch order dimensions."
                        self.log_conversation(user_input, response_text)
                        return response_text
                                
                system_message = (
                    'NOTE: Provide concise and direct responses based on the permit information. If the permit_info does not mention any information related to the query, respond with "NO" and specify which field the query is related to from the following: state_name, speed_limit, operating_time, restricted_travel, escorts, signs_flags_lights, miscellaneous, state_info, night_travel, permit_limits, superloads.\n'
                    f"Here is the permit information for {state_name}: {state_permit_info}"
                )
                                        
                formatted_query = f"My dimensions: {order_dimensions}\n\n {user_input} (after checking my dimensions) (respond in 1 sentence and dont give unnecessary info or checks)"
                
                messages = [{"role": "system", "content": system_message}]
                
                # For permit_info, use only 3 previous user inputs
                messages.extend(self.get_previous_user_inputs(MAX_PERMIT_HISTORY))
                
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
                
                print(f"[RESPONSE] Permit response generated: {response_text[:50]}...")
                self.log_conversation(user_input, response_text)
                return response_text
            else:
                print(f"[PERMIT PROCESS] No permit info found for state: {mentioned_state}")
        
        print("[PROCESS] Generating final conversational response")
        final_response = self.generate_final_response(user_input, restructured_data)
        print(f"[RESPONSE] Final response generated: {final_response[:50]}...")
        
        self.log_conversation(user_input, final_response)
        print("--- QUERY PROCESSING COMPLETE ---\n")
        return final_response

# API route to get a session
def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return sessions[session_id]

# Endpoint to convert text to speech
@app.post("/speak")
async def speak(request: SpeakRequest):
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        print(f"[SPEAK] Converting to speech: '{request.text[:50]}...'")
        audio_data = await text_to_speech(request.text)
        return Response(content=audio_data, media_type="audio/mpeg")
    except Exception as e:
        print(f"[ERROR] Error in speak endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")

# API Endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        print(f"[CHAT] Received request - Order ID: {request.order_id}, Message: '{request.message[:50]}...'")
        
        # If session_id is provided, use existing session
        if request.session_id and request.session_id in sessions:
            print(f"[CHAT] Using existing session: {request.session_id}")
            session = sessions[request.session_id]
        # Otherwise, create a new session
        else:
            session_id = f"{request.order_id}_{int(time.time())}"
            print(f"[CHAT] Creating new session: {session_id}")
            try:
                session = Session(request.order_id)
                sessions[session_id] = session
            except ValueError as e:
                print(f"[ERROR] Failed to create session: {str(e)}")
                raise HTTPException(status_code=404, detail=str(e))
            
        process_start_time = time.time()
        response_text = session.process_user_query(request.message)
        process_end_time = time.time()
        process_duration = process_end_time - process_start_time
        print(f"[TIMING] Total processing time: {process_duration:.2f}s")
        
        # Use existing session ID or the newly created one
        session_id = request.session_id or session_id
        
        # Generate the audio endpoint URL for the response
        audio_endpoint = "/speak"
        
        response = ChatResponse(
            response=response_text,
            session_id=session_id,
            audio_endpoint=audio_endpoint
        )
        
        print(f"[CHAT] Returning response - Session ID: {session_id}, Response: '{response_text[:50]}...'")
        return response
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Error processing request: {str(e)}\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

# Endpoint to create a new session
@app.post("/sessions")
async def create_session(order_id: str):
    try:
        session_id = f"{order_id}_{int(time.time())}"
        print(f"[SESSION] Creating new session: {session_id}")
        session = Session(order_id)
        sessions[session_id] = session
        return {"session_id": session_id, "message": f"Session created for order {order_id}"}
    except ValueError as e:
        print(f"[ERROR] Failed to create session: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)