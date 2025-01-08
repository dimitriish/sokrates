import ollama

def ollama_call(messages, model='gemma2:2b'):
    """
    Calls Ollama LLM with the given messages and model.
    messages should be a list of dicts like:
    [
       {"role": "system", "content": "..."},
       {"role": "user", "content": "..."}
    ]
    """
    response = ollama.chat(model=model, messages=messages)
    return response['message']['content']