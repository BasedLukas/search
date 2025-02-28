import os
import json
import requests
from typing import List, Dict, Any
from openai import OpenAI  # Import the client class
import dotenv

dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Instantiate the client with your API key
client = OpenAI(api_key=OPENAI_API_KEY)

# Define the function schema for local search
TOOLS = [{
    "type": "function",
    "function": {
        "name": "local_search",  # This is crucial: the function name must be provided
        "description": "Perform a search query using the local search API.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to be executed on the local search API."
                }
            },
            "required": ["query"],
            "additionalProperties": False
        },
        "strict": True
    }
}]

def call_local_search(query: str) -> Dict[str, Any]:
    """
    Calls your local search API with the provided query.
    """
    try:
        response = requests.post("http://localhost:5000/api", json={"query": query})
        response.raise_for_status()
        return response.text
    except Exception as e:
        return {"error": str(e)}

def chat_with_openai(messages: List[Dict[str, str]], tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Calls the OpenAI Chat API synchronously using the client.
    Passes the function definitions via the 'functions' parameter.
    Returns the raw message dict from the API.
    """
    response = client.chat.completions.create(
        model="gpt-4-0613",
        messages=messages,
        tools=tools  # Ensure that 'functions' is provided
    )
    # Return the message (it may include a function call)
    return response.choices[0].message.to_dict()


def main(use_search: bool = True) -> None:
    """
    Runs the conversation:
      - If `use_search=True`, the model is allowed to call the local_search function.
      - If `use_search=False`, no function is provided, and the model generates a response without searching.
    """
    user_question = input("You: ")
    messages = [
        {
            "role": "system",
            "content": (
                "If asked technical questions, make use of the locally available search function to "
                "get up-to-date information. When needed, call the function 'local_search' with a "
                "JSON object containing the key 'query'."
            ) if use_search else "Answer the user's questions as best you can."
        },
        {"role": "user", "content": user_question}
    ]

    # Initial call to the chat API
    response_message = chat_with_openai(messages, tools=TOOLS if use_search else None)

    if use_search and "tool_calls" in response_message and response_message["tool_calls"]:
        function_call = response_message["tool_calls"][0]
        try:
            args = json.loads(function_call["function"]["arguments"])
            query = args.get("query", "")
        except Exception as e:
            print("Error parsing function call arguments:", e)
            return

        if query:
            print("Detected search function call with query:", query)
            local_result = call_local_search(query)
            # Append the function call message and its result to the conversation
            messages.append(response_message)
            messages.append({
                "role": "tool",
                "tool_call_id": function_call["id"],
                "content": json.dumps(local_result)
            })
            print("\nLocal API called. Continuing conversation...\n")
            final_response = chat_with_openai(messages, tools=TOOLS)
            print("AI:", final_response.get("content", ""))
        else:
            print("\nFunction call detected but no query provided. Conversation complete.")
    else:
        print("AI:", response_message.get("content", ""))

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the chatbot with or without local search.")
    parser.add_argument("--no-search", action="store_true", help="Disable local search for this session.")
    args = parser.parse_args()

    main(use_search=not args.no_search)