TITLE: Call OpenAI Chat Completion (Python)
DESCRIPTION: Demonstrates how to call the OpenAI chat completion API using the `openai` library. It sends a user prompt to the `gpt-4o` model and returns the model's response. Requires the `openai` library and an API key, which is recommended to store securely.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/llm.md#_snippet_0

LANGUAGE: python
CODE:
```
def call_llm(prompt):
    from openai import OpenAI
    client = OpenAI(api_key="YOUR_API_KEY_HERE")
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return r.choices[0].message.content

# Example usage
call_llm("How are you?")
```

----------------------------------------

TITLE: Add Caching with Retry Handling (Python)
DESCRIPTION: Presents a caching strategy designed to work with retries, allowing the cache to be bypassed on subsequent attempts. It uses `lru_cache` and accesses the original function via `__wrapped__`. Includes an example of how this might be used within a `Node` class.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/llm.md#_snippet_8

LANGUAGE: python
CODE:
```
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_call(prompt):
    pass

def call_llm(prompt, use_cache):
    if use_cache:
        return cached_call(prompt)
    # Call the underlying function directly
    return cached_call.__wrapped__(prompt)

class SummarizeNode(Node):
    def exec(self, text):
        return call_llm(f"Summarize: {text}", self.cur_retry==0)
```

----------------------------------------

TITLE: Composing an Order Processing Pipeline with Nested Flows in Python
DESCRIPTION: Provides a practical example of breaking down a complex process (order processing) into multiple independent sub-flows (payment, inventory, shipping). Each sub-flow is defined and can be composed into a larger, overarching flow, demonstrating a modular approach to pipeline design.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/flow.md#_snippet_3

LANGUAGE: Python
CODE:
```
# Payment processing sub-flow
validate_payment >> process_payment >> payment_confirmation
payment_flow = Flow(start=validate_payment)

# Inventory sub-flow
check_stock >> reserve_items >> update_inventory
inventory_flow = Flow(start=check_stock)

# Shipping sub-flow
create_label >> assign_carrier >> schedule_pickup
shipping_flow = Flow(start=create_label)
```

----------------------------------------

TITLE: Defining Offline RAG Pipeline Nodes in Python
DESCRIPTION: This snippet defines three Python classes (`ChunkDocs`, `EmbedDocs`, `StoreIndex`) that represent the core components of the offline RAG indexing stage. `ChunkDocs` reads and splits text files into smaller segments. `EmbedDocs` generates vector embeddings for each chunk using a `get_embedding` function. `StoreIndex` creates and stores a vector index (e.g., FAISS) from these embeddings. These nodes are designed to be wired together in a sequence to form a data processing flow.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/rag.md#_snippet_0

LANGUAGE: Python
CODE:
```
class ChunkDocs(BatchNode):
    def prep(self, shared):
        # A list of file paths in shared["files"]. We process each file.
        return shared["files"]

    def exec(self, filepath):
        # read file content. In real usage, do error handling.
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        # chunk by 100 chars each
        chunks = []
        size = 100
        for i in range(0, len(text), size):
            chunks.append(text[i : i + size])
        return chunks
    
    def post(self, shared, prep_res, exec_res_list):
        # exec_res_list is a list of chunk-lists, one per file.
        # flatten them all into a single list of chunks.
        all_chunks = []
        for chunk_list in exec_res_list:
            all_chunks.extend(chunk_list)
        shared["all_chunks"] = all_chunks

class EmbedDocs(BatchNode):
    def prep(self, shared):
        return shared["all_chunks"]

    def exec(self, chunk):
        return get_embedding(chunk)

    def post(self, shared, prep_res, exec_res_list):
        # Store the list of embeddings.
        shared["all_embeds"] = exec_res_list
        print(f"Total embeddings: {len(exec_res_list)}")

class StoreIndex(Node):
    def prep(self, shared):
        # We'll read all embeds from shared.
        return shared["all_embeds"]

    def exec(self, all_embeds):
        # Create a vector index (faiss or other DB in real usage).
        index = create_index(all_embeds)
        return index

    def post(self, shared, prep_res, index):
        shared["index"] = index

# Wire them in sequence
chunk_node = ChunkDocs()
embed_node = EmbedDocs()
store_node = StoreIndex()

chunk_node >> embed_node >> store_node

OfflineFlow = Flow(start=chunk_node)
```

----------------------------------------

TITLE: Calling LLM and Generating Embeddings - Python
DESCRIPTION: This Python snippet illustrates how to interact with a large language model using `call_llm` to get a text response and how to generate a text embedding using `get_embedding`. It demonstrates the basic API calls for AI model interaction within the PocketFlow framework.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_2

LANGUAGE: Python
CODE:
```
response = call_llm("What's the meaning of life?")
print(response)
embedding = get_embedding("What's the meaning of life?")
print(embedding)
```

----------------------------------------

TITLE: Call Anthropic Claude API (Python)
DESCRIPTION: Shows how to call the Anthropic Claude API using the `anthropic` library. It sends a user prompt to the `claude-3-7-sonnet-20250219` model with a specified maximum token limit and returns the model's text response. Requires the `anthropic` library and an API key.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/llm.md#_snippet_1

LANGUAGE: python
CODE:
```
def call_llm(prompt):
    from anthropic import Anthropic
    client = Anthropic(api_key="YOUR_API_KEY_HERE")
    r = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=3000,
        messages=[
                {"role": "user", "content": prompt}
            ]
    )
    return r.content[0].text
```

----------------------------------------

TITLE: Data Science Flow Definition in Python
DESCRIPTION: This code defines a complex Flow for data science, including nodes for data preparation, validation, feature extraction, model training, and evaluation. It demonstrates how to connect these nodes to create a data science pipeline.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/viz.md#_snippet_1

LANGUAGE: Python
CODE:
```
class DataPrepBatchNode(BatchNode):
    def prep(self,shared): return []
class ValidateDataNode(Node): pass
class FeatureExtractionNode(Node): pass
class TrainModelNode(Node): pass
class EvaluateModelNode(Node): pass
class ModelFlow(Flow): pass
class DataScienceFlow(Flow):pass

feature_node = FeatureExtractionNode()
train_node = TrainModelNode()
evaluate_node = EvaluateModelNode()
feature_node >> train_node >> evaluate_node
model_flow = ModelFlow(start=feature_node)
data_prep_node = DataPrepBatchNode()
validate_node = ValidateDataNode()
data_prep_node >> validate_node >> model_flow
data_science_flow = DataScienceFlow(start=data_prep_node)
result = build_mermaid(start=data_science_flow)
```

----------------------------------------

TITLE: Visualizing the Order Pipeline with Mermaid Flowchart
DESCRIPTION: This Mermaid diagram provides a visual representation of the order processing pipeline, detailing the sub-flows for payment, inventory, and shipping. It illustrates the internal steps within each sub-flow and the sequential connection between them, offering a clear overview of the system's architecture and execution flow.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/flow.md#_snippet_5

LANGUAGE: mermaid
CODE:
```
flowchart LR
    subgraph order_pipeline[Order Pipeline]
        subgraph paymentFlow["Payment Flow"]
            A[Validate Payment] --> B[Process Payment] --> C[Payment Confirmation]
        end

        subgraph inventoryFlow["Inventory Flow"]
            D[Check Stock] --> E[Reserve Items] --> F[Update Inventory]
        end

        subgraph shippingFlow["Shipping Flow"]
            G[Create Label] --> H[Assign Carrier] --> I[Schedule Pickup]
        end

        paymentFlow --> inventoryFlow
        inventoryFlow --> shippingFlow
    end
```

----------------------------------------

TITLE: Implementing AsyncGuesser for Taboo Game in Python
DESCRIPTION: This class defines the 'Guesser' agent's behavior. It asynchronously retrieves hints from the hinter's queue, uses an LLM to make a guess based on the hint and past wrong guesses, and then evaluates if the guess is correct. If correct, it signals game over; otherwise, it updates past guesses and sends the guess back to the hinter for a new hint.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/multi_agent.md#_snippet_2

LANGUAGE: Python
CODE:
```
class AsyncGuesser(AsyncNode):
    async def prep_async(self, shared):
        hint = await shared["guesser_queue"].get()
        return hint, shared.get("past_guesses", [])

    async def exec_async(self, inputs):
        hint, past_guesses = inputs
        prompt = f"Given hint: {hint}, past wrong guesses: {past_guesses}, make a new guess. Directly reply a single word:"
        guess = call_llm(prompt)
        print(f"Guesser: I guess it's - {guess}")
        return guess

    async def post_async(self, shared, prep_res, exec_res):
        if exec_res.lower() == shared["target_word"].lower():
            print("Game Over - Correct guess!")
            await shared["hinter_queue"].put("GAME_OVER")
            return "end"
            
        if "past_guesses" not in shared:
            shared["past_guesses"] = []
        shared["past_guesses"].append(exec_res)
        
        await shared["hinter_queue"].put(exec_res)
        return "continue"
```

----------------------------------------

TITLE: Constructing and Running a RAG Workflow in Python
DESCRIPTION: This snippet demonstrates how to instantiate the custom nodes (`PrepareEmbeddings`, `FindRelevantDocument`, `AnswerQuestion`) and connect them to form a complete RAG workflow. It defines the flow's sequence and conditional transitions, then executes the entire process using the `Flow` class, starting with embedding preparation.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_16

LANGUAGE: Python
CODE:
```
# Create nodes and flow
prep_embeddings = PrepareEmbeddings()
find_relevant = FindRelevantDocument()
answer = AnswerQuestion()

# Connect nodes
prep_embeddings >> find_relevant
find_relevant - "answer" >> answer
find_relevant - "end" >> None
answer - "continue" >> find_relevant

# Create and run flow
rag_flow = Flow(start=prep_embeddings)
rag_flow.run(shared)
```

----------------------------------------

TITLE: Complete SummarizeFile Node Example with Fallback and Execution in Python
DESCRIPTION: This comprehensive example defines a `SummarizeFile` Node, illustrating all three core steps (`prep`, `exec`, `post`) and a custom `exec_fallback` for graceful error handling. It shows how the node processes input data, calls an LLM, handles potential failures, and stores the result. The example also demonstrates how to instantiate and run the node, observing its behavior with retries and fallback.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/node.md#_snippet_3

LANGUAGE: Python
CODE:
```
class SummarizeFile(Node):
    def prep(self, shared):
        return shared["data"]

    def exec(self, prep_res):
        if not prep_res:
            return "Empty file content"
        prompt = f"Summarize this text in 10 words: {prep_res}"
        summary = call_llm(prompt)  # might fail
        return summary

    def exec_fallback(self, prep_res, exc):
        # Provide a simple fallback instead of crashing
        return "There was an error processing your request."

    def post(self, shared, prep_res, exec_res):
        shared["summary"] = exec_res
        # Return "default" by not returning

summarize_node = SummarizeFile(max_retries=3)

# node.run() calls prep->exec->post
# If exec() fails, it retries up to 3 times before calling exec_fallback()
action_result = summarize_node.run(shared)

print("Action returned:", action_result)
print("Summary stored:", shared["summary"])
```

----------------------------------------

TITLE: Implementing an LLM Utility Function in Python
DESCRIPTION: This Python utility function, `call_llm`, demonstrates how to interact with the OpenAI API to generate responses from a large language model. It takes a `prompt` as input, uses `gpt-4o` as the model, and returns the generated content. It requires the `openai` library and an API key for authentication.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/guide.md#_snippet_1

LANGUAGE: python
CODE:
```
# utils/call_llm.py
from openai import OpenAI

def call_llm(prompt):    
    client = OpenAI(api_key="YOUR_API_KEY_HERE")
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return r.choices[0].message.content
    
if __name__ == "__main__":
    prompt = "What is the meaning of life?"
    print(call_llm(prompt))
```

----------------------------------------

TITLE: Creating a Question-Answering Flow in PocketFlow (Python)
DESCRIPTION: This code defines `create_qa_flow`, a function responsible for assembling a PocketFlow `Flow`. It instantiates the `GetQuestionNode` and `AnswerNode`, connects them sequentially using the `>>` operator, and returns a `Flow` object starting with the input node.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/guide.md#_snippet_4

LANGUAGE: Python
CODE:
```
# flow.py
from pocketflow import Flow
from nodes import GetQuestionNode, AnswerNode

def create_qa_flow():
    """Create and return a question-answering flow."""
    # Create nodes
    get_question_node = GetQuestionNode()
    answer_node = AnswerNode()
    
    # Connect nodes in sequence
    get_question_node >> answer_node
    
    # Create flow starting with input node
    return Flow(start=get_question_node)
```

----------------------------------------

TITLE: Handle Chat History with OpenAI (Python)
DESCRIPTION: Modifies the basic LLM call function to accept a list of messages, enabling the handling of conversation history. This example uses the OpenAI API with the `gpt-4o` model. Requires the `openai` library and an API key.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/llm.md#_snippet_6

LANGUAGE: python
CODE:
```
def call_llm(messages):
    from openai import OpenAI
    client = OpenAI(api_key="YOUR_API_KEY_HERE")
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    return r.choices[0].message.content
```

----------------------------------------

TITLE: Implementing Real-time Chat with WebSockets in JavaScript
DESCRIPTION: This JavaScript code manages the client-side logic for a real-time chat application using WebSockets. It handles connection status, sends user messages, receives and displays AI responses (including streaming chunks), and updates the UI dynamically based on message types and connection states.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-websocket/static/index.html#_snippet_1

LANGUAGE: JavaScript
CODE:
```
const ws = new WebSocket(`ws://localhost:8000/ws`);
const messagesDiv = document.getElementById('messages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const statusDiv = document.getElementById('status');
let isStreaming = false;
let currentAiMessage = null;

ws.onopen = function() {
  statusDiv.textContent = 'Connected';
  messageInput.disabled = false;
  sendButton.disabled = false;
  messageInput.focus();
};

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  if (data.type === 'start') {
    isStreaming = true;
    currentAiMessage = document.createElement('div');
    currentAiMessage.className = 'message ai-message';
    messagesDiv.appendChild(currentAiMessage);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    sendButton.disabled = true;
    statusDiv.textContent = 'AI is typing...';
  } else if (data.type === 'chunk') {
    if (currentAiMessage) {
      currentAiMessage.textContent += data.content;
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
  } else if (data.type === 'end') {
    isStreaming = false;
    currentAiMessage = null;
    sendButton.disabled = false;
    statusDiv.textContent = 'Connected';
    messageInput.focus();
  }
};

ws.onclose = function() {
  statusDiv.textContent = 'Disconnected';
  messageInput.disabled = true;
  sendButton.disabled = true;
};

function sendMessage() {
  const message = messageInput.value.trim();
  if (message && !isStreaming) {
    const userMessage = document.createElement('div');
    userMessage.className = 'message user-message';
    userMessage.textContent = message;
    messagesDiv.appendChild(userMessage);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    ws.send(JSON.stringify({ type: 'message', content: message }));
    messageInput.value = '';
    statusDiv.textContent = 'Sending...';
  }
}

sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', function(e) {
  if (e.key === 'Enter') {
    e.preventDefault();
    sendMessage();
  }
});
```

----------------------------------------

TITLE: Creating Agent Flow with PocketFlow (Python)
DESCRIPTION: This `create_agent_flow` function defines the orchestration of the research agent using PocketFlow. It instantiates the `DecideAction`, `SearchWeb`, and `AnswerQuestion` nodes and connects them to establish the workflow: decision leads to search or answer, and search loops back to decision. It returns a `Flow` object starting with the `DecideAction` node.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/demo.ipynb#_snippet_7

LANGUAGE: Python
CODE:
```
# flow.py
from pocketflow import Flow

def create_agent_flow():
    """
    Create and connect the nodes to form a complete agent flow.

    The flow works like this:
    1. DecideAction node decides whether to search or answer
    2. If search, go to SearchWeb node
    3. If answer, go to AnswerQuestion node
    4. After SearchWeb completes, go back to DecideAction

    Returns:
        Flow: A complete research agent flow
    """
    # Create instances of each node
    decide = DecideAction()
    search = SearchWeb()
    answer = AnswerQuestion()

    # Connect the nodes
    # If DecideAction returns "search", go to SearchWeb
    decide - "search" >> search

    # If DecideAction returns "answer", go to AnswerQuestion
    decide - "answer" >> answer

    # After SearchWeb completes and returns "decide", go back to DecideAction
    search - "decide" >> decide

    # Create and return the flow, starting with the DecideAction node
    return Flow(start=decide)
```

----------------------------------------

TITLE: Defining the AnswerQuestion Node in Python
DESCRIPTION: This class implements the `AnswerQuestion` node, handling the logic for generating answers using a Large Language Model (LLM). The `prep` method prepares the question and context, `exec` constructs the LLM prompt and calls the model, and `post` prints the results and signals to continue the flow.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_14

LANGUAGE: Python
CODE:
```
class AnswerQuestion(Node):
    def prep(self, shared):
        return (
            shared["current_question"],
            shared["context"]
        )
        
    def exec(self, inputs):
        question, context = inputs
        prompt = f"""\nContext: {context}\n\nQuestion: {question}\n\nAnswer the question based on the context above. If the context doesn't contain relevant information, say so.\nAnswer:"""
        return call_llm(prompt)
    
    def post(self, shared, prep_res, exec_res):
        print(f"\nQ: {shared['current_question']}")
        print(f"A: {exec_res}")
        print(f"\nSource: {shared['relevant_file']}")
        return "continue"  # Loop back for more questions
```

----------------------------------------

TITLE: Converting Audio to Text STT Python
DESCRIPTION: Converts recorded in-memory audio data (NumPy array) to text using a Speech-to-Text (STT) API. It reads audio data from shared state, converts it to a suitable format (e.g., WAV bytes), calls the STT API, appends the transcribed text to the chat history, and clears the temporary audio data.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-voice-chat/docs/design.md#_snippet_3

LANGUAGE: Python
CODE:
```
# SpeechToTextNode
# Purpose: Convert the recorded in-memory audio to text.

# prep:
# Read shared["user_audio_data"] (NumPy array) and shared["user_audio_sample_rate"].
# Return (user_audio_data_numpy, user_audio_sample_rate).
audio_numpy_array, sample_rate = shared["user_audio_data"], shared["user_audio_sample_rate"]

# exec:
# Convert audio_numpy_array to audio bytes (e.g., WAV using scipy.io.wavfile.write to io.BytesIO).
audio_bytes = convert_numpy_to_wav_bytes(audio_numpy_array, sample_rate) # Placeholder for conversion logic
# Call utils.speech_to_text.speech_to_text_api(audio_bytes, sample_rate).
exec_res = utils.speech_to_text.speech_to_text_api(audio_bytes, sample_rate)

# post:
# transcribed_text = exec_res
# Append {"role": "user", "content": transcribed_text} to shared["chat_history"].
# Clear shared["user_audio_data"] and shared["user_audio_sample_rate"].
# Returns "default".
```

----------------------------------------

TITLE: Converting Text to Speech TTS Python
DESCRIPTION: Converts the LLM's text response into speech and plays it back. It reads the last message from chat history, calls the Text-to-Speech (TTS) API, converts the resulting audio bytes to a NumPy array, plays the audio, and determines the next workflow step based on the conversation continuation flag.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-voice-chat/docs/design.md#_snippet_5

LANGUAGE: Python
CODE:
```
# TextToSpeechNode
# Purpose: Convert the LLM's text response into speech and play it.

# prep:
# Read shared["chat_history"].
# Identify the last message (LLM's response).
# Return its content.
text_to_synthesize = shared["chat_history"][-1]["content"]

# exec:
# Call utils.text_to_speech.text_to_speech_api(text_to_synthesize).
# This returns (llm_audio_bytes, llm_sample_rate).
exec_res = utils.text_to_speech.text_to_speech_api(text_to_synthesize)

# post:
# llm_audio_bytes, llm_sample_rate = exec_res
# Convert llm_audio_bytes (e.g., MP3) to a NumPy array (e.g., using pydub or soundfile).
llm_audio_numpy_array = convert_audio_bytes_to_numpy(llm_audio_bytes, llm_sample_rate) # Placeholder
# Call utils.audio_utils.play_audio_data(llm_audio_numpy_array, llm_sample_rate).
utils.audio_utils.play_audio_data(llm_audio_numpy_array, llm_sample_rate)
# (Optional) Log completion.
# If shared["continue_conversation"] is True, return "next_turn".
# Otherwise, return "end_conversation".
```

----------------------------------------

TITLE: Agent Prompt Structure for Dynamic Actions - Python
DESCRIPTION: This snippet defines a structured f-string prompt used by an agent node to decide its next action. It provides context (task, previous actions, current state) and an action space with descriptions and parameters. The prompt instructs the agent to return its decision in a YAML format, including reasoning, action name, and parameters. This structure guides the LLM to make informed, actionable decisions.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/agent.md#_snippet_0

LANGUAGE: Python
CODE:
```
f"""
### CONTEXT
Task: {task_description}
Previous Actions: {previous_actions}
Current State: {current_state}

### ACTION SPACE
[1] search
  Description: Use web search to get results
  Parameters:
    - query (str): What to search for

[2] answer
  Description: Conclude based on the results
  Parameters:
    - result (str): Final answer to provide

### NEXT ACTION
Decide the next action based on the current context and available action space.
Return your response in the following format:

```yaml
thinking: |
    <your step-by-step reasoning process>
action: <action_name>
parameters:
    <parameter_name>: <parameter_value>
```"""
```

----------------------------------------

TITLE: Implementing Text Summarization with LLM Prompting (Python)
DESCRIPTION: This Python `SummarizeNode` class demonstrates how to prompt an LLM to produce a structured YAML summary. It constructs a prompt, calls the LLM, extracts the YAML, and validates its structure, ensuring a list of exactly 3 bullet points.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/structure.md#_snippet_3

LANGUAGE: python
CODE:
```
class SummarizeNode(Node):
    def exec(self, prep_res):
        # Suppose `prep_res` is the text to summarize.
        prompt = f"""
Please summarize the following text as YAML, with exactly 3 bullet points

{prep_res}

Now, output:
```yaml
summary:
  - bullet 1
  - bullet 2
  - bullet 3
```"""
        response = call_llm(prompt)
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()

        import yaml
        structured_result = yaml.safe_load(yaml_str)

        assert "summary" in structured_result
        assert isinstance(structured_result["summary"], list)

        return structured_result
```

----------------------------------------

TITLE: Defining OpenAI LLM and Embedding Utility Functions (Python)
DESCRIPTION: This Python snippet defines two utility functions: `call_llm` for sending prompts to the OpenAI GPT-4o model and retrieving responses, and `get_embedding` for generating vector embeddings of text using the OpenAI `text-embedding-ada-002` model. Both functions require an `API_KEY` for authentication with the OpenAI service.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_1

LANGUAGE: Python
CODE:
```
from openai import OpenAI
import os

def call_llm(prompt):
    client = OpenAI(api_key=API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def get_embedding(text):
    client = OpenAI(api_key=API_KEY)
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding
```

----------------------------------------

TITLE: Implementing Parallel Batch Processing with AsyncParallelBatchNode in Python
DESCRIPTION: This snippet demonstrates how to use `AsyncParallelBatchNode` to process multiple items concurrently. It defines a `ParallelSummaries` node that prepares a list of texts, calls an LLM asynchronously for each text in parallel, and then combines the summaries. This is ideal for I/O-bound tasks like LLM calls.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/parallel.md#_snippet_0

LANGUAGE: Python
CODE:
```
class ParallelSummaries(AsyncParallelBatchNode):
    async def prep_async(self, shared):
        # e.g., multiple texts
        return shared["texts"]

    async def exec_async(self, text):
        prompt = f"Summarize: {text}"
        return await call_llm_async(prompt)

    async def post_async(self, shared, prep_res, exec_res_list):
        shared["summary"] = "\n\n".join(exec_res_list)
        return "default"

node = ParallelSummaries()
flow = AsyncFlow(start=node)
```

----------------------------------------

TITLE: Defining Online RAG Query Nodes in Python
DESCRIPTION: This snippet defines three Python classes (`EmbedQuery`, `RetrieveDocs`, `GenerateAnswer`) that constitute the online RAG query and answer generation stage. `EmbedQuery` generates an embedding for the user's question. `RetrieveDocs` uses this embedding to search the pre-built index and retrieve the most relevant document chunk. `GenerateAnswer` then combines the original question and the retrieved chunk into a prompt for an LLM to generate the final answer. These nodes are designed to be chained for a complete query flow.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/rag.md#_snippet_2

LANGUAGE: Python
CODE:
```
class EmbedQuery(Node):
    def prep(self, shared):
        return shared["question"]

    def exec(self, question):
        return get_embedding(question)

    def post(self, shared, prep_res, q_emb):
        shared["q_emb"] = q_emb

class RetrieveDocs(Node):
    def prep(self, shared):
        # We'll need the query embedding, plus the offline index/chunks
        return shared["q_emb"], shared["index"], shared["all_chunks"]

    def exec(self, inputs):
        q_emb, index, chunks = inputs
        I, D = search_index(index, q_emb, top_k=1)
        best_id = I[0][0]
        relevant_chunk = chunks[best_id]
        return relevant_chunk

    def post(self, shared, prep_res, relevant_chunk):
        shared["retrieved_chunk"] = relevant_chunk
        print("Retrieved chunk:", relevant_chunk[:60], "...")

class GenerateAnswer(Node):
    def prep(self, shared):
        return shared["question"], shared["retrieved_chunk"]

    def exec(self, inputs):
        question, chunk = inputs
        prompt = f"Question: {question}\nContext: {chunk}\nAnswer:"
        return call_llm(prompt)

    def post(self, shared, prep_res, answer):
        shared["answer"] = answer
        print("Answer:", answer)

embed_qnode = EmbedQuery()
retrieve_node = RetrieveDocs()
generate_node = GenerateAnswer()

embed_qnode >> retrieve_node >> generate_node
OnlineFlow = Flow(start=embed_qnode)
```

----------------------------------------

TITLE: Implementing an Async Node with AsyncFlow in Python
DESCRIPTION: This snippet demonstrates how to define a custom `AsyncNode` subclass, `SummarizeThenVerify`, with `prep_async` for reading data, `exec_async` for making LLM calls, and `post_async` for handling user feedback. It also illustrates how to set up transitions between nodes and execute the `AsyncFlow` asynchronously using `asyncio`.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/async.md#_snippet_0

LANGUAGE: python
CODE:
```
class SummarizeThenVerify(AsyncNode):
    async def prep_async(self, shared):
        # Example: read a file asynchronously
        doc_text = await read_file_async(shared["doc_path"])
        return doc_text

    async def exec_async(self, prep_res):
        # Example: async LLM call
        summary = await call_llm_async(f"Summarize: {prep_res}")
        return summary

    async def post_async(self, shared, prep_res, exec_res):
        # Example: wait for user feedback
        decision = await gather_user_feedback(exec_res)
        if decision == "approve":
            shared["summary"] = exec_res
            return "approve"
        return "deny"

summarize_node = SummarizeThenVerify()
final_node = Finalize()

# Define transitions
summarize_node - "approve" >> final_node
summarize_node - "deny"    >> summarize_node  # retry

flow = AsyncFlow(start=summarize_node)

async def main():
    shared = {"doc_path": "document.txt"}
    await flow.run_async(shared)
    print("Final Summary:", shared.get("summary"))

asyncio.run(main())
```

----------------------------------------

TITLE: Querying LLM Chat History Python
DESCRIPTION: Queries a Large Language Model (LLM) based on the current conversation history. It reads the chat history from shared state, calls the LLM API with the history as messages, and appends the LLM's response to the shared chat history.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-voice-chat/docs/design.md#_snippet_4

LANGUAGE: Python
CODE:
```
# QueryLLMNode
# Purpose: Get a response from the LLM based on the user's query and conversation history.

# prep:
# Read shared["chat_history"].
# Return chat_history.
history = shared["chat_history"]

# exec:
# Call utils.call_llm.call_llm(messages=history).
exec_res = utils.call_llm.call_llm(messages=history)

# post:
# llm_response = exec_res
# Append {"role": "assistant", "content": llm_response} to shared["chat_history"].
# Returns "default".
```

----------------------------------------

TITLE: Shared Store Design for Chain of Thought Node - Python
DESCRIPTION: Defines the structure of the `shared` dictionary, which holds the problem statement, a list of generated thoughts, a counter for the current thought, and the final solution. This store facilitates state management across iterations of the Chain of Thought process.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/design.md#_snippet_1

LANGUAGE: python
CODE:
```
shared = {
    "problem": str,             # The problem statement.
    "thoughts": list[dict],     # List of thought dictionaries generated so far.
    "current_thought_number": int, # Counter for the current thought being generated.
    "solution": str | None    # Stores the final conclusion text when finished.
}
```

----------------------------------------

TITLE: Implementing Parallel Sub-Flow Execution with AsyncParallelBatchFlow in Python
DESCRIPTION: This snippet illustrates the use of `AsyncParallelBatchFlow` to run a sub-flow concurrently for different parameters. It defines a `SummarizeMultipleFiles` flow that prepares a list of filenames, and then executes a `LoadAndSummarizeFile` sub-flow for each file in parallel. This is useful for orchestrating parallel operations across multiple data points.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/parallel.md#_snippet_1

LANGUAGE: Python
CODE:
```
class SummarizeMultipleFiles(AsyncParallelBatchFlow):
    async def prep_async(self, shared):
        return [{"filename": f} for f in shared["files"]]

sub_flow = AsyncFlow(start=LoadAndSummarizeFile())
parallel_flow = SummarizeMultipleFiles(start=sub_flow)
await parallel_flow.run_async(shared)
```

----------------------------------------

TITLE: Finding Relevant Document using FAISS Index - Python
DESCRIPTION: This PocketFlow Node, `FindRelevantDocument`, handles user interaction by prompting for a question, generating an embedding for the question, and then performing a similarity search against the pre-built FAISS index stored in the shared context. It retrieves the most relevant document's filename based on the search results, demonstrating how to query the indexed embeddings.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_12

LANGUAGE: python
CODE:
```
class FindRelevantDocument(Node):
    def prep(self, shared):
        # Get user question
        question = input("Enter your question (or press Enter to quit): ")
        if not question:
            return None
        return question
        
    def exec(self, question):
        if question is None:
            return None
            
        # Get question embedding and search
        query_embedding = get_embedding(question)
        
        # Search for most similar document
        D, I = shared["search_index"].search(
            np.array([query_embedding]).astype('float32'),
            k=1
        )
        most_relevant_idx = I[0][0]
        most_relevant_file = shared["filenames"][most_relevant_idx]
        
        return question, most_relevant_file
        
    def post(self, shared, prep_res, exec_res):
        if exec_res is None:
            return "end"
```

----------------------------------------

TITLE: Nesting Flows within a Parent Flow in Python
DESCRIPTION: Shows how to embed one 'Flow' (subflow) as a node within another 'Flow' (parent flow). This enables modularity and reuse, where the subflow executes completely before the parent flow continues to the next node, demonstrating powerful composition patterns.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/flow.md#_snippet_2

LANGUAGE: Python
CODE:
```
# Create a sub-flow
node_a >> node_b
subflow = Flow(start=node_a)

# Connect it to another node
subflow >> node_c

# Create the parent flow
parent_flow = Flow(start=subflow)
```

----------------------------------------

TITLE: AnswerQuestion Node for Agent Workflow (Python)
DESCRIPTION: The `AnswerQuestion` class, another PocketFlow `Node`, is responsible for generating the final answer. Its `prep` method retrieves the question and context, `exec` calls an LLM to synthesize the answer based on the provided information, and `post` saves the final answer and signals the completion of the flow.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/demo.ipynb#_snippet_6

LANGUAGE: Python
CODE:
```
class AnswerQuestion(Node):
    def prep(self, shared):
        """Get the question and context for answering."""
        return shared["question"], shared.get("context", "")

    def exec(self, inputs):
        """Call the LLM to generate a final answer."""
        question, context = inputs

        print(f"✍️ Crafting final answer...")

        # Create a prompt for the LLM to answer the question
        prompt = f"""
### CONTEXT
Based on the following information, answer the question.
Question: {question}
Research: {context}

## YOUR ANSWER:
Provide a comprehensive answer using the research results.
"""
        # Call the LLM to generate an answer
        answer = call_llm(prompt)
        return answer

    def post(self, shared, prep_res, exec_res):
        """Save the final answer and complete the flow."""
        # Save the answer in the shared store
        shared["answer"] = exec_res

        print(f"✅ Answer generated successfully")

        # We're done - no need to continue the flow
        return "done"
```

----------------------------------------

TITLE: Running Online RAG Query Pipeline in Python
DESCRIPTION: This example illustrates how to execute the `OnlineFlow` for a user query. It assumes that the `shared` dictionary already contains the `all_chunks` and `index` from the offline stage. It then adds a user `question` to the `shared` dictionary and runs `OnlineFlow.run(shared)`. The pipeline processes the question, retrieves context, and generates an answer, which is then stored in `shared["answer"]`.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/rag.md#_snippet_3

LANGUAGE: Python
CODE:
```
# Suppose we already ran OfflineFlow and have:
# shared["all_chunks"], shared["index"], etc.
shared["question"] = "Why do people like cats?"

OnlineFlow.run(shared)
# final answer in shared["answer"]
```

----------------------------------------

TITLE: Generating Embeddings with OpenAI (Python)
DESCRIPTION: This Python snippet demonstrates how to generate text embeddings using the OpenAI API. It initializes the OpenAI client with an API key, creates an embedding for a given text using a specified model, and then extracts and prints the resulting embedding vector as a NumPy array.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/embedding.md#_snippet_0

LANGUAGE: Python
CODE:
```
from openai import OpenAI

client = OpenAI(api_key="YOUR_API_KEY")
response = client.embeddings.create(
    model="text-embedding-ada-002",
    input=text
)
    
# Extract the embedding vector from the response
embedding = response.data[0].embedding
embedding = np.array(embedding, dtype=np.float32)
print(embedding)
```

----------------------------------------

TITLE: Defining LLM and Web Search Utilities in Python
DESCRIPTION: This Python snippet from `utils.py` defines two core functions: `call_llm` for interacting with the OpenAI API to generate responses from a large language model (GPT-4o), and `search_web` for performing web searches using DuckDuckGo and formatting the results. It also includes example usage demonstrating how to test both functions.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/demo.ipynb#_snippet_1

LANGUAGE: python
CODE:
```
from openai import OpenAI
import os
from duckduckgo_search import DDGS

def call_llm(prompt):
    client = OpenAI(api_key="your-api-key")
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return r.choices[0].message.content

def search_web(query):
    results = DDGS().text(query, max_results=5)
    # Convert results to a string
    results_str = "\n\n".join([f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}" for r in results])
    return results_str

print("## Testing call_llm")
prompt = "In a few words, what is the meaning of life?"
print(f"## Prompt: {prompt}")
response = call_llm(prompt)
print(f"## Response: {response}")

print("## Testing search_web")
query = "Who won the Nobel Prize in Physics 2024?"
print(f"## Query: {query}")
results = search_web(query)
print(f"## Results: {results}")
```

----------------------------------------

TITLE: Chaining Nodes in PocketFlow
DESCRIPTION: This snippet demonstrates the chaining mechanism in PocketFlow, where 'node_1''s output is directed as input to 'node_2', allowing for sequential processing steps. It's a fundamental way to build linear workflows.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_7

LANGUAGE: Python
CODE:
```
node_1 >> node_2
```

----------------------------------------

TITLE: Mermaid Graph of Agent Workflow
DESCRIPTION: This Mermaid diagram illustrates the core graph structure of the research agent. It shows the flow between `DecideAction`, `SearchWeb`, and `AnswerQuestion` nodes, highlighting the decision points for searching or answering.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/README.md#_snippet_5

LANGUAGE: mermaid
CODE:
```
graph TD
    A[DecideAction] -->|"search"| B[SearchWeb]
    A -->|"answer"| C[AnswerQuestion]
    B -->|"decide"| A
```

----------------------------------------

TITLE: Defining Pocketflow Shared Memory Structure - Python
DESCRIPTION: This dictionary defines the structure of the shared memory object used to pass data between nodes in the pocketflow processing flow. It stores temporary state such as user audio data, sample rate, conversation history, and a flag to control the main loop.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-voice-chat/docs/design.md#_snippet_1

LANGUAGE: Python
CODE:
```
shared = {
    "user_audio_data": None,      # In-memory audio data (NumPy array) from user
    "user_audio_sample_rate": None, # int: Sample rate of the user audio
    "chat_history": [],            # list: Conversation history [{"role": "user/assistant", "content": "..."}]
    "continue_conversation": True # boolean: Flag to control the main conversation loop
}
```

----------------------------------------

TITLE: Implementing MapReduce for Document Summarization in Python
DESCRIPTION: This Python example demonstrates the MapReduce pattern using `BatchNode` for the map phase and `Node` for the reduce phase. The `SummarizeAllFiles` class processes multiple input files concurrently, generating individual summaries. The `CombineSummaries` class then aggregates these individual summaries into a single, final summary. It showcases how to set up a `Flow` and pass shared data for execution.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/mapreduce.md#_snippet_0

LANGUAGE: Python
CODE:
```
class SummarizeAllFiles(BatchNode):
    def prep(self, shared):
        files_dict = shared["files"]  # e.g. 10 files
        return list(files_dict.items())  # [("file1.txt", "aaa..."), ("file2.txt", "bbb..."), ...]

    def exec(self, one_file):
        filename, file_content = one_file
        summary_text = call_llm(f"Summarize the following file:\n{file_content}")
        return (filename, summary_text)

    def post(self, shared, prep_res, exec_res_list):
        shared["file_summaries"] = dict(exec_res_list)

class CombineSummaries(Node):
    def prep(self, shared):
        return shared["file_summaries"]

    def exec(self, file_summaries):
        # format as: "File1: summary\nFile2: summary...\n"
        text_list = []
        for fname, summ in file_summaries.items():
            text_list.append(f"{fname} summary:\n{summ}\n")
        big_text = "\n---\n".join(text_list)

        return call_llm(f"Combine these file summaries into one final summary:\n{big_text}")

    def post(self, shared, prep_res, final_summary):
        shared["all_files_summary"] = final_summary

batch_node = SummarizeAllFiles()
combine_node = CombineSummaries()
batch_node >> combine_node

flow = Flow(start=batch_node)

shared = {
    "files": {
        "file1.txt": "Alice was beginning to get very tired of sitting by her sister...",
        "file2.txt": "Some other interesting text ...",
        # ...
    }
}
flow.run(shared)
print("Individual Summaries:", shared["file_summaries"])
print("\nFinal Summary:\n", shared["all_files_summary"])
```

----------------------------------------

TITLE: Connecting, Defining Schema, and Searching Milvus (Python)
DESCRIPTION: This snippet demonstrates connecting to a Milvus instance, defining a collection schema with an ID and a float vector field, inserting random data into the collection, creating an index on the vector field, loading the collection into memory, and finally performing a vector search to find similar embeddings. It covers the full lifecycle of data management and querying in Milvus.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/vector.md#_snippet_4

LANGUAGE: python
CODE:
```
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection
import numpy as np

connections.connect(alias="default", host="localhost", port="19530")

fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128)
]
schema = CollectionSchema(fields)
collection = Collection("MyCollection", schema)

emb = np.random.rand(10, 128).astype('float32')
ids = list(range(10))
collection.insert([ids, emb])

index_params = {
    "index_type": "IVF_FLAT",
    "params": {"nlist": 128},
    "metric_type": "L2"
}
collection.create_index("embedding", index_params)
collection.load()

query_emb = np.random.rand(1, 128).astype('float32')
results = collection.search(query_emb, "embedding", param={"nprobe": 10}, limit=3)
print(results)
```

----------------------------------------

TITLE: Generating Embeddings with AWS Bedrock (Python)
DESCRIPTION: This Python snippet shows how to generate text embeddings using AWS Bedrock. It initializes a Boto3 client for Bedrock Runtime, constructs a JSON payload with the input text, invokes a specified Titan embedding model, and then parses the response to extract and print the embedding vector.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/embedding.md#_snippet_3

LANGUAGE: Python
CODE:
```
import boto3, json

client = boto3.client("bedrock-runtime", region_name="us-east-1")
body = {"inputText": "Hello world"}
resp = client.invoke_model(modelId="amazon.titan-embed-text-v2:0", contentType="application/json", body=json.dumps(body))
resp_body = json.loads(resp["body"].read())
vec = resp_body["embedding"]
print(vec)
```

----------------------------------------

TITLE: Preparing Document Embeddings and FAISS Index - Python
DESCRIPTION: This PocketFlow Node, `PrepareEmbeddings`, is responsible for taking document content, generating vector embeddings for each document using an assumed `get_embedding` function, and then constructing a FAISS (Facebook AI Similarity Search) index. The resulting FAISS index and the list of original filenames are stored in the shared context for subsequent nodes to utilize, enabling efficient similarity searches.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_11

LANGUAGE: python
CODE:
```
from pocketflow import Node, Flow
import faiss
import numpy as np
import os

class PrepareEmbeddings(Node):
    def prep(self, shared):
        # Get list of (filename, content) pairs
        return list(shared["data"].items())
        
    def exec(self, items):
        # Create embeddings for each document
        embeddings = []
        filenames = []
        for filename, content in items:
            embedding = get_embedding(content)
            embeddings.append(embedding)
            filenames.append(filename)
            
        # Create FAISS index
        dim = len(embeddings[0])
        index = faiss.IndexFlatL2(dim)
        index.add(np.array(embeddings).astype('float32'))
        
        return index, filenames
    
    def post(self, shared, prep_res, exec_res):
        # Store index and filenames in shared store
        index, filenames = exec_res
        shared["search_index"] = index
        shared["filenames"] = filenames
        return "default"
```

----------------------------------------

TITLE: Implementing Agent Communication with Asyncio Queue in Python
DESCRIPTION: This Python example demonstrates inter-agent communication using `asyncio.Queue`. It defines an `AgentNode` that asynchronously retrieves and processes messages from a queue, and a `send_system_messages` coroutine that continuously puts messages into the same queue. The `main` function orchestrates the concurrent execution of the agent flow and the message sender, showcasing a basic producer-consumer pattern for multi-agent systems.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/multi_agent.md#_snippet_0

LANGUAGE: Python
CODE:
```
class AgentNode(AsyncNode):
    async def prep_async(self, _):
        message_queue = self.params["messages"]
        message = await message_queue.get()
        print(f"Agent received: {message}")
        return message

# Create node and flow
agent = AgentNode()
agent >> agent  # connect to self
flow = AsyncFlow(start=agent)

# Create heartbeat sender
async def send_system_messages(message_queue):
    counter = 0
    messages = [
        "System status: all systems operational",
        "Memory usage: normal",
        "Network connectivity: stable",
        "Processing load: optimal"
    ]
    
    while True:
        message = f"{messages[counter % len(messages)]} | timestamp_{counter}"
        await message_queue.put(message)
        counter += 1
        await asyncio.sleep(1)

async def main():
    message_queue = asyncio.Queue()
    shared = {}
    flow.set_params({"messages": message_queue})
    
    # Run both coroutines
    await asyncio.gather(
        flow.run_async(shared),
        send_system_messages(message_queue)
    )
    
asyncio.run(main())
```

----------------------------------------

TITLE: Defining Nodes for LLM Interaction in PocketFlow (Python)
DESCRIPTION: This snippet defines two PocketFlow `Node` classes: `GetQuestionNode` for capturing user input and `AnswerNode` for calling an LLM. It illustrates how nodes use `exec` for core logic and `post` or `prep` to interact with a shared state dictionary.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/guide.md#_snippet_3

LANGUAGE: Python
CODE:
```
# nodes.py
from pocketflow import Node
from utils.call_llm import call_llm

class GetQuestionNode(Node):
    def exec(self, _):
        # Get question directly from user input
        user_question = input("Enter your question: ")
        return user_question
    
    def post(self, shared, prep_res, exec_res):
        # Store the user's question
        shared["question"] = exec_res
        return "default"  # Go to the next node

class AnswerNode(Node):
    def prep(self, shared):
        # Read question from shared
        return shared["question"]
    
    def exec(self, question):
        # Call LLM to get the answer
        return call_llm(question)
    
    def post(self, shared, prep_res, exec_res):
        # Store the answer in shared
        shared["answer"] = exec_res
```

----------------------------------------

TITLE: Defining Shared Store Structure for Workflow Data (Python)
DESCRIPTION: This snippet defines the structure of the `shared` dictionary, which acts as a central data store for the article generation workflow. It holds the initial topic, an `asyncio.Queue` for real-time SSE updates, intermediate results like `sections` and `draft` content, and the `final_article`. This store facilitates data exchange between different processing nodes.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/docs/design.md#_snippet_0

LANGUAGE: Python
CODE:
```
shared = {
    "topic": "user-provided-topic",
    "sse_queue": asyncio.Queue(),  # For sending SSE updates
    "sections": ["section1", "section2", "section3"],
    "draft": "combined-section-content",
    "final_article": "styled-final-article"
}
```

----------------------------------------

TITLE: Directed Branching with Action in PocketFlow
DESCRIPTION: This snippet illustrates directed branching in PocketFlow, where 'node_1''s 'post()' method returns an 'action' string that dictates the flow to 'node_2'. This enables agentic decision-making within the graph.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_8

LANGUAGE: Python
CODE:
```
node_1 - "action" ->> node_2
```

----------------------------------------

TITLE: Connecting, Recreating Collection, and Searching Qdrant (Python)
DESCRIPTION: This snippet demonstrates connecting to a Qdrant cloud endpoint using an API key, recreating a collection with specified vector parameters (size and distance metric), upserting points with associated payloads, and performing a vector search to find the nearest neighbors within the collection. It covers the essential steps for managing data in Qdrant.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/vector.md#_snippet_2

LANGUAGE: python
CODE:
```
import qdrant_client
from qdrant_client.models import Distance, VectorParams, PointStruct

client = qdrant_client.QdrantClient(
    url="https://YOUR-QDRANT-CLOUD-ENDPOINT",
    api_key="YOUR_API_KEY"
)

collection = "my_collection"
client.recreate_collection(
    collection_name=collection,
    vectors_config=VectorParams(size=128, distance=Distance.COSINE)
)

points = [
    PointStruct(id=1, vector=[0.1]*128, payload={"type": "doc1"}),
    PointStruct(id=2, vector=[0.2]*128, payload={"type": "doc2"}),
]

client.upsert(collection_name=collection, points=points)

results = client.search(
    collection_name=collection,
    query_vector=[0.15]*128,
    limit=2
)
print(results)
```

----------------------------------------

TITLE: Setting OpenAI API Key via .env File
DESCRIPTION: This line demonstrates how to set the OpenAI API key within a `.env` file. This method is recommended for local development as it keeps sensitive credentials out of version control and allows for easy management of environment-specific variables.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-embeddings/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
OPENAI_API_KEY=your_api_key_here
```

----------------------------------------

TITLE: Setting Up Environment Variables - .env
DESCRIPTION: This snippet shows the required environment variables for configuring the Google Calendar API and application settings. `GOOGLE_CALENDAR_ID` specifies the target calendar, `GOOGLE_APPLICATION_CREDENTIALS` points to the API credentials file, and `TIMEZONE` sets the application's operational timezone.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-google-calendar/README.md#_snippet_2

LANGUAGE: env
CODE:
```
# Google Calendar API Configuration
GOOGLE_CALENDAR_ID=your_calendar_id@group.calendar.google.com
GOOGLE_APPLICATION_CREDENTIALS=credentials.json

# Application Configuration
TIMEZONE=America/Sao_Paulo  # or your preferred timezone
```

----------------------------------------

TITLE: Initializing and Querying FAISS Index (Python)
DESCRIPTION: This snippet demonstrates how to initialize a FAISS `IndexFlatL2` index for vector search, add random data to it, and then perform a k-nearest neighbors search. It utilizes `numpy` for efficient vector operations and showcases the basic workflow for setting up and querying a FAISS index.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/vector.md#_snippet_0

LANGUAGE: python
CODE:
```
import faiss
import numpy as np

# Dimensionality of embeddings
d = 128

# Create a flat L2 index
index = faiss.IndexFlatL2(d)

# Random vectors
data = np.random.random((1000, d)).astype('float32')
index.add(data)

# Query
query = np.random.random((1, d)).astype('float32')
D, I = index.search(query, k=5)

print("Distances:", D)
print("Neighbors:", I)
```

----------------------------------------

TITLE: Defining Branching and Looping Transitions in Python
DESCRIPTION: Illustrates how to create complex flow logic using named actions for branching and default transitions for looping. This example models an expense approval process with 'approved', 'needs_revision', and 'rejected' paths, showing how different actions lead to different subsequent nodes.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/flow.md#_snippet_1

LANGUAGE: Python
CODE:
```
# Define the flow connections
review - "approved" >> payment        # If approved, process payment
review - "needs_revision" >> revise   # If needs changes, go to revision
review - "rejected" >> finish         # If rejected, finish the process

revise >> review   # After revision, go back for another review
payment >> finish  # After payment, finish the process

flow = Flow(start=review)
```

----------------------------------------

TITLE: Connecting, Defining Schema, and Querying Weaviate (Python)
DESCRIPTION: This example shows how to connect to a Weaviate instance, define a schema for a new class (e.g., 'Article') with a 'none' vectorizer, create a data object with a title, content, and a pre-defined vector, and then execute a vector-based query to retrieve similar articles. It illustrates the schema definition and data interaction patterns in Weaviate.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/vector.md#_snippet_3

LANGUAGE: python
CODE:
```
import weaviate

client = weaviate.Client("https://YOUR-WEAVIATE-CLOUD-ENDPOINT")

schema = {
    "classes": [
        {
            "class": "Article",
            "vectorizer": "none"
        }
    ]
}
client.schema.create(schema)

obj = {
    "title": "Hello World",
    "content": "Weaviate vector search"
}
client.data_object.create(obj, "Article", vector=[0.1]*128)

resp = (
    client.query
    .get("Article", ["title", "content"])
    .with_near_vector({"vector": [0.15]*128})
    .with_limit(3)
    .do()
)
print(resp)
```

----------------------------------------

TITLE: Setting OpenAI API Key Environment Variable
DESCRIPTION: This command sets the `OPENAI_API_KEY` environment variable, which is required for the PocketFlow agent to interact with OpenAI's services. Replace `"your-api-key-here"` with your actual OpenAI API key.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-a2a/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Setting the OpenAI API Key
DESCRIPTION: This command sets the OpenAI API key as an environment variable, which is required to use the real OpenAI streaming functionality in the demo.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-llm-streaming/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Creating Python Virtual Environment - Bash
DESCRIPTION: This command creates a new Python virtual environment named 'venv' in the current directory. Virtual environments isolate project dependencies, preventing conflicts with other Python projects or the system's Python installation.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-database/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
python -m venv venv
```

----------------------------------------

TITLE: Setting Anthropic API Key (Bash)
DESCRIPTION: Sets the `ANTHROPIC_API_KEY` environment variable, which is crucial for authenticating requests to the Anthropic API. Users must replace 'your-api-key-here' with their actual API key to enable communication with the LLM.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-majority-vote/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export ANTHROPIC_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Orchestrating Multi-Agent Taboo Game in Python
DESCRIPTION: This asynchronous `main` function sets up and runs the Taboo game. It initializes shared game state including the target word, forbidden words, and `asyncio.Queue`s for inter-agent communication. It then instantiates `AsyncHinter` and `AsyncGuesser` nodes, defines their asynchronous flows, and runs them concurrently using `asyncio.gather` to simulate the game.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/multi_agent.md#_snippet_3

LANGUAGE: Python
CODE:
```
async def main():
    # Set up game
    shared = {
        "target_word": "nostalgia",
        "forbidden_words": ["memory", "past", "remember", "feeling", "longing"],
        "hinter_queue": asyncio.Queue(),
        "guesser_queue": asyncio.Queue()
    }
    
    print("Game starting!")
    print(f"Target word: {shared['target_word']}")
    print(f"Forbidden words: {shared['forbidden_words']}")

    # Initialize by sending empty guess to hinter
    await shared["hinter_queue"].put("")

    # Create nodes and flows
    hinter = AsyncHinter()
    guesser = AsyncGuesser()

    # Set up flows
    hinter_flow = AsyncFlow(start=hinter)
    guesser_flow = AsyncFlow(start=guesser)

    # Connect nodes to themselves
    hinter - "continue" >> hinter
    guesser - "continue" >> guesser

    # Run both agents concurrently
    await asyncio.gather(
        hinter_flow.run_async(shared),
        guesser_flow.run_async(shared)
    )

asyncio.run(main())
```

----------------------------------------

TITLE: Implementing DecideAction PocketFlow Node in Python
DESCRIPTION: This Python snippet defines the `DecideAction` class, a custom `Node` for the PocketFlow framework. It includes `prep` and `exec` methods: `prep` retrieves the current context and question, while `exec` constructs a detailed prompt in YAML format for an LLM to decide between performing a web search or providing a final answer based on the given context and question.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/demo.ipynb#_snippet_2

LANGUAGE: python
CODE:
```
from pocketflow import Node
import yaml

class DecideAction(Node):
    def prep(self, shared):
        """Prepare the context and question for the decision-making process."""
        # Get the current context (default to "No previous search" if none exists)
        context = shared.get("context", "No previous search")
        # Get the question from the shared store
        question = shared["question"]
        # Return both for the exec step
        return question, context

    def exec(self, inputs):
        """Call the LLM to decide whether to search or answer."""
        question, context = inputs

        print(f"🤔 Agent deciding what to do next...")

        # Create a prompt to help the LLM decide what to do next with proper yaml formatting
        prompt = f"""
### CONTEXT
You are a research assistant that can search the web.
Question: {question}
Previous Research: {context}

### ACTION SPACE
[1] search
  Description: Look up more information on the web
  Parameters:
    - query (str): What to search for

[2] answer
  Description: Answer the question with current knowledge
  Parameters:
    - answer (str): Final answer to the question

"""
```

----------------------------------------

TITLE: Call Local Ollama LLM (Python)
DESCRIPTION: Shows how to interact with a local Ollama instance using the `ollama` library. It sends a user prompt to the specified model (e.g., `llama2`) running locally via Ollama and returns the model's response content. Requires the `ollama` library and a running Ollama instance.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/llm.md#_snippet_4

LANGUAGE: python
CODE:
```
def call_llm(prompt):
    from ollama import chat
    response = chat(
        model="llama2",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.message.content
```

----------------------------------------

TITLE: DecideAction Node for Agent Workflow (Python)
DESCRIPTION: This `DecideAction` class, inheriting from `Node`, is responsible for determining the agent's next step. Its `exec` method calls an LLM to decide whether to perform a web search or provide an answer, based on the current context. The `post` method saves the LLM's decision and returns the chosen action to guide the flow.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/demo.ipynb#_snippet_4

LANGUAGE: Python
CODE:
```
        # Call the LLM to make a decision
        response = call_llm(prompt)

        # Parse the response to get the decision
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()
        decision = yaml.safe_load(yaml_str)

        return decision

    def post(self, shared, prep_res, exec_res):
        """Save the decision and determine the next step in the flow."""
        # If LLM decided to search, save the search query
        if exec_res["action"] == "search":
            shared["search_query"] = exec_res["search_query"]
            print(f"🔍 Agent decided to search for: {exec_res['search_query']}")
        else:
            shared["context"] = exec_res["answer"] #save the context if LLM gives the answer without searching.
            print(f"💡 Agent decided to answer the question")

        # Return the action to determine the next node in the flow
        return exec_res["action"]
```

----------------------------------------

TITLE: Implementing AsyncHinter for Taboo Game in Python
DESCRIPTION: This class defines the 'Hinter' agent's behavior in the Taboo game. It asynchronously prepares game state (target word, forbidden words, past guesses), generates hints using an LLM while avoiding forbidden words, and posts the hint to the guesser's queue. It handles game termination by checking for a 'GAME_OVER' signal.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/multi_agent.md#_snippet_1

LANGUAGE: Python
CODE:
```
class AsyncHinter(AsyncNode):
    async def prep_async(self, shared):
        guess = await shared["hinter_queue"].get()
        if guess == "GAME_OVER":
            return None
        return shared["target_word"], shared["forbidden_words"], shared.get("past_guesses", [])

    async def exec_async(self, inputs):
        if inputs is None:
            return None
        target, forbidden, past_guesses = inputs
        prompt = f"Generate hint for '{target}'\nForbidden words: {forbidden}"
        if past_guesses:
            prompt += f"\nPrevious wrong guesses: {past_guesses}\nMake hint more specific."
        prompt += "\nUse at most 5 words."
        
        hint = call_llm(prompt)
        print(f"\nHinter: Here's your hint - {hint}")
        return hint

    async def post_async(self, shared, prep_res, exec_res):
        if exec_res is None:
            return "end"
        await shared["guesser_queue"].put(exec_res)
        return "continue"
```

----------------------------------------

TITLE: Initializing a Node with Retries in Python
DESCRIPTION: This snippet demonstrates how to instantiate a Node, specifically `SummarizeFile`, with fault tolerance parameters. `max_retries` specifies the maximum number of attempts for the `exec()` method, and `wait` defines the delay in seconds between retries, useful for handling rate limits.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/node.md#_snippet_0

LANGUAGE: Python
CODE:
```
my_node = SummarizeFile(max_retries=3, wait=10)
```

----------------------------------------

TITLE: Initializing Client, Adding Data, and Querying Chroma (Python)
DESCRIPTION: This code demonstrates how to initialize a Chroma client with a persistent directory, create a new collection, add embeddings along with their metadata and unique IDs to the collection, and then perform a query using a query embedding to retrieve the most similar results. It showcases the basic operations for setting up and interacting with a Chroma database.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/vector.md#_snippet_5

LANGUAGE: python
CODE:
```
import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_data"
))

coll = client.create_collection("my_collection")

vectors = [[0.1, 0.2, 0.3], [0.2, 0.2, 0.2]]
metas = [{"doc": "text1"}, {"doc": "text2"}]
ids = ["id1", "id2"]
coll.add(embeddings=vectors, metadatas=metas, ids=ids)

res = coll.query(query_embeddings=[[0.15, 0.25, 0.3]], n_results=2)
print(res)
```

----------------------------------------

TITLE: Implementing Shared Store Communication in Python
DESCRIPTION: This example demonstrates how `LoadData` and `Summarize` nodes interact using a shared store. `LoadData` writes content to `shared["data"]`, while `Summarize` reads from `shared["data"]`, processes it (e.g., summarizes with an LLM), and writes the result to `shared["summary"]`. This showcases the `prep` and `post` methods for reading from and writing to the shared store.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/communication.md#_snippet_1

LANGUAGE: Python
CODE:
```
class LoadData(Node):
    def post(self, shared, prep_res, exec_res):
        # We write data to shared store
        shared["data"] = "Some text content"
        return None

class Summarize(Node):
    def prep(self, shared):
        # We read data from shared store
        return shared["data"]

    def exec(self, prep_res):
        # Call LLM to summarize
        prompt = f"Summarize: {prep_res}"
        summary = call_llm(prompt)
        return summary

    def post(self, shared, prep_res, exec_res):
        # We write summary to shared store
        shared["summary"] = exec_res
        return "default"

load_data = LoadData()
summarize = Summarize()
load_data >> summarize
flow = Flow(start=load_data)

shared = {}
flow.run(shared)
```

----------------------------------------

TITLE: Installing PocketFlow with pip
DESCRIPTION: This command installs the PocketFlow package using pip, the Python package installer. It allows users to quickly integrate PocketFlow into their Python projects.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-parallel-batch/translations/README_PORTUGUESE.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install pocketflow
```

----------------------------------------

TITLE: SearchWeb Node for Agent Workflow (Python)
DESCRIPTION: The `SearchWeb` class, a `Node` in the PocketFlow system, handles web search operations. Its `prep` method retrieves the search query from shared data, `exec` performs the actual web search using a utility function, and `post` saves the results back into the shared context, then directs the flow back to the decision node.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/demo.ipynb#_snippet_5

LANGUAGE: Python
CODE:
```
class SearchWeb(Node):
    def prep(self, shared):
        """Get the search query from the shared store."""
        return shared["search_query"]

    def exec(self, search_query):
        """Search the web for the given query."""
        # Call the search utility function
        print(f"🌐 Searching the web for: {search_query}")
        results = search_web(search_query)
        return results

    def post(self, shared, prep_res, exec_res):
        """Save the search results and go back to the decision node."""
        # Add the search results to the context in the shared store
        previous = shared.get("context", "")
        shared["context"] = previous + "\n\nSEARCH: " + shared["search_query"] + "\nRESULTS: " + exec_res

        print(f"📚 Found information, analyzing results...")

        # Always go back to the decision node after searching
        return "decide"
```

----------------------------------------

TITLE: Implementing FetchRecipes AsyncNode in Python
DESCRIPTION: This `AsyncNode` handles fetching recipes. `prep_async` gathers the ingredient from user input, while `exec_async` performs an asynchronous API call to `fetch_recipes` using the provided ingredient, returning the list of recipes.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-async-basic/README.md#_snippet_0

LANGUAGE: Python
CODE:
```
async def prep_async(self, shared):
    ingredient = input("Enter ingredient: ")
    return ingredient

async def exec_async(self, ingredient):
    # Async API call
    recipes = await fetch_recipes(ingredient)
    return recipes
```

----------------------------------------

TITLE: Creating Index, Inserting, and Searching in Redis (Python)
DESCRIPTION: This snippet illustrates how to connect to a Redis instance, create a RediSearch vector index using the `FT.CREATE` command with specified vector parameters, insert a vector into a Redis hash, and then perform a K-nearest neighbor (KNN) search using RediSearch's query language. It demonstrates how Redis can be used as a vector database with its search module.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/vector.md#_snippet_6

LANGUAGE: python
CODE:
```
import redis
import struct

r = redis.Redis(host="localhost", port=6379)

# Create index
r.execute_command(
    "FT.CREATE", "my_idx", "ON", "HASH",
    "SCHEMA", "embedding", "VECTOR", "FLAT", "6",
    "TYPE", "FLOAT32", "DIM", "128",
    "DISTANCE_METRIC", "L2"
)

# Insert
vec = struct.pack('128f', *[0.1]*128)
r.hset("doc1", mapping={"embedding": vec})

# Search
qvec = struct.pack('128f', *[0.15]*128)
q = "*=>[KNN 3 @embedding $BLOB AS dist]"
res = r.ft("my_idx").search(q, query_params={"BLOB": qvec})
print(res.docs)
```

----------------------------------------

TITLE: Connecting, Upserting, and Querying Pinecone Index (Python)
DESCRIPTION: This code illustrates how to initialize the Pinecone client with an API key and environment, create a new index if it doesn't already exist, connect to the specified index, upsert vectors with unique IDs, and perform a vector-based query to retrieve similar items. It highlights the core operations for interacting with Pinecone.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/vector.md#_snippet_1

LANGUAGE: python
CODE:
```
import pinecone

pinecone.init(api_key="YOUR_API_KEY", environment="YOUR_ENV")

index_name = "my-index"

# Create the index if it doesn't exist
if index_name not in pinecone.list_indexes():
    pinecone.create_index(name=index_name, dimension=128)

# Connect
index = pinecone.Index(index_name)

# Upsert
vectors = [
    ("id1", [0.1]*128),
    ("id2", [0.2]*128)
]
index.upsert(vectors)

# Query
response = index.query([[0.15]*128], top_k=3)
print(response)
```

----------------------------------------

TITLE: Setting Up PocketFlow Virtual Environment (Bash)
DESCRIPTION: This command sequence creates a Python virtual environment named 'venv' and then activates it, isolating project dependencies from the global Python installation. The activation command differs slightly for Windows.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-hello-world/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

----------------------------------------

TITLE: Extracting Product Information (YAML)
DESCRIPTION: This YAML snippet demonstrates how to extract key product details like name, price, and description into a structured format. It's an example of an LLM output designed for easy parsing and integration.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/structure.md#_snippet_0

LANGUAGE: yaml
CODE:
```
product:
  name: Widget Pro
  price: 199.99
  description: |
    A high-quality widget designed for professionals.
    Recommended for advanced users.
```

----------------------------------------

TITLE: Call Azure OpenAI API (Python)
DESCRIPTION: Illustrates how to call the Azure OpenAI API using the `openai` library configured for Azure. It requires an Azure endpoint URL, API key, API version, and a specific deployment name. It sends a user prompt and returns the model's chat completion response.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/llm.md#_snippet_3

LANGUAGE: python
CODE:
```
def call_llm(prompt):
    from openai import AzureOpenAI
    client = AzureOpenAI(
        azure_endpoint="https://<YOUR_RESOURCE_NAME>.openai.azure.com/",
        api_key="YOUR_API_KEY_HERE",
        api_version="2023-05-15"
    )
    r = client.chat.completions.create(
        model="<YOUR_DEPLOYMENT_NAME>",
        messages=[{"role": "user", "content": prompt}]
    )
    return r.choices[0].message.content
```

----------------------------------------

TITLE: Creating a Simple Sequential Flow in Python
DESCRIPTION: Demonstrates how to define a basic sequential flow where 'node_a' transitions to 'node_b' by default. It shows the instantiation of a 'Flow' object with a start node and its execution using 'flow.run(shared)'.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/flow.md#_snippet_0

LANGUAGE: Python
CODE:
```
node_a >> node_b
flow = Flow(start=node_a)
flow.run(shared)
```

----------------------------------------

TITLE: Creating Python Virtual Environment
DESCRIPTION: This command sequence creates a new Python virtual environment named 'venv' and then activates it. A virtual environment isolates project dependencies, preventing conflicts with other Python projects or the system's Python installation.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-embeddings/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

----------------------------------------

TITLE: Running Offline RAG Pipeline in Python
DESCRIPTION: This example demonstrates how to initialize and run the `OfflineFlow` defined previously. It sets up a `shared` dictionary containing a list of file paths (`doc1.txt`, `doc2.txt`) which the `ChunkDocs` node will process. Executing `OfflineFlow.run(shared)` triggers the entire indexing process, populating the `shared` dictionary with processed chunks and the final vector index.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/rag.md#_snippet_1

LANGUAGE: Python
CODE:
```
shared = {
    "files": ["doc1.txt", "doc2.txt"]  # any text files
}
OfflineFlow.run(shared)
```

----------------------------------------

TITLE: Implementing a Search Agent with Nodes and Flow - Python
DESCRIPTION: This comprehensive example demonstrates a search agent implemented using `Node` and `Flow` classes. The `DecideAction` node determines whether to search or answer, `SearchWeb` performs the web search, and `DirectAnswer` provides the final response. Nodes are connected to create a dynamic flow, allowing the agent to loop back for multiple search steps until sufficient context is gathered. It showcases context management and action branching.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/agent.md#_snippet_1

LANGUAGE: Python
CODE:
```
class DecideAction(Node):
    def prep(self, shared):
        context = shared.get("context", "No previous search")
        query = shared["query"]
        return query, context
        
    def exec(self, inputs):
        query, context = inputs
        prompt = f"""
Given input: {query}
Previous search results: {context}
Should I: 1) Search web for more info 2) Answer with current knowledge
Output in yaml:
```yaml
action: search/answer
reason: why this action
search_term: search phrase if action is search
```"""
        resp = call_llm(prompt)
        yaml_str = resp.split("```yaml")[1].split("```")[0].strip()
        result = yaml.safe_load(yaml_str)
        
        assert isinstance(result, dict)
        assert "action" in result
        assert "reason" in result
        assert result["action"] in ["search", "answer"]
        if result["action"] == "search":
            assert "search_term" in result
        
        return result

    def post(self, shared, prep_res, exec_res):
        if exec_res["action"] == "search":
            shared["search_term"] = exec_res["search_term"]
        return exec_res["action"]

class SearchWeb(Node):
    def prep(self, shared):
        return shared["search_term"]
        
    def exec(self, search_term):
        return search_web(search_term)
    
    def post(self, shared, prep_res, exec_res):
        prev_searches = shared.get("context", [])
        shared["context"] = prev_searches + [
            {"term": shared["search_term"], "result": exec_res}
        ]
        return "decide"
        
class DirectAnswer(Node):
    def prep(self, shared):
        return shared["query"], shared.get("context", "")
        
    def exec(self, inputs):
        query, context = inputs
        return call_llm(f"Context: {context}\nAnswer: {query}")

    def post(self, shared, prep_res, exec_res):
       print(f"Answer: {exec_res}")
       shared["answer"] = exec_res

# Connect nodes
decide = DecideAction()
search = SearchWeb()
answer = DirectAnswer()

decide - "search" >> search
decide - "answer" >> answer
search - "decide" >> decide  # Loop back

flow = Flow(start=decide)
flow.run({"query": "Who won the Nobel Prize in Physics 2024?"})
```

----------------------------------------

TITLE: Activating Virtual Environment (Linux/macOS) - Bash
DESCRIPTION: This command activates the previously created virtual environment on Linux and macOS systems. Once activated, subsequent Python commands will use the Python interpreter and packages within this environment.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-database/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
source venv/bin/activate
```

----------------------------------------

TITLE: Activating Virtual Environment (Windows) - Bash
DESCRIPTION: This command activates the previously created virtual environment on Windows systems. After activation, Python commands will execute within this isolated environment, using its specific interpreter and installed packages.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-database/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
venv\Scripts\activate
```

----------------------------------------

TITLE: Plan Step Dictionary Structure - Python
DESCRIPTION: Illustrates the structure of a single step within the `planning` list. Each step includes a description, status, optional result, optional mark for verification, and can contain nested sub-steps, allowing for hierarchical plan management.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/design.md#_snippet_3

LANGUAGE: python
CODE:
```
# Example structure for a plan step dictionary
{
    "description": str,                     # Description of the step.
    "status": str,                          # "Pending", "Done", "Verification Needed".
    "result": str | None,                   # Optional: Concise result when status is "Done".
    "mark": str | None,                     # Optional: Reason for "Verification Needed".
    "sub_steps": list[dict] | None          # Optional: Nested list for sub-steps.
}
```

----------------------------------------

TITLE: Implementing Batch Text Summarization with PocketFlow in Python
DESCRIPTION: This Python snippet defines a `BatchSummarizeNode` inheriting from PocketFlow's `BatchNode`. It implements `prep` to retrieve data, `exec` to summarize text using a placeholder `call_llm` function, and `post` to store summaries. The example also includes a test setup to load text files from a local directory into a shared store and execute the node.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_5

LANGUAGE: python
CODE:
```
from pocketflow import BatchNode
import os

class BatchSummarizeNode(BatchNode):
    def prep(self, shared):
        # Return list of (filename, content) tuples from shared store
        return [(fn, content) for fn, content in shared["data"].items()]
        
    def exec(self, item):
        # Unpack the filename and content
        filename, text = item
        # Call LLM to summarize
        prompt = f"Summarize this text in 50 words:\n\n{text}"
        summary = call_llm(prompt)
        return filename, summary
    
    def post(self, shared, prep_res, exec_res_list):
        # Store all summaries in a dict by filename
        shared["summaries"] = {
            filename: summary 
            for filename, summary in exec_res_list
        }
        return "default"

# Create test data structure
shared = {
    "data": {},
    "summaries": {}
}

# Load all files from the directory
path = "./data/PaulGrahamEssaysLarge"
for filename in os.listdir(path):
    with open(os.path.join(path, filename), "r") as f:
        shared["data"][filename] = f.read()

# Create and run the batch node
batch_summarize = BatchSummarizeNode()
batch_summarize.run(shared)
```

----------------------------------------

TITLE: Setting API Environment Variables
DESCRIPTION: These commands set the necessary API keys as environment variables. `SERPAPI_API_KEY` is for Google search via SerpAPI, and `OPENAI_API_KEY` is for accessing the GPT-4 model for analysis. Replace placeholders with your actual keys.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-search/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export SERPAPI_API_KEY='your-serpapi-key'
export OPENAI_API_KEY='your-openai-key'
```

----------------------------------------

TITLE: Voice Chat Workflow Diagram (Mermaid)
DESCRIPTION: This Mermaid diagram visualizes the high-level workflow for the continuous voice chat feature. It shows the sequence of steps: capturing audio, converting speech to text, querying the LLM, converting the response to speech and playing it, and then looping back to capture audio for the next turn.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-voice-chat/docs/design.md#_snippet_0

LANGUAGE: Mermaid
CODE:
```
flowchart TD
    CaptureAudio[Capture Audio] --> SpeechToText[Speech to Text]
    SpeechToText --> QueryLLM[Query LLM]
    QueryLLM --> TextToSpeech[Text to Speech & Play]
    TextToSpeech -- "Next Turn" --> CaptureAudio
```

----------------------------------------

TITLE: Defining and Running an Order Pipeline in Python
DESCRIPTION: This Python snippet demonstrates how to define a sequential order processing pipeline by chaining individual flows (payment, inventory, shipping) using the '>>' operator. It then creates a master 'Flow' object starting with the payment flow and executes the entire pipeline with shared data, illustrating a clear, modular execution path.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/flow.md#_snippet_4

LANGUAGE: python
CODE:
```
payment_flow >> inventory_flow >> shipping_flow

# Create the master flow
order_pipeline = Flow(start=payment_flow)

# Run the entire pipeline
order_pipeline.run(shared_data)
```

----------------------------------------

TITLE: YAML Response Format for Agent Decisions
DESCRIPTION: This YAML snippet defines the expected structure for the agent's decision output. It includes fields for reasoning, the chosen action (search or answer), the justification, the answer if applicable, and the search query if a search is performed. It emphasizes proper indentation and multi-line field handling.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/demo.ipynb#_snippet_3

LANGUAGE: YAML
CODE:
```
thinking: |
    <your step-by-step reasoning process>
action: search OR answer
reason: <why you chose this action>
answer: <if action is answer>
search_query: <specific search query if action is search>
```

----------------------------------------

TITLE: Installing PocketFlow Project Dependencies (Bash)
DESCRIPTION: This command installs all required Python packages listed in the 'requirements.txt' file, ensuring that the PocketFlow application has all its necessary libraries to run correctly.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-hello-world/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Implementing a Retrying Node in Python
DESCRIPTION: This code defines a custom Node, `RetryNode`, that demonstrates how to access the current retry count within the `exec()` method using `self.cur_retry`. It intentionally raises an exception to illustrate the retry mechanism.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/node.md#_snippet_1

LANGUAGE: Python
CODE:
```
class RetryNode(Node):
    def exec(self, prep_res):
        print(f"Retry {self.cur_retry} times")
        raise Exception("Failed")
```

----------------------------------------

TITLE: Generating Embeddings with Google Vertex AI (Python)
DESCRIPTION: This Python snippet demonstrates how to obtain text embeddings using Google Vertex AI. It initializes Vertex AI with the project ID and location, loads a pre-trained `TextEmbeddingModel`, and then uses `get_embeddings` to generate and print the embedding for the input text.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/embedding.md#_snippet_2

LANGUAGE: Python
CODE:
```
from vertexai.preview.language_models import TextEmbeddingModel
import vertexai

vertexai.init(project="YOUR_GCP_PROJECT_ID", location="us-central1")
model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")

emb = model.get_embeddings(["Hello world"])
print(emb[0])
```

----------------------------------------

TITLE: Setting OpenAI API Key (Bash)
DESCRIPTION: Sets the OpenAI API key as an environment variable, which is required for the LLM-powered agents (Hinter and Guesser) to function. Replace `your_api_key_here` with your actual API key.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-multi-agent/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY=your_api_key_here
```

----------------------------------------

TITLE: Setting OpenAI API Key in Bash
DESCRIPTION: This snippet shows how to set the OpenAI API key as an environment variable in a bash shell. This key is required for authenticating API requests to OpenAI services. Alternatively, the key can be updated directly within the `utils.py` file.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-mcp/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Setting OpenAI API Key (Bash)
DESCRIPTION: This snippet demonstrates how to set the OpenAI API key as an environment variable using the `export` command. This is a common prerequisite for applications interacting with OpenAI services, ensuring secure access without hardcoding credentials directly into the application code.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-chat-guardrail/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Setting OpenAI API Key Environment Variable
DESCRIPTION: This command sets the `OPENAI_API_KEY` environment variable, which is required for the agent to authenticate with the OpenAI API. Replace "your-api-key-here" with your actual API key.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Research Agent Graph Structure (Mermaid)
DESCRIPTION: This Mermaid diagram illustrates the internal graph structure of the research agent and its interaction with the supervisor. It visualizes the flow of decisions and actions, including web searches, answer generation, and supervisor validation, providing insight into the system's architecture.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-supervisor/README.md#_snippet_5

LANGUAGE: mermaid
CODE:
```
graph TD
    subgraph InnerAgent[Inner Research Agent]
        DecideAction -->|"search"| SearchWeb
        DecideAction -->|"answer"| UnreliableAnswerNode
        SearchWeb -->|"decide"| DecideAction
    end
    
    InnerAgent --> SupervisorNode
    SupervisorNode -->|"retry"| InnerAgent
```

----------------------------------------

TITLE: Installing Pocket Flow and OpenAI Dependencies (Python)
DESCRIPTION: These `pip` commands install the core Pocket Flow library, `faiss-cpu` for efficient similarity search (often used with embeddings), and the `openai` Python client, which are prerequisites for interacting with OpenAI models and building AI applications.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_0

LANGUAGE: Python
CODE:
```
! pip install pocketflow
! pip install faiss-cpu
! pip install openai
```

----------------------------------------

TITLE: Implementing a Text Summarization Node with PocketFlow (Python)
DESCRIPTION: This Python snippet defines a `SummarizeNode` class inheriting from `pocketflow.Node` to perform text summarization. The `prep` method reads input text from a shared dictionary, `exec` constructs a prompt and calls an assumed `call_llm` function for summarization, and `post` stores the LLM's output back into the shared dictionary. The example also includes a test setup to load data from a file and execute the node.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_3

LANGUAGE: python
CODE:
```
from pocketflow import Node

class SummarizeNode(Node):
    def prep(self, shared):
        # Read data from shared store
        return shared["data"]["before.txt"]
        
    def exec(self, text):
        # Call LLM to summarize
        prompt = f"Summarize this text in 50 words:\n\n{text}"
        return call_llm(prompt)
    
    def post(self, shared, prep_res, exec_res):
        # Store the summary back
        shared["summary"] = exec_res
        # No specific next action needed
        return "default"

# Create test data
shared = {
    "data": {},
    "summary": None
}

# Load the file
with open("./data/PaulGrahamEssaysLarge/before.txt", "r") as f:
    shared["data"]["before.txt"] = f.read()

# Create and run the node
summarize_node = SummarizeNode()
summarize_node.run(shared)
```

----------------------------------------

TITLE: Handling Article Generation Progress Updates - JavaScript
DESCRIPTION: This function processes incoming progress data from the SSE connection. It updates the progress bar, status messages, and step indicators based on the current stage of article generation (e.g., 'connected', 'outline', 'content', 'style', 'complete'), displaying errors or the final article as needed.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/static/progress.html#_snippet_3

LANGUAGE: JavaScript
CODE:
```
function handleProgressUpdate(data) {
  if (data.error) {
    showError(data.error);
    return;
  }
  if (data.heartbeat) {
    return; // Ignore heartbeat messages
  }
  const progress = data.progress || 0;
  updateProgress(progress);
  switch (data.step) {
    case 'connected':
      updateStatus('🔗 Connected', 'Successfully connected to the article generation process.');
      break;
    case 'outline':
      updateStepIndicator(1);
      if (data.data && data.data.sections) {
        updateStatus('📝 Creating Outline', `Generated outline with ${data.data.sections.length} sections`);
      } else {
        updateStatus('📝 Creating Outline', 'Generating article structure and main points...');
      }
      break;
    case 'content':
      updateStepIndicator(2);
      if (data.data && data.data.section) {
        updateStatus('✍️ Writing Content', `Writing section: "${data.data.section}" (${data.data.completed_sections}/${data.data.total_sections})`);
      } else {
        updateStatus('✍️ Writing Content', 'Creating detailed content for each section...');
      }
      break;
    case 'style':
      updateStepIndicator(3);
      updateStatus('🎨 Applying Style', 'Polishing the article with engaging, conversational tone...');
      break;
    case 'complete':
      updateStepIndicator(3, true);
      updateProgress(100);
      updateStatus('✅ Complete!', 'Your article has been generated successfully.');
      if (data.data && data.data.final_article) {
        showResult(data.data.final_article);
      }
      break;
  }
}
```

----------------------------------------

TITLE: Performing Web Search with Brave Search API (Python)
DESCRIPTION: This Python code shows how to interact with the Brave Search API. It requires a subscription token for authentication, which is passed in the 'X-Subscription-Token' header. The script sends a GET request to the Brave search endpoint with the specified query and outputs the JSON response.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/websearch.md#_snippet_3

LANGUAGE: Python
CODE:
```
import requests

SUBSCRIPTION_TOKEN = "YOUR_BRAVE_API_TOKEN"
query = "example"

url = "https://api.search.brave.com/res/v1/web/search"
headers = {
    "X-Subscription-Token": SUBSCRIPTION_TOKEN
}
params = {
    "q": query
}

response = requests.get(url, headers=headers, params=params)
results = response.json()
print(results)
```

----------------------------------------

TITLE: Add In-Memory Caching (Python)
DESCRIPTION: Demonstrates adding simple in-memory caching to a function using Python's `functools.lru_cache` decorator. The cache stores results based on function arguments up to a specified maximum size. The implementation details of the LLM call are omitted.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/llm.md#_snippet_7

LANGUAGE: python
CODE:
```
from functools import lru_cache

@lru_cache(maxsize=1000)
def call_llm(prompt):
    # Your implementation here
    pass
```

----------------------------------------

TITLE: Installing Python Dependencies
DESCRIPTION: Installs all necessary Python packages listed in the `requirements.txt` file, which are prerequisites for running the PocketFlow Code Generator.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-code-generator/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Installing Python Dependencies for PocketFlow A2A Agent
DESCRIPTION: This command installs all required Python packages listed in the `requirements.txt` file. It is a prerequisite for running both the PocketFlow agent and the A2A server and client components.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-a2a/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Installing Python Dependencies (bash)
DESCRIPTION: Installs the required Python packages listed in the `requirements.txt` file using pip. This is a standard step for setting up a Python project.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-pdf-vision/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Installing Python Dependencies with pip
DESCRIPTION: Installs the required Python packages listed in the `requirements.txt` file. This is the first step to set up the project environment.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-text2sql/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Installing Python Dependencies with Pip
DESCRIPTION: This command installs all necessary Python packages listed in the `requirements.txt` file. It ensures that all project dependencies are met before running the application.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-streamlit-fsm/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Add Logging to LLM Call (Python)
DESCRIPTION: Illustrates how to integrate basic logging into the LLM call function using Python's `logging` module. It logs the input prompt before the call and the response after the call. The actual LLM call implementation is represented by a placeholder.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/llm.md#_snippet_9

LANGUAGE: python
CODE:
```
def call_llm(prompt):
    import logging
    logging.info(f"Prompt: {prompt}")
    response = ... # Your implementation here
    logging.info(f"Response: {response}")
    return response
```

----------------------------------------

TITLE: Understanding PocketFlow Project Structure
DESCRIPTION: This snippet illustrates the typical directory layout for a PocketFlow project, showing the location of documentation, utility functions, the core PocketFlow implementation, and the main application entry point.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-hello-world/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
.
├── docs/          # Documentation files
├── utils/         # Utility functions
├── flow.py        # PocketFlow implementation
├── main.py        # Main application entry point
└── README.md      # Project documentation
```

----------------------------------------

TITLE: Installing Dependencies and Running Application in Bash
DESCRIPTION: This snippet outlines the steps to install project dependencies using pip from `requirements.txt` and then run the main application script `main.py`. These commands are essential for setting up and launching the PocketFlow agent.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-mcp/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
python main.py
```

----------------------------------------

TITLE: Implementing Naive (Fixed-Size) Text Chunking in Python
DESCRIPTION: This Python function implements a naive fixed-size text chunking approach. It splits the input text into segments of a specified character length, ignoring sentence or semantic boundaries. While simple, this method can lead to awkwardly cut sentences, reducing coherence.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/chunking.md#_snippet_0

LANGUAGE: python
CODE:
```
def fixed_size_chunk(text, chunk_size=100):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i : i + chunk_size])
    return chunks
```

----------------------------------------

TITLE: Processing Document Search Results in Python
DESCRIPTION: This snippet defines the execution logic for a node responsible for processing the results of a document search. It updates the shared state with the current question, the relevant filename, and the extracted context, then signals to proceed to the 'answer' stage.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_13

LANGUAGE: Python
CODE:
```
question, filename = exec_res
shared["current_question"] = question
shared["relevant_file"] = filename
shared["context"] = shared["data"][filename]
return "answer"
```

----------------------------------------

TITLE: Defining and Running an Article Writing Workflow - Python
DESCRIPTION: This Python snippet defines a multi-stage workflow for article generation using custom Node classes (GenerateOutline, WriteSection, ReviewAndRefine). It illustrates how to chain these nodes together to form a Flow, enabling complex tasks to be broken down into sequential LLM calls with shared state.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/workflow.md#_snippet_0

LANGUAGE: python
CODE:
```
class GenerateOutline(Node):
    def prep(self, shared): return shared["topic"]
    def exec(self, topic): return call_llm(f"Create a detailed outline for an article about {topic}")
    def post(self, shared, prep_res, exec_res): shared["outline"] = exec_res

class WriteSection(Node):
    def prep(self, shared): return shared["outline"]
    def exec(self, outline): return call_llm(f"Write content based on this outline: {outline}")
    def post(self, shared, prep_res, exec_res): shared["draft"] = exec_res

class ReviewAndRefine(Node):
    def prep(self, shared): return shared["draft"]
    def exec(self, draft): return call_llm(f"Review and improve this draft: {draft}")
    def post(self, shared, prep_res, exec_res): shared["final_article"] = exec_res

# Connect nodes
outline = GenerateOutline()
write = WriteSection()
review = ReviewAndRefine()

outline >> write >> review

# Create and run flow
writing_flow = Flow(start=outline)
shared = {"topic": "AI Safety"}
writing_flow.run(shared)
```

----------------------------------------

TITLE: Performing Web Search with DuckDuckGo Instant Answer API (Python)
DESCRIPTION: This snippet demonstrates how to use the DuckDuckGo Instant Answer API, which provides direct answers rather than traditional search results with URLs. It's a free API that typically requires no authentication. The code sends a GET request with the query and specifies JSON format, then prints the response.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/websearch.md#_snippet_2

LANGUAGE: Python
CODE:
```
import requests

query = "example"
url = "https://api.duckduckgo.com/"
params = {
    "q": query,
    "format": "json"
}

response = requests.get(url, params=params)
results = response.json()
print(results)
```

----------------------------------------

TITLE: Performing Web Search with Google Custom Search JSON API (Python)
DESCRIPTION: This snippet demonstrates how to use the Google Custom Search JSON API to perform a web search. It requires an API key and a Custom Search Engine ID (CX_ID) for authentication and to specify the search context. The code sends a GET request to the API endpoint with the query and credentials, then prints the JSON response.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/websearch.md#_snippet_0

LANGUAGE: Python
CODE:
```
import requests

API_KEY = "YOUR_API_KEY"
CX_ID = "YOUR_CX_ID"
query = "example"

url = "https://www.googleapis.com/customsearch/v1"
params = {
    "key": API_KEY,
    "cx": CX_ID,
    "q": query
}

response = requests.get(url, params=params)
results = response.json()
print(results)
```

----------------------------------------

TITLE: Performing Web Search with Bing Web Search API (Python)
DESCRIPTION: This Python example illustrates how to query the Bing Web Search API. It uses a subscription key for authentication, which is passed in the 'Ocp-Apim-Subscription-Key' header. The code constructs a GET request with the search query and prints the JSON results returned by the API.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/websearch.md#_snippet_1

LANGUAGE: Python
CODE:
```
import requests

SUBSCRIPTION_KEY = "YOUR_BING_API_KEY"
query = "example"

url = "https://api.bing.microsoft.com/v7.0/search"
headers = {"Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY}
params = {"q": query}

response = requests.get(url, headers=headers, params=params)
results = response.json()
print(results)
```

----------------------------------------

TITLE: Implementing Sentence-Based Text Chunking in Python
DESCRIPTION: This Python function performs sentence-based text chunking, grouping a specified maximum number of sentences into each chunk. It relies on the NLTK library for accurate sentence tokenization. A limitation of this approach is its potential inefficiency when handling very long sentences or paragraphs.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/chunking.md#_snippet_1

LANGUAGE: python
CODE:
```
import nltk

def sentence_based_chunk(text, max_sentences=2):
    sentences = nltk.sent_tokenize(text)
    chunks = []
    for i in range(0, len(sentences), max_sentences):
        chunks.append(" ".join(sentences[i : i + max_sentences]))
    return chunks
```

----------------------------------------

TITLE: Activating Pipenv Virtual Environment - Bash
DESCRIPTION: This command activates the virtual environment managed by Pipenv, allowing access to the project's installed dependencies and ensuring that Python commands run within the isolated environment.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-google-calendar/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
pipenv shell
```

----------------------------------------

TITLE: Visualizing a PocketFlow Graph
DESCRIPTION: This code snippet demonstrates how to visualize a PocketFlow graph using the `visualize_flow` function. It requires importing the function and your flow module, then calling the function with your flow object and a name for the flow. This will print a Mermaid diagram and generate a D3.js visualization.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/README.md#_snippet_0

LANGUAGE: Python
CODE:
```
from visualize import visualize_flow
from your_flow_module import your_flow

# Generate visualization
visualize_flow(your_flow, "Your Flow Name")
```

----------------------------------------

TITLE: Using Node and Flow Parameters in Python
DESCRIPTION: This example illustrates how to use `params` for per-node or per-flow configurations that are immutable during a node's run cycle. The `SummarizeFile` node accesses a `filename` from its `self.params` to fetch specific data from the shared store and write results back. It shows how parameters can be set directly on a node for testing or on a flow, with flow parameters overwriting node-specific ones.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/communication.md#_snippet_2

LANGUAGE: Python
CODE:
```
# 1) Create a Node that uses params
class SummarizeFile(Node):
    def prep(self, shared):
        # Access the node's param
        filename = self.params["filename"]
        return shared["data"].get(filename, "")

    def exec(self, prep_res):
        prompt = f"Summarize: {prep_res}"
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        filename = self.params["filename"]
        shared["summary"][filename] = exec_res
        return "default"

# 2) Set params
node = SummarizeFile()

# 3) Set Node params directly (for testing)
node.set_params({"filename": "doc1.txt"})
node.run(shared)

# 4) Create Flow
flow = Flow(start=node)

# 5) Set Flow params (overwrites node params)
flow.set_params({"filename": "doc2.txt"})
flow.run(shared)  # The node summarizes doc2, not doc1
```

----------------------------------------

TITLE: Overriding exec_fallback for Graceful Error Handling in Python
DESCRIPTION: This snippet shows the default implementation of `exec_fallback`, which simply re-raises the exception. Users can override this method to provide a custom fallback result instead of letting the exception propagate, ensuring graceful error handling after all retries have been exhausted.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/node.md#_snippet_2

LANGUAGE: Python
CODE:
```
def exec_fallback(self, prep_res, exc):
    raise exc
```

----------------------------------------

TITLE: Set OpenAI API Key Environment Variable
DESCRIPTION: Sets the `OPENAI_API_KEY` environment variable with your OpenAI API key. This allows the application to authenticate with the OpenAI API. Replace `"your-api-key-here"` with your actual key.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-structured-output/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Setting OpenAI API Key
DESCRIPTION: This command sets the `OPENAI_API_KEY` environment variable, which is required for the content analysis functionality that uses the GPT-4 API.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-crawler/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY='your-api-key'
```

----------------------------------------

TITLE: Setting OpenAI API Key - Bash
DESCRIPTION: This snippet demonstrates how to set the OpenAI API key as an environment variable in a Bash shell. This is a common prerequisite for applications interacting with OpenAI services, ensuring secure access without hardcoding credentials directly into the main application logic.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-chat/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Set OpenAI API Key (Bash)
DESCRIPTION: Sets the OPENAI_API_KEY environment variable required for accessing OpenAI services used by the application's utility scripts.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-voice-chat/README.md#_snippet_0

LANGUAGE: Bash
CODE:
```
export OPENAI_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Setting OpenAI API Key - Bash
DESCRIPTION: This command sets the `OPENAI_API_KEY` environment variable, which is required for authenticating with the OpenAI API. Users can also update the API key directly within the `utils.py` file if preferred.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-rag/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Implementing Nested BatchFlow Structure in Python
DESCRIPTION: This code defines three components: an outer BatchFlow (DirectoryBatchFlow) providing directory paths, an inner BatchFlow (FileBatchFlow) providing filenames within those directories, and a processing Node (ProcessFile) that uses parameters from both levels. It shows how to instantiate and connect these components to form a nested flow and execute it.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/batch.md#_snippet_2

LANGUAGE: python
CODE:
```
class FileBatchFlow(BatchFlow):
    def prep(self, shared):
        # Access directory from params (set by parent)
        directory = self.params["directory"]
        # e.g., files = ["file1.txt", "file2.txt", ...]
        files = [f for f in os.listdir(directory) if f.endswith(".txt")]
        return [{"filename": f} for f in files]

class DirectoryBatchFlow(BatchFlow):
    def prep(self, shared):
        directories = [ "/path/to/dirA", "/path/to/dirB"]
        return [{"directory": d} for d in directories]

# The actual processing node
class ProcessFile(Node):
    def prep(self, shared):
        # Access both directory and filename from params
        directory = self.params["directory"]  # From outer batch
        filename = self.params["filename"]    # From inner batch
        full_path = os.path.join(directory, filename)
        return full_path
        
    def exec(self, full_path):
        # Process the file...
        return f"Processed {full_path}"
        
    def post(self, shared, prep_res, exec_res):
        # Store results, perhaps indexed by path
        if "results" not in shared:
            shared["results"] = {}
        shared["results"][prep_res] = exec_res
        return "default"

# Set up the nested batch structure
process_node = ProcessFile()
inner_flow = FileBatchFlow(start=process_node)
outer_flow = DirectoryBatchFlow(start=inner_flow)

# Run it
outer_flow.run(shared)
```

----------------------------------------

TITLE: Processing Questions with Agent Flow in Python
DESCRIPTION: This snippet defines the main execution logic for the PocketFlow application. It initializes a default question, allows overriding it via command-line arguments (prefixed with `--`), creates an agent flow using `create_agent_flow()`, processes the question through this flow, and finally prints the obtained answer. It depends on the `sys` module for argument parsing and an external `create_agent_flow` function.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/demo.ipynb#_snippet_8

LANGUAGE: Python
CODE:
```
import sys

def main():
    """Simple function to process a question."""
    # Default question
    default_question = "Who won the Nobel Prize in Physics 2024?"

    # Get question from command line if provided with --
    question = default_question
    for arg in sys.argv[1:]:
        if arg.startswith("--"):
            question = arg[2:]
            break

    # Create the agent flow
    agent_flow = create_agent_flow()

    # Process the question
    shared = {"question": question}
    print(f"🤔 Processing question: {question}")
    agent_flow.run(shared)
    print("\n🎯 Final Answer:")
    print(shared.get("answer", "No answer found"))

main()
```

----------------------------------------

TITLE: Testing LLM and Web Search Features (Python)
DESCRIPTION: This command executes the `utils.py` script to perform a quick check of the LLM call and web search functionalities. It verifies if the OpenAI API key is working and if external services can be accessed, ensuring the core components are operational.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-supervisor/README.md#_snippet_2

LANGUAGE: python
CODE:
```
python utils.py
```

----------------------------------------

TITLE: Call DeepSeek API (Python)
DESCRIPTION: Provides an example of calling the DeepSeek API using the `openai` library with a custom `base_url`. It sends a user prompt to the `deepseek-chat` model and returns the chat completion response. Requires the `openai` library, a DeepSeek API key, and sets the appropriate base URL.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/llm.md#_snippet_5

LANGUAGE: python
CODE:
```
def call_llm(prompt):
    from openai import OpenAI
    client = OpenAI(api_key="YOUR_DEEPSEEK_API_KEY", base_url="https://api.deepseek.com")
    r = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}]
    )
    return r.choices[0].message.content
```

----------------------------------------

TITLE: Setting Anthropic API Key
DESCRIPTION: Sets the `ANTHROPIC_API_KEY` environment variable, which is required for the system to authenticate and make requests to the Anthropic LLM API.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-code-generator/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export ANTHROPIC_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Designing Shared Store in PocketFlow (Python)
DESCRIPTION: This snippet illustrates a basic in-memory shared store design using a Python dictionary, a core principle for data communication in PocketFlow. It demonstrates how to structure nested data, such as user information and context, and initialize an empty dictionary for results. This design is suitable for simple systems or as a starting point before migrating to a database for persistence.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/guide.md#_snippet_2

LANGUAGE: Python
CODE:
```
shared = {
    "user": {
        "id": "user123",
        "context": {                # Another nested dict
            "weather": {"temp": 72, "condition": "sunny"},
            "location": "San Francisco"
        }
    },
    "results": {}                   # Empty dict to store outputs
}
```

----------------------------------------

TITLE: Call Google Generative AI API (Python)
DESCRIPTION: Provides an example of calling the Google Generative AI API (PaLM API) using the `google-generativeai` library. It sends content to the `gemini-2.0-flash-001` model and returns the generated text response. Requires the `google-generativeai` library and an API key.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/llm.md#_snippet_2

LANGUAGE: python
CODE:
```
def call_llm(prompt):
    from google import genai
    client = genai.Client(api_key='GEMINI_API_KEY')
    response = client.models.generate_content(
        model='gemini-2.0-flash-001',
        contents=prompt
    )
    return response.text
```

----------------------------------------

TITLE: Installing Dependencies and Running Application (Bash)
DESCRIPTION: This snippet provides commands to install the necessary Python dependencies from `requirements.txt` and then run the main application script `main.py`. These steps are essential to set up and launch the PocketFlow chat application.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-chat-memory/README.md#_snippet_1

LANGUAGE: Bash
CODE:
```
pip install -r requirements.txt
python main.py
```

----------------------------------------

TITLE: Establishing Server-Sent Events (SSE) Connection for Progress Updates - JavaScript
DESCRIPTION: This function establishes a Server-Sent Events (SSE) connection to receive real-time progress updates for a given job ID. It defines `onmessage` to parse and handle incoming data via `handleProgressUpdate` and `onerror` to manage connection errors and display user feedback.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/static/progress.html#_snippet_2

LANGUAGE: JavaScript
CODE:
```
function connectToProgress() {
  const eventSource = new EventSource(`/progress/${jobId}`);
  eventSource.onmessage = function(event) {
    try {
      const data = JSON.parse(event.data);
      handleProgressUpdate(data);
    } catch (error) {
      console.error('Error parsing SSE data:', error);
    }
  };
  eventSource.onerror = function(error) {
    console.error('SSE connection error:', error);
    showError('Connection lost. Please refresh the page.');
    eventSource.close();
  };
}
```

----------------------------------------

TITLE: Defining Streamlit Session State for Image Generation Workflow - Python
DESCRIPTION: This Python snippet defines the structure of `st.session_state` used as shared memory for the PocketFlow image generation workflow. It stores user input, current workflow stage, error messages, and processing data like the generated image and final approved result. This eliminates the need for separate data structures and maintains state across user interactions.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-streamlit-fsm/docs/design.md#_snippet_0

LANGUAGE: Python
CODE:
```
st.session_state = {
    # User input and workflow state
    "task_input": "user's text prompt for image generation",
    "stage": "current workflow stage (initial_input/user_feedback/final)",
    "error_message": "any error messages for user feedback",
    
    # Processing data
    "input_used_by_process": "prompt used for generation",
    "generated_image": "base64 encoded image data",
    "final_result": "final approved image data",
    
    # Streamlit built-in keys (managed automatically)
    # "_streamlit_*": various internal streamlit state
}
```

----------------------------------------

TITLE: Synthesizing Speech with Amazon Polly (Python)
DESCRIPTION: This snippet demonstrates how to use the boto3 library to synthesize speech using Amazon Polly. It initializes the Polly client with AWS credentials, synthesizes a given text into an MP3 audio stream, and saves the audio content to a file.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/text_to_speech.md#_snippet_0

LANGUAGE: Python
CODE:
```
import boto3

polly = boto3.client("polly", region_name="us-east-1",
                     aws_access_key_id="YOUR_AWS_ACCESS_KEY_ID",
                     aws_secret_access_key="YOUR_AWS_SECRET_ACCESS_KEY")

resp = polly.synthesize_speech(
    Text="Hello from Polly!",
    OutputFormat="mp3",
    VoiceId="Joanna"
)

with open("polly.mp3", "wb") as f:
    f.write(resp["AudioStream"].read())
```

----------------------------------------

TITLE: Running the FastAPI Application Server
DESCRIPTION: This command starts the FastAPI web server by executing the `main.py` script. Once running, the application will be accessible via a web browser at the specified local address.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Initializing Flow with a Start Node in PocketFlow
DESCRIPTION: This snippet shows how to initialize a 'Flow' object in PocketFlow by specifying a starting node ('node_a'). This sets the entry point for the computational graph.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_9

LANGUAGE: Python
CODE:
```
Flow(start=node_a)
```

----------------------------------------

TITLE: Summarizing Documents into Bullet Points (YAML)
DESCRIPTION: This YAML snippet illustrates a structured summary output, where a document's key points are presented as a list of bullet points. This format is useful for concise overviews generated by an LLM.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/structure.md#_snippet_1

LANGUAGE: yaml
CODE:
```
summary:
  - This product is easy to use.
  - It is cost-effective.
  - Suitable for all skill levels.
```

----------------------------------------

TITLE: Implementing BatchFlow for Iterating Over Parameters - Python
DESCRIPTION: This example shows how to use a BatchFlow to run a child Flow multiple times, each with a different set of parameters. The BatchFlow's `prep` method returns a list of parameter dictionaries. The child Flow's nodes access these parameters via `self.params` instead of the shared store, allowing independent processing for each parameter set (e.g., summarizing multiple files).
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/batch.md#_snippet_1

LANGUAGE: python
CODE:
```
class SummarizeAllFiles(BatchFlow):
    def prep(self, shared):
        # IMPORTANT: Return a list of param dictionaries (not data for processing)
        filenames = list(shared["data"].keys())  # e.g., ["file1.txt", "file2.txt", ...]
        return [{"filename": fn} for fn in filenames]

# Child node that accesses filename from params, not shared store
class LoadFile(Node):
    def prep(self, shared):
        # Access filename from params (not from shared)
        filename = self.params["filename"]  # Important! Use self.params, not shared
        return filename
        
    def exec(self, filename):
        with open(filename, 'r') as f:
            return f.read()
            
    def post(self, shared, prep_res, exec_res):
        # Store file content in shared
        shared["current_file_content"] = exec_res
        return "default"

# Summarize node that works on the currently loaded file
class Summarize(Node):
    def prep(self, shared):
        return shared["current_file_content"]
        
    def exec(self, content):
        prompt = f"Summarize this file in 50 words: {content}"
        return call_llm(prompt)
        
    def post(self, shared, prep_res, exec_res):
        # Store summary in shared, indexed by current filename
        filename = self.params["filename"]  # Again, using params
        if "summaries" not in shared:
            shared["summaries"] = {}
        shared["summaries"][filename] = exec_res
        return "default"

# Create a per-file flow
load_file = LoadFile()
summarize = Summarize()
load_file >> summarize
summarize_file = Flow(start=load_file)

# Wrap in a BatchFlow to process all files
summarize_all_files = SummarizeAllFiles(start=summarize_file)
summarize_all_files.run(shared)
```

----------------------------------------

TITLE: Handling Topic Selection and Article Generation Form Submission - JavaScript
DESCRIPTION: This JavaScript snippet provides functionality for setting the topic input field from popular tags and handling the form submission for article generation. It prevents default form submission, shows a loading state, sends an asynchronous POST request to '/start-job', and redirects to a progress page upon success or displays an error.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/static/index.html#_snippet_1

LANGUAGE: javascript
CODE:
```
function setTopic(topic) { document.getElementById('topic').value = topic; } document.getElementById('articleForm').addEventListener('submit', async function(e) { e.preventDefault(); const submitBtn = document.querySelector('.submit-btn'); const originalText = submitBtn.textContent; submitBtn.textContent = 'Starting...'; submitBtn.disabled = true; try { const formData = new FormData(this); const response = await fetch('/start-job', { method: 'POST', body: formData }); const result = await response.json(); if (response.ok) { window.location.href = `/progress.html?job_id=${result.job_id}&topic=${encodeURIComponent(result.topic)}`; } else { throw new Error('Failed to start job'); } } catch (error) { alert('Error starting job: ' + error.message); submitBtn.textContent = originalText; submitBtn.disabled = false; } });
```

----------------------------------------

TITLE: PocketFlow Article Workflow Diagram
DESCRIPTION: This Mermaid diagram visualizes the sequential flow of the article writing process. It shows three main nodes: 'Generate Outline', 'Write Content', and 'Apply Style', illustrating their execution order.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-workflow/README.md#_snippet_4

LANGUAGE: mermaid
CODE:
```
graph LR
    Outline[Generate Outline] --> Write[Write Content]
    Write --> Style[Apply Style]
```

----------------------------------------

TITLE: Synthesizing Speech with Azure TTS (Python)
DESCRIPTION: This snippet demonstrates text-to-speech conversion using the Azure Cognitive Services Speech SDK. It configures the speech service with a subscription key and region, sets up an audio output file, and then uses a SpeechSynthesizer to speak the provided text asynchronously.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/text_to_speech.md#_snippet_2

LANGUAGE: Python
CODE:
```
import azure.cognitiveservices.speech as speechsdk

speech_config = speechsdk.SpeechConfig(
    subscription="AZURE_KEY", region="AZURE_REGION")
audio_cfg = speechsdk.audio.AudioConfig(filename="azure_tts.wav")

synthesizer = speechsdk.SpeechSynthesizer(
    speech_config=speech_config,
    audio_config=audio_cfg
)

synthesizer.speak_text_async("Hello from Azure TTS!").get()
```

----------------------------------------

TITLE: Implementing BatchNode for Chunk Processing - Python
DESCRIPTION: This example demonstrates how to use a BatchNode to process a large input (a file's content) in smaller chunks. The `prep` method splits the content into chunks, `exec` processes each chunk individually (e.g., summarizes it), and `post` combines the results from all chunks.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/batch.md#_snippet_0

LANGUAGE: python
CODE:
```
class MapSummaries(BatchNode):
    def prep(self, shared):
        # Suppose we have a big file; chunk it
        content = shared["data"]
        chunk_size = 10000
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        return chunks

    def exec(self, chunk):
        prompt = f"Summarize this chunk in 10 words: {chunk}"
        summary = call_llm(prompt)
        return summary

    def post(self, shared, prep_res, exec_res_list):
        combined = "\n".join(exec_res_list)
        shared["summary"] = combined
        return "default"

map_summaries = MapSummaries()
flow = Flow(start=map_summaries)
flow.run(shared)
```

----------------------------------------

TITLE: Generating Embeddings with Azure OpenAI (Python)
DESCRIPTION: This Python snippet illustrates how to generate text embeddings using Azure OpenAI. It configures the OpenAI client with Azure-specific details like API type, base URL, version, and API key, then calls the `Embedding.create` method with the specified engine and input text to retrieve the embedding vector.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/embedding.md#_snippet_1

LANGUAGE: Python
CODE:
```
import openai

openai.api_type = "azure"
openai.api_base = "https://YOUR_RESOURCE_NAME.openai.azure.com"
openai.api_version = "2023-03-15-preview"
openai.api_key = "YOUR_AZURE_API_KEY"

resp = openai.Embedding.create(engine="ada-embedding", input="Hello world")
vec = resp["data"][0]["embedding"]
print(vec)
```

----------------------------------------

TITLE: Joke Generator Workflow Flowchart (Mermaid)
DESCRIPTION: This Mermaid diagram visualizes the high-level workflow of the joke generator application. It illustrates the sequence of nodes: GetTopicNode for input, GenerateJokeNode for joke creation, and GetFeedbackNode for user approval, with a loop back to GenerateJokeNode if the joke is disapproved.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-cmd-hitl/docs/design.md#_snippet_0

LANGUAGE: mermaid
CODE:
```
flowchart TD
    GetTopic[GetTopicNode] --> GenerateJoke[GenerateJokeNode]
    GenerateJoke --> GetFeedback[GetFeedbackNode]
    GetFeedback -- "Approve" --> Z((End))
    GetFeedback -- "Disapprove" --> GenerateJoke
```

----------------------------------------

TITLE: Testing LLM Utility Script
DESCRIPTION: This command runs the `call_llm.py` utility script directly. It's used to verify that the LLM integration and API key setup are working correctly before running the main application.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-cmd-hitl/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python utils/call_llm.py
```

----------------------------------------

TITLE: Setting OpenAI API Key in Bash
DESCRIPTION: This snippet sets the `OPENAI_API_KEY` environment variable, which is required for authenticating with the OpenAI API. Replace `"your-openai-api-key"` with your actual API key.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-streamlit-fsm/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY="your-openai-api-key"
```

----------------------------------------

TITLE: Setting OpenAI API Key Environment Variable
DESCRIPTION: This command sets the `OPENAI_API_KEY` environment variable. This key is crucial for the application to authenticate and interact with the OpenAI API for large language model (LLM) operations.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY=your_api_key_here
```

----------------------------------------

TITLE: Setting OpenAI API Key Environment Variable (bash)
DESCRIPTION: Sets the `OPENAI_API_KEY` environment variable to your specific OpenAI API key. This allows the application to authenticate with the OpenAI API. Replace `your_api_key_here` with your actual key.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-pdf-vision/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY=your_api_key_here
```

----------------------------------------

TITLE: Setting OpenAI API Key (Bash)
DESCRIPTION: This command sets the `OPENAI_API_KEY` environment variable, which is required for the project to authenticate with the OpenAI API. Users must replace `"your-api-key-here"` with their actual API key to enable LLM interactions.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-supervisor/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Installing Dependencies (Bash)
DESCRIPTION: Installs the necessary Python packages listed in `requirements.txt` to run the Taboo game application. This is the first step to set up the project environment.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-multi-agent/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: FastAPI WebSocket Chat Flow Diagram - Mermaid
DESCRIPTION: This Mermaid flowchart visualizes the high-level data flow for the real-time AI chatbot interface. It illustrates how user interactions from the browser are routed through a FastAPI WebSocket endpoint, processed by a PocketFlow Streaming Chat AsyncNode, and then streamed back to the user, ensuring bidirectional communication.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-websocket/docs/design.md#_snippet_0

LANGUAGE: Mermaid
CODE:
```
flowchart TD
    user((User Browser)) --> websocket(FastAPI WebSocket)
    websocket --> flow[Streaming Chat AsyncNode]
    flow --> websocket
    websocket --> user
    
    style user fill:#e1f5fe
    style websocket fill:#f3e5f5
    style flow fill:#e8f5e8,stroke:#4caf50,stroke-width:3px
```

----------------------------------------

TITLE: Installing Project Dependencies - Bash
DESCRIPTION: This command installs all required Python packages listed in the `requirements.txt` file. It is the initial step to set up the project's environment before running the translation process.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Installing Project Dependencies (Bash)
DESCRIPTION: Installs the necessary Python packages listed in the `requirements.txt` file. This command ensures that all required libraries and dependencies for the project are properly set up in the environment before execution.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-majority-vote/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Customizing and Running Summarization Flow
DESCRIPTION: This Python snippet demonstrates how to provide custom text for summarization by modifying the 'data' key in the `shared` dictionary. It then runs the PocketFlow `flow` with this data and prints the resulting summary stored in the 'summary' key.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-node/README.md#_snippet_4

LANGUAGE: python
CODE:
```
shared = {"data": "Your text to summarize here..."}
flow.run(shared)
print("Summary:", shared["summary"])
```

----------------------------------------

TITLE: Defining a Shared Store in Python
DESCRIPTION: This snippet illustrates the typical structure of a shared store, which is an in-memory dictionary. It serves as a global data structure for nodes to read and write data, summaries, and configurations. It can also hold references to external resources like file handlers or database connections.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/communication.md#_snippet_0

LANGUAGE: Python
CODE:
```
shared = {"data": {}, "summary": {}, "config": {...}, ...}
```

----------------------------------------

TITLE: Implementing SuggestRecipe AsyncNode in Python
DESCRIPTION: This `AsyncNode` processes the fetched recipes using an LLM. The `exec_async` method makes an asynchronous call to `call_llm_async`, instructing it to choose the best recipe from the input list and returning the LLM's suggestion.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-async-basic/README.md#_snippet_1

LANGUAGE: Python
CODE:
```
async def exec_async(self, recipes):
    # Async LLM call
    suggestion = await call_llm_async(
        f"Choose best recipe from: {recipes}"
    )
    return suggestion
```

----------------------------------------

TITLE: Set Anthropic API Key
DESCRIPTION: Sets the Anthropic API key as an environment variable. This key is required to authenticate with the Anthropic API for text translation.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-parallel-batch/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export ANTHROPIC_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Running the PocketFlow OpenAI Embeddings Example
DESCRIPTION: This command executes the main Python script, `main.py`, which orchestrates the entire example. It loads the API key, initializes the PocketFlow node, processes sample text, generates embeddings, and displays the results, demonstrating the end-to-end integration.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-embeddings/README.md#_snippet_4

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Defining Shared Memory Structure in Python
DESCRIPTION: This Python snippet defines the initial structure for the shared memory, represented as a dictionary. It illustrates how data will be organized and accessed across different nodes in the project, with 'key' holding 'value'.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-hello-world/docs/design.md#_snippet_1

LANGUAGE: python
CODE:
```
shared = {
    "key": "value"
}
```

----------------------------------------

TITLE: Generating Embeddings with Cohere (Python)
DESCRIPTION: This Python snippet demonstrates how to generate text embeddings using the Cohere API. It initializes the Cohere client with an API key, calls the `embed` method with the input text, and then extracts and prints the first embedding vector from the response.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/embedding.md#_snippet_4

LANGUAGE: Python
CODE:
```
import cohere

co = cohere.Client("YOUR_API_KEY")
resp = co.embed(texts=["Hello world"])
vec = resp.embeddings[0]
print(vec)
```

----------------------------------------

TITLE: Multi-Agent Communication Flow (Mermaid)
DESCRIPTION: Illustrates the asynchronous communication pattern between the AsyncHinter and AsyncGuesser nodes via a central Message Queue, which facilitates non-blocking interactions in the Taboo game.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-multi-agent/README.md#_snippet_3

LANGUAGE: mermaid
CODE:
```
flowchart LR
    AsyncHinter[AsyncHinter Node] <--> MessageQueue{Message Queue}
    MessageQueue <--> AsyncGuesser[AsyncGuesser Node]
```

----------------------------------------

TITLE: Synthesizing Speech with ElevenLabs (Python)
DESCRIPTION: This snippet demonstrates how to interact with the ElevenLabs API for text-to-speech conversion using the requests library. It constructs the API URL and headers with an API key, prepares the JSON payload with text and voice settings, sends a POST request, and saves the received audio content to a file.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/text_to_speech.md#_snippet_4

LANGUAGE: Python
CODE:
```
import requests

api_key = "ELEVENLABS_KEY"
voice_id = "ELEVENLABS_VOICE"
url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
headers = {"xi-api-key": api_key, "Content-Type": "application/json"}

json_data = {
    "text": "Hello from ElevenLabs!",
    "voice_settings": {"stability": 0.75, "similarity_boost": 0.75}
}

resp = requests.post(url, headers=headers, json=json_data)

with open("elevenlabs.mp3", "wb") as f:
    f.write(resp.content)
```

----------------------------------------

TITLE: Verify OpenAI API Key Setup
DESCRIPTION: Runs the `utils.py` script to perform a quick check and ensure that the OpenAI API key is correctly set up and working. This helps confirm connectivity before running the main application.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-structured-output/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python utils.py
```

----------------------------------------

TITLE: Representing Dialogue with Block Literal (YAML)
DESCRIPTION: This YAML snippet demonstrates using a block literal (`|`) to represent multi-line strings without needing to escape internal quotes or newlines. This makes the output more natural and easier for LLMs to generate accurately compared to JSON.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/structure.md#_snippet_5

LANGUAGE: yaml
CODE:
```
dialogue: |
  Alice said: "Hello Bob.
  How are you?
  I am good."
```

----------------------------------------

TITLE: Running a Flow in PocketFlow
DESCRIPTION: This snippet demonstrates how to execute a previously defined 'Flow' instance, passing a 'shared' object that likely contains global state or data accessible throughout the flow's execution.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_10

LANGUAGE: Python
CODE:
```
flow.run(shared)
```

----------------------------------------

TITLE: Verifying API Key and Environment Setup
DESCRIPTION: This command executes a utility script ('utils.py') to perform a quick check. It verifies that the API key is correctly set and that the environment is properly configured for the project to interact with the LLM services.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_2

LANGUAGE: Bash
CODE:
```
python utils.py
```

----------------------------------------

TITLE: Verifying OpenAI API Key - Python
DESCRIPTION: This command executes the `utils.py` script, which performs a quick check to ensure that the configured OpenAI API key is working correctly. It's a prerequisite step to confirm connectivity before running the main application.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-rag/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
python utils.py
```

----------------------------------------

TITLE: Client-side Task Submission and SSE Handling - JavaScript
DESCRIPTION: This code block initializes DOM element references, sets up event listeners for user interactions (submit, approve, reject), and defines asynchronous functions to handle task submission via POST request, establish and manage an SSE connection for real-time status updates, process incoming SSE messages, update the UI accordingly, and send feedback via another POST request. It includes error handling and UI state management (disabling buttons, showing/hiding sections).
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-hitl/templates/index.html#_snippet_0

LANGUAGE: javascript
CODE:
```
const taskInput = document.getElementById('task-input');
const submitButton = document.getElementById('submit-button');
const taskIdDisplay = document.getElementById('task-id-display');
const statusDisplay = document.getElementById('status-display');
const reviewSection = document.getElementById('review-section');
const reviewOutput = document.getElementById('review-output');
const approveButton = document.getElementById('approve-button');
const rejectButton = document.getElementById('reject-button');
const resultSection = document.getElementById('result-section');
const finalResult = document.getElementById('final-result');

let currentTaskId = null;
let eventSource = null;

submitButton.addEventListener('click', handleSubmit);
approveButton.addEventListener('click', () => handleFeedback('approved'));
rejectButton.addEventListener('click', () => handleFeedback('rejected'));

async function handleSubmit() {
  const data = taskInput.value.trim();
  if (!data) return alert('Input is empty.');

  resetUI();
  statusDisplay.textContent = 'Submitting...';
  submitButton.disabled = true;

  try {
    const response = await fetch('/submit', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ data: data })
    });

    if (!response.ok) throw new Error(`Submit failed: ${response.status}`);

    const result = await response.json();
    currentTaskId = result.task_id;
    taskIdDisplay.textContent = `Task ID: ${currentTaskId}`;

    startSSEListener(currentTaskId);

  } catch (error) {
    console.error('Submit error:', error);
    statusDisplay.textContent = `Submit Error: ${error.message}`;
    resetUI();
  } finally {
    submitButton.disabled = false;
  }
}

function startSSEListener(taskId) {
  closeSSEListener(); // Close existing connection
  eventSource = new EventSource(`/stream/${taskId}`);
  eventSource.onmessage = handleSSEMessage;
  eventSource.onerror = handleSSEError;
  eventSource.onopen = () => console.log(`SSE connected for ${taskId}`);
}

function handleSSEMessage(event) {
  console.log("SSE data:", event.data);
  try {
    const data = JSON.parse(event.data);
    updateUI(data);
  } catch (e) {
    console.error("SSE parse error:", e);
  }
}

function handleSSEError(error) {
  console.error("SSE Error:", error);
  statusDisplay.textContent = "Status stream error. Connection closed.";
  closeSSEListener();
}

function closeSSEListener() {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
    console.log("SSE connection closed.");
  }
}

function updateUI(data) {
  // Always update main status
  statusDisplay.textContent = `Status: ${data.status || 'Unknown'}`;

  // Hide sections, then show relevant one
  reviewSection.classList.add('hidden');
  resultSection.classList.add('hidden');

  approveButton.disabled = false; // Re-enable by default
  rejectButton.disabled = false;

  switch(data.status) {
    case 'waiting_for_review':
      reviewOutput.textContent = data.output_to_review || '';
      reviewSection.classList.remove('hidden');
      break;
    case 'processing_feedback':
      approveButton.disabled = true; // Disable while processing
      rejectButton.disabled = true;
      break;
    case 'completed':
      finalResult.textContent = data.final_result || '';
      resultSection.classList.remove('hidden');
      closeSSEListener();
      break;
    case 'failed':
    case 'feedback_error':
      statusDisplay.textContent = `Status: ${data.status} - ${data.error || 'Unknown error'}`;
      closeSSEListener();
      break;
    case 'finished_incomplete':
      statusDisplay.textContent = `Status: Flow finished unexpectedly.`;
      closeSSEListener();
      break;
    case 'stream_closed':
      // Server closed the stream gracefully (usually after completed/failed)
      // This check prevents overwriting a final status if the stream closes after it's set
      // Assumes 'tasks' object exists globally or is accessible, which isn't shown here.
      // A more robust check might involve the current UI status or a local state.
      // For this snippet, we'll simplify and just show the message if not already completed/failed.
      // NOTE: The original code references 'tasks[currentTaskId]?.status' which is not defined in this snippet.
      // Assuming a simplified check or relying on the fact that updateUI is called before stream_closed status.
      // If the status is NOT one of the final states, display the connection closed message.
      // This simplified logic might need adjustment based on the full application context.
      if (!statusDisplay.textContent.includes('completed') && !statusDisplay.textContent.includes('failed') && !statusDisplay.textContent.includes('finished_incomplete')) {
           statusDisplay.textContent = "Status: Connection closed by server.";
      }
      closeSSEListener();
      break;
    case 'pending':
    case 'running':
      // Just update status text, wait for next message
      break;
  }
}

async function handleFeedback(feedbackValue) {
  if (!currentTaskId) return;

  approveButton.disabled = true;
  rejectButton.disabled = true;
  statusDisplay.textContent = `Sending ${feedbackValue}...`; // Optimistic UI update

  try {
    const response = await fetch(`/feedback/${currentTaskId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ feedback: feedbackValue })
    });

    if (!response.ok) {
      // Rely on SSE for status change or error reporting
      const errorData = await response.json().catch(()=>({error: `Feedback failed: ${response.status}`}));
      throw new Error(errorData.error);
    }

    console.log(`Feedback ${feedbackValue} POST successful.`);
    // Successful POST - wait for SSE to update status to 'processing', then 'running' etc.

  } catch (error) {
    console.error('Feedback error:', error);
    statusDisplay.textContent = `Feedback Error: ${error.message}`;
    // Re-enable buttons if feedback POST failed
    approveButton.disabled = false;
    rejectButton.disabled = false;
  }
}

function resetUI() {
  closeSSEListener();
  currentTaskId = null;
  taskIdDisplay.textContent = 'Task ID: N/A';
  statusDisplay.textContent = 'Status: Idle'; // Assuming 'Idle' is the initial state
  reviewSection.classList.add('hidden');
  resultSection.classList.add('hidden');
  reviewOutput.textContent = '';
  finalResult.textContent = '';
  approveButton.disabled = false;
  rejectButton.disabled = false;
}
```

----------------------------------------

TITLE: Synthesizing Speech with Google Cloud TTS (Python)
DESCRIPTION: This code illustrates how to use the Google Cloud Text-to-Speech API to convert text into speech. It sets up the client, defines the input text, voice parameters, and audio configuration, then synthesizes the speech and saves the resulting MP3 audio.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/text_to_speech.md#_snippet_1

LANGUAGE: Python
CODE:
```
from google.cloud import texttospeech

client = texttospeech.TextToSpeechClient()
input_text = texttospeech.SynthesisInput(text="Hello from Google Cloud TTS!")
voice = texttospeech.VoiceSelectionParams(language_code="en-US")
audio_cfg = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

resp = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_cfg)

with open("gcloud_tts.mp3", "wb") as f:
    f.write(resp.audio_content)
```

----------------------------------------

TITLE: Mermaid Diagram for Human-in-the-Loop Workflow
DESCRIPTION: Visual representation of the human-in-the-loop workflow using Mermaid syntax, showing the flow between processing, review, and result nodes with conditional branching based on feedback.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-hitl/docs/design.md#_snippet_0

LANGUAGE: mermaid
CODE:
```
flowchart TD
    Process[Process Task] -- "default" --> Review{Wait for Feedback}
    Review -- "approved" --> Result[Final Result]
    Review -- "rejected" --> Process
```

----------------------------------------

TITLE: Define D3.js Drag Handlers
DESCRIPTION: These functions implement the standard drag behavior for nodes in a D3.js force-directed simulation. `dragstarted` fixes the node's position and restarts the simulation, `dragged` updates the fixed position, and `dragended` releases the fixed position.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_15

LANGUAGE: javascript
CODE:
```
}); // Drag functions function dragstarted(event, d) {
 if (!event.active) simulation.alphaTarget(0.3).restart();
 d.fx = d.x;
 d.fy = d.y;
 } function dragged(event, d) {
 d.fx = event.x;
 d.fy = event.y;
 } function dragended(event, d) {
 if (!event.active) simulation.alphaTarget(0);
 d.fx = null;
 d.fy = null;
 }
```

----------------------------------------

TITLE: Synthesizing Speech with IBM Watson TTS (Python)
DESCRIPTION: This example shows how to use the IBM Watson Text to Speech service. It initializes the service with an IAM authenticator and service URL, then synthesizes text into an MP3 audio stream using a specified voice, and finally saves the audio content to a file.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/text_to_speech.md#_snippet_3

LANGUAGE: Python
CODE:
```
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

auth = IAMAuthenticator("IBM_API_KEY")
service = TextToSpeechV1(authenticator=auth)
service.set_service_url("IBM_SERVICE_URL")

resp = service.synthesize(
    "Hello from IBM Watson!",
    voice="en-US_AllisonV3Voice",
    accept="audio/mp3"
).get_result()

with open("ibm_tts.mp3", "wb") as f:
    f.write(resp.content)
```

----------------------------------------

TITLE: Shared Store Structure for WebSocket Chat - Python
DESCRIPTION: This Python dictionary defines the structure of the shared store used within the PocketFlow AsyncNode. It holds the WebSocket connection object, the current user's message, and the complete conversation history, minimizing data redundancy across node steps.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-websocket/docs/design.md#_snippet_1

LANGUAGE: Python
CODE:
```
shared = {
    "websocket": None,           # WebSocket connection object
    "user_message": "",          # Current user message
    "conversation_history": []   # List of message history with roles
}
```

----------------------------------------

TITLE: Verifying OpenAI API Key Setup
DESCRIPTION: Runs the `utils.py` script to perform a quick check of the OpenAI API key setup. If the key is valid and accessible, the script should execute successfully, typically by printing a short joke as mentioned in the text.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-text2sql/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
python utils.py
```

----------------------------------------

TITLE: Generating Embeddings with Jina AI (Python)
DESCRIPTION: This Python snippet demonstrates how to generate text embeddings using the Jina AI API. It sends a POST request to the Jina embedding endpoint with the input text, a specified model, and an authorization token, then parses the JSON response to extract and print the embedding vector.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/embedding.md#_snippet_6

LANGUAGE: Python
CODE:
```
import requests

url = "https://api.jina.ai/v2/embed"
headers = {"Authorization": "Bearer YOUR_JINA_TOKEN"}
payload = {"data": ["Hello world"], "model": "jina-embeddings-v3"}
res = requests.post(url, headers=headers, json=payload)
vec = res.json()["data"][0]["embedding"]
print(vec)
```

----------------------------------------

TITLE: Run Parallel Translation Process
DESCRIPTION: Executes the main script to perform parallel translation of the README file into multiple languages. This script leverages PocketFlow's AsyncParallelBatchNode for concurrent translation.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-parallel-batch/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Running Text-to-SQL Workflow with Custom Query (Quoted Argument)
DESCRIPTION: Executes the main script `main.py` with a custom natural language query provided as a single command-line argument by enclosing it in double quotes. This is necessary for queries containing spaces or special characters to be passed correctly to the script.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-text2sql/README.md#_snippet_4

LANGUAGE: bash
CODE:
```
python main.py "List orders placed in the last 30 days with status 'shipped'"
```

----------------------------------------

TITLE: Self-Looping Chain of Thought Node Flow - Mermaid
DESCRIPTION: This Mermaid flowchart visualizes the self-looping nature of the `ChainOfThoughtNode`. The node calls itself repeatedly based on a 'continue' condition, enabling iterative problem-solving within a single node.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/design.md#_snippet_0

LANGUAGE: mermaid
CODE:
```
flowchart LR
    cot[ChainOfThoughtNode] -->|"continue"| cot
```

----------------------------------------

TITLE: Running PocketFlow with Custom Problem
DESCRIPTION: Launches the PocketFlow Code Generator, allowing users to provide a custom coding problem description as a command-line argument for solution generation.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-code-generator/README.md#_snippet_4

LANGUAGE: bash
CODE:
```
python main.py "Reverse a linked list. Given the head of a singly linked list, reverse the list and return the reversed list."
```

----------------------------------------

TITLE: Verifying OpenAI API Key Configuration
DESCRIPTION: This command runs a utility script (`utils.py`) to perform a quick check, ensuring that the configured OpenAI API key is working correctly and accessible to the application.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-a2a/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python utils.py
```

----------------------------------------

TITLE: Running the Main Application - Bash
DESCRIPTION: This command executes the `main.py` script, which is the entry point for the Pocket Google Calendar application. It initiates the application's core logic and functionalities.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-google-calendar/README.md#_snippet_4

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Adjusting Force Simulation Parameters
DESCRIPTION: This JavaScript code snippet shows how to adjust the force simulation parameters in D3.js to change the layout of the graph. It controls the distance between connected nodes, how nodes repel each other, centers the graph, and prevents nodes from overlapping.  These parameters affect the visual arrangement of nodes and flows in the visualization.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/README.md#_snippet_2

LANGUAGE: JavaScript
CODE:
```
// Create a force simulation
const simulation = d3.forceSimulation(data.nodes)
    // Controls the distance between connected nodes
    .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
    // Controls how nodes repel each other - lower values bring nodes closer
    .force("charge", d3.forceManyBody().strength(-30))
    // Centers the entire graph in the SVG
    .force("center", d3.forceCenter(width / 2, height / 2))
    // Prevents nodes from overlapping - acts like a minimum distance
    .force("collide", d3.forceCollide().radius(50));
```

----------------------------------------

TITLE: Running Application with Custom Query - Python
DESCRIPTION: This command executes the `main.py` script while passing a specific user query as a command-line argument. This allows users to test the RAG system's ability to retrieve information and generate answers based on their own custom questions.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-rag/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
python main.py --"How does the Q-Mesh protocol achieve high transaction speeds?"
```

----------------------------------------

TITLE: Running a PocketFlow Application Entry Point (Python)
DESCRIPTION: This `main.py` snippet serves as the application's entry point. It initializes a `shared` dictionary to manage state, creates the question-answering flow using `create_qa_flow`, runs the flow, and then prints the question and answer retrieved from the `shared` state.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/guide.md#_snippet_5

LANGUAGE: Python
CODE:
```
# main.py
from flow import create_qa_flow

# Example main function
# Please replace this with your own main function
def main():
    shared = {
        "question": None,  # Will be populated by GetQuestionNode from user input
        "answer": None     # Will be populated by AnswerNode
    }

    # Create the flow and run it
    qa_flow = create_qa_flow()
    qa_flow.run(shared)
    print(f"Question: {shared['question']}")
    print(f"Answer: {shared['answer']}")

if __name__ == "__main__":
    main()
```

----------------------------------------

TITLE: Shared Store Structure for Joke Generator (Python)
DESCRIPTION: This Python dictionary defines the shared data structure used across different nodes in the joke generator application. It stores the user's topic, the current joke, a list of disliked jokes for context, and the latest user feedback.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-cmd-hitl/docs/design.md#_snippet_1

LANGUAGE: python
CODE:
```
shared = {
    "topic": None,             # Stores the user-provided joke topic
    "current_joke": None,      # Stores the most recently generated joke
    "disliked_jokes": [],    # A list to store jokes the user didn't like, for context
    "user_feedback": None      # Stores the user's latest feedback (e.g., "approve", "disapprove")
}
```

----------------------------------------

TITLE: Thought Dictionary Structure - Python
DESCRIPTION: Outlines the structure of each individual thought dictionary stored in the `shared['thoughts']` list. It includes the thought's sequence number, detailed thinking, the updated plan, and a flag indicating if further iteration is needed.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/design.md#_snippet_2

LANGUAGE: python
CODE:
```
{
    "thought_number": int,      # The sequence number of this thought.
    "current_thinking": str,    # Detailed text of the evaluation and thinking for this step.
    "planning": list[dict],     # The updated plan structure (list of dictionaries).
    "next_thought_needed": bool # Flag indicating if the loop should continue.
}
```

----------------------------------------

TITLE: Creating Graph Nodes with Drag Behavior (D3.js)
DESCRIPTION: Selects and appends 'circle' elements for graph nodes. Configures radius, fill color based on group, and attaches D3 drag behavior.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_9

LANGUAGE: javascript
CODE:
```
const node = svg.append("g")
  .attr("class", "nodes")
  .selectAll("circle")
  .data(data.nodes)
  .enter()
  .append("circle")
  .attr("r", 15)
  .attr("fill", d => color(d.group))
  .call(d3.drag()
    .on("start", dragstarted)
    .on("drag", dragged)
    .on("end", dragended));
```

----------------------------------------

TITLE: Performing Web Search with SerpApi (Python)
DESCRIPTION: This example demonstrates using SerpApi, a service that scrapes search engine results, in Python. It requires an API key and allows specifying the search engine (e.g., 'google'). The code sends a GET request to the SerpApi endpoint with the query, engine, and API key, then prints the parsed JSON results.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/websearch.md#_snippet_4

LANGUAGE: Python
CODE:
```
import requests

API_KEY = "YOUR_SERPAPI_KEY"
query = "example"

url = "https://serpapi.com/search"
params = {
    "engine": "google",
    "q": query,
    "api_key": API_KEY
}

response = requests.get(url, params=params)
results = response.json()
print(results)
```

----------------------------------------

TITLE: Generating Configuration Files (YAML)
DESCRIPTION: This YAML snippet shows how an LLM can generate a configuration file with predefined settings for a server, including host, port, and SSL status. This ensures consistent and machine-readable configurations.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/structure.md#_snippet_2

LANGUAGE: yaml
CODE:
```
server:
  host: 127.0.0.1
  port: 8080
  ssl: true
```

----------------------------------------

TITLE: Resetting UI Elements and Buttons - JavaScript
DESCRIPTION: This snippet resets the content of an element, hides review and result sections, clears the value of a task input field, and enables submit, approve, and reject buttons. It's commonly used to prepare the UI for a new task or after completing a process.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-hitl/templates/index.html#_snippet_1

LANGUAGE: javascript
CODE:
```
ontent = 'Submit a task.'; reviewSection.classList.add('hidden'); resultSection.classList.add('hidden'); taskInput.value = ''; submitButton.disabled = false; approveButton.disabled = false; rejectButton.disabled = false; }
```

----------------------------------------

TITLE: Installing Dependencies and Running Application - Python
DESCRIPTION: These commands first install all necessary Python packages listed in `requirements.txt` using pip, and then execute the `main.py` script to run the RAG application with its default query. This is the standard way to get the application up and running.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-rag/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
python main.py
```

----------------------------------------

TITLE: Running the Parallel Image Processor
DESCRIPTION: This snippet provides the necessary commands to set up and run the parallel image processing application. It first installs required Python dependencies and then executes the main script.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-parallel-batch-flow/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
python main.py
```

----------------------------------------

TITLE: Creating Node Labels (D3.js)
DESCRIPTION: Selects and appends 'text' elements to label the graph nodes. Positions the label below the node circle.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_10

LANGUAGE: javascript
CODE:
```
const nodeLabel = svg.append("g")
  .attr("class", "node-labels")
  .selectAll("text")
  .data(data.nodes)
  .enter()
  .append("text")
  .text(d => d.name)
  .attr("text-anchor", "middle")
  .attr("dy", 25);
```

----------------------------------------

TITLE: Generating Embeddings with Hugging Face Inference API (Python)
DESCRIPTION: This Python snippet illustrates how to generate text embeddings using the Hugging Face Inference API. It sends a POST request to a specified model endpoint with the input text and an authorization token, then parses the JSON response to extract and print the embedding vector.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/embedding.md#_snippet_5

LANGUAGE: Python
CODE:
```
import requests

API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
HEADERS = {"Authorization": "Bearer YOUR_HF_TOKEN"}

res = requests.post(API_URL, headers=HEADERS, json={"inputs": "Hello world"})
vec = res.json()[0]
print(vec)
```

----------------------------------------

TITLE: Run the PocketFlow Application (Bash)
DESCRIPTION: Executes the main Python script to start the PocketFlow voice chat application. The application will then listen for user input via the microphone.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-voice-chat/README.md#_snippet_3

LANGUAGE: Bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Building Mermaid Diagram for Flow Visualization in Python
DESCRIPTION: This function recursively traverses a nested graph, assigns unique IDs to each node, and generates Mermaid syntax for visualizing Flow nodes as subgraphs. It takes a starting node as input and returns a Mermaid diagram string.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/viz.md#_snippet_0

LANGUAGE: Python
CODE:
```
def build_mermaid(start):
    ids, visited, lines = {}, set(), ["graph LR"]
    ctr = 1
    def get_id(n):
        nonlocal ctr
        return ids[n] if n in ids else (ids.setdefault(n, f"N{ctr}"), (ctr := ctr + 1))[0]
    def link(a, b):
        lines.append(f"    {a} --> {b}")
    def walk(node, parent=None):
        if node in visited:
            return parent and link(parent, get_id(node))
        visited.add(node)
        if isinstance(node, Flow):
            node.start_node and parent and link(parent, get_id(node.start_node))
            lines.append(f"\n    subgraph sub_flow_{get_id(node)}[{type(node).__name__}]")
            node.start_node and walk(node.start_node)
            for nxt in node.successors.values():
                node.start_node and walk(nxt, get_id(node.start_node)) or (parent and link(parent, get_id(nxt))) or walk(nxt)
            lines.append("    end\n")
        else:
            lines.append(f"    {(nid := get_id(node))}['{type(node).__name__}']")
            parent and link(parent, nid)
            [walk(nxt, nid) for nxt in node.successors.values()]
    walk(start)
    return "\n".join(lines)
```

----------------------------------------

TITLE: Implementing GetApproval AsyncNode in Python
DESCRIPTION: This `AsyncNode` handles user confirmation for a suggested recipe. The `post_async` method asynchronously waits for user input to accept or reject the suggestion, returning 'accept' or 'retry' to control the flow based on the response.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-async-basic/README.md#_snippet_2

LANGUAGE: Python
CODE:
```
async def post_async(self, shared, prep_res, suggestion):
    # Async user input
    answer = await get_user_input(
        f"Accept {suggestion}? (y/n): "
    )
    return "accept" if answer == "y" else "retry"
```

----------------------------------------

TITLE: Running Agent with Custom Question (Python)
DESCRIPTION: This command runs the main agent script, `main.py`, allowing a custom question to be provided using the `--` prefix. This enables users to query the agent on any desired topic, showcasing its versatility.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-supervisor/README.md#_snippet_4

LANGUAGE: python
CODE:
```
python main.py --"What is quantum computing?"
```

----------------------------------------

TITLE: Switching to Real OpenAI Streaming
DESCRIPTION: This code snippet shows how to modify the main.py file to switch from using fake streaming responses to using real OpenAI streaming by replacing the fake_stream_llm function call with the stream_llm function call.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-llm-streaming/README.md#_snippet_1

LANGUAGE: python
CODE:
```
# Change this line:
chunks = fake_stream_llm(prompt)
# To this:
chunks = stream_llm(prompt)
```

----------------------------------------

TITLE: Displaying Error Messages - JavaScript
DESCRIPTION: This function displays an error message to the user. It sets the text content of an error message element, makes it visible, and hides the main status card.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/static/progress.html#_snippet_8

LANGUAGE: JavaScript
CODE:
```
function showError(message) {
  document.getElementById('errorMessage').textContent = message;
  document.getElementById('errorMessage').style.display = 'block';
  document.getElementById('statusCard').style.display = 'none';
}
```

----------------------------------------

TITLE: Installing PocketFlow with pip
DESCRIPTION: This command installs the PocketFlow package using pip, the Python package installer. It allows users to quickly set up and use the framework in their projects.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-parallel-batch/translations/README_KOREAN.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install pocketflow
```

----------------------------------------

TITLE: Installing Pocket Flow with pip
DESCRIPTION: This command installs the Pocket Flow package using pip, the Python package installer. It fetches the latest version of Pocket Flow from the Python Package Index (PyPI) and installs it along with any dependencies.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-parallel-batch/translations/README_SPANISH.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install pocketflow
```

----------------------------------------

TITLE: Data Science Flow with Call Stack Debugging in Python
DESCRIPTION: This code defines a data science flow similar to the previous example, but includes a call to get_node_call_stack within the EvaluateModelNode. This allows for debugging by printing the call stack during the evaluation phase.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/viz.md#_snippet_4

LANGUAGE: Python
CODE:
```
class DataPrepBatchNode(BatchNode): 
    def prep(self, shared): return []
class ValidateDataNode(Node): pass
class FeatureExtractionNode(Node): pass
class TrainModelNode(Node): pass
class EvaluateModelNode(Node): 
    def prep(self, shared):
        stack = get_node_call_stack()
        print("Call stack:", stack)
class ModelFlow(Flow): pass
class DataScienceFlow(Flow):pass

feature_node = FeatureExtractionNode()
train_node = TrainModelNode()
evaluate_node = EvaluateModelNode()
feature_node >> train_node >> evaluate_node
model_flow = ModelFlow(start=feature_node)
data_prep_node = DataPrepBatchNode()
validate_node = ValidateDataNode()
data_prep_node >> validate_node >> model_flow
data_science_flow = DataScienceFlow(start=data_prep_node)
data_science_flow.run({})
```

----------------------------------------

TITLE: Project Directory Structure
DESCRIPTION: This snippet illustrates the typical directory structure of the PocketFlow summarization project, showing the organization of documentation, utility functions, the main flow implementation, and the application entry point.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-node/README.md#_snippet_0

LANGUAGE: text
CODE:
```
.
├── docs/          # Documentation files
├── utils/         # Utility functions (LLM API wrapper)
├── flow.py        # PocketFlow implementation with Summarize Node
├── main.py        # Main application entry point
└── README.md      # Project documentation
```

----------------------------------------

TITLE: Setting up D3.js Force Simulation for Flow Visualization (JavaScript)
DESCRIPTION: Loads flow data from a JSON file, defines SVG arrow markers for links, sets up a color scale for node groups, processes nodes into groups, initializes a D3 force simulation with link, charge, center, and collide forces, and defines custom forces for intra-group clustering and inter-group layout.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_1

LANGUAGE: javascript
CODE:
```
// Load data from file
d3.json("flow_visualization.json").then(data => {
  const svg = d3.select("#graph");
  const width = window.innerWidth;
  const height = window.innerHeight;

  // Define arrow markers for links
  svg.append("defs").append("marker")
    .attr("id", "arrowhead")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 25) // Position the arrow away from the target node
    .attr("refY", 0)
    .attr("orient", "auto")
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("xoverflow", "visible")
    .append("path")
    .attr("d", "M 0,-5 L 10,0 L 0,5")
    .attr("fill", "#999");

  // Define thicker arrow markers for group links
  svg.append("defs").append("marker")
    .attr("id", "group-arrowhead")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 3) // Position at the boundary of the group
    .attr("refY", 0)
    .attr("orient", "auto")
    .attr("markerWidth", 8)
    .attr("markerHeight", 8)
    .attr("xoverflow", "visible")
    .append("path")
    .attr("d", "M 0,-5 L 10,0 L 0,5")
    .attr("fill", "#333");

  // Color scale for node groups
  const color = d3.scaleOrdinal(d3.schemeCategory10);

  // Process the data to identify groups
  const groups = {};
  data.nodes.forEach(node => {
    if (node.group > 0) {
      if (!groups[node.group]) {
        // Use the flow name instead of generic "Group X"
        const flowName = data.flows && data.flows[node.group] ? data.flows[node.group] : `Flow ${node.group}`;
        groups[node.group] = { id: node.group, name: flowName, nodes: [], x: 0, y: 0, width: 0, height: 0 };
      }
      groups[node.group].nodes.push(node);
    }
  });

  // Create a force simulation
  const simulation = d3.forceSimulation(data.nodes)
    // Controls the distance between connected nodes
    .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
    // Controls how nodes repel each other - lower values bring nodes closer
    .force("charge", d3.forceManyBody().strength(-30))
    // Centers the entire graph in the SVG
    .force("center", d3.forceCenter(width / 2, height / 2))
    // Prevents nodes from overlapping - acts like a minimum distance
    .force("collide", d3.forceCollide().radius(50));

  // Group forces - create a force to keep nodes in the same group closer together
  // This creates the effect of nodes clustering within their group boxes
  const groupForce = alpha => {
    for (let i = 0; i < data.nodes.length; i++) {
      const node = data.nodes[i];
      if (node.group > 0) {
        const group = groups[node.group];
        if (group && group.nodes.length > 1) {
          // Calculate center of group
          let centerX = 0, centerY = 0;
          group.nodes.forEach(n => {
            centerX += n.x || 0;
            centerY += n.y || 0;
          });
          centerX /= group.nodes.length;
          centerY /= group.nodes.length;

          // Move nodes toward center
          const k = alpha * 0.3; // Increased from 0.1 to 0.3
          node.vx += (centerX - node.x) * k;
          node.vy += (centerY - node.y) * k;
        }
      }
    }
  };

  // Additional force to position groups in a more organized layout (like in the image)
  // This arranges the groups horizontally/vertically based on their connections
  const groupLayoutForce = alpha => {
    // Get group centers
    const groupCenters = Object.values(groups).map(g => {
      return { id: g.id, cx: 0, cy: 0 };
    });

    // Calculate current center positions
    Object.values(groups).forEach(g => {
      if (g.nodes.length > 0) {
        let cx = 0, cy = 0;
        g.nodes.forEach(n => {
          cx += n.x || 0;
          cy += n.y || 0;
        });
        const groupCenter = groupCenters.find(gc => gc.id === g.id);
        if (groupCenter) {
          groupCenter.cx = cx / g.nodes.length;
          groupCenter.cy = cy / g.nodes.length;
        }
      }
    });

    // Apply forces to position groups
    const k = alpha * 0.05;
    // Try to position groups in a more structured way
    // Adjust these values to change the overall layout
    for (let i = 0; i < data.group_links.length; i++) {
      const link = data.group_links[i];
      const source = groupCenters.find(g => g.id === link.source);
      const target = groupCenters.find(g => g.id === link.target);

      if (source && target) {
        // Add a horizontal force to align groups
        const desiredDx = 300; // Desired horizontal distance between linked groups
        const dx = target.cx - source.cx;
        const diff = desiredDx - Math.abs(dx);

        // Apply forces to group nodes
        groups[source.id].nodes.forEach(n => {
          if (dx > 0) {
            n.vx -= diff * k;
          } else {
            n.vx += diff * k;
          }
        });
        groups[target.id].nodes.forEach(n => {
          if (dx > 0) {
            n.vx +=
```

----------------------------------------

TITLE: Setting Up Python Virtual Environment
DESCRIPTION: This command sequence creates a new Python virtual environment named 'venv' and then activates it. A virtual environment isolates project dependencies, preventing conflicts with other Python projects.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-node/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

----------------------------------------

TITLE: Running the PocketFlow PDF Vision Example (bash)
DESCRIPTION: Executes the main Python script (`main.py`) to start the PocketFlow PDF Vision process. This script will load, process, and extract text from PDF files placed in the `pdfs` directory.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-pdf-vision/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Shared Memory Structure for PocketFlow Code Generator
DESCRIPTION: This Python dictionary defines the shared memory structure used by the PocketFlow system. It stores critical information such as the problem description, generated test cases, the implemented function's code, the results of test executions, and iteration metadata like current count and maximum allowed iterations.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-code-generator/doc/design.md#_snippet_1

LANGUAGE: python
CODE:
```
shared = {
    "problem": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
    "test_cases": [
        {"name": "Basic case", "input": {"nums": [2,7,11,15], "target": 9}, "expected": [0,1]},
        {"name": "Different order", "input": {"nums": [3,2,4], "target": 6}, "expected": [1,2]},
        # ... more test cases
    ],
    "function_code": "def run_code(nums, target): ...",
    "test_results": [
        {"test_case": {...}, "passed": True/False, "error": "..."},
        # ... results for each test case
    ],
    "iteration_count": 0,
    "max_iterations": 5
}
```

----------------------------------------

TITLE: Running Research Agent with Default Question
DESCRIPTION: This command starts the research agent using the default question (about Nobel Prize winners). It demonstrates the agent's core functionality without requiring specific input.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/README.md#_snippet_3

LANGUAGE: python
CODE:
```
python main.py
```

----------------------------------------

TITLE: Running PocketFlow Async Example with Bash
DESCRIPTION: These commands demonstrate how to set up and run the PocketFlow async example. First, `pip install -r requirements.txt` installs necessary Python dependencies, then `python main.py` executes the main application script.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-async-basic/README.md#_snippet_3

LANGUAGE: Bash
CODE:
```
pip install -r requirements.txt
python main.py
```

----------------------------------------

TITLE: Installing Python Dependencies (Bash)
DESCRIPTION: This command installs all necessary Python packages listed in the `requirements.txt` file. It ensures that the project has all its required libraries to run correctly, setting up the environment for the research supervisor.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-supervisor/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Installing Python Dependencies
DESCRIPTION: This command installs all required Python packages listed in the `requirements.txt` file. It's the first step after cloning the repository to set up the project environment.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-search/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Install Dependencies with pip
DESCRIPTION: Installs the required Python packages listed in the `requirements.txt` file using the pip package manager. This is the first step to set up the project environment.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-structured-output/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Initializing Shared Data and Loading Documents in Python
DESCRIPTION: This snippet initializes a shared data dictionary and populates it by reading content from multiple text files located in a specified directory. This data serves as the knowledge base for the RAG system, making document content accessible to subsequent processing nodes.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_15

LANGUAGE: Python
CODE:
```
# Create test data
shared = {"data": {}}

# Load all files
path = "./data/PaulGrahamEssaysLarge"
for filename in os.listdir(path):
    with open(os.path.join(path, filename), "r") as f:
        shared["data"][filename] = f.read()
```

----------------------------------------

TITLE: Get Node Call Stack in Python
DESCRIPTION: This function inspects the runtime call stack to identify and return the names of the nodes in the call stack. It uses the inspect module to traverse the stack frames and identify instances of BaseNode.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/viz.md#_snippet_3

LANGUAGE: Python
CODE:
```
import inspect

def get_node_call_stack():
    stack = inspect.stack()
    node_names = []
    seen_ids = set()
    for frame_info in stack[1:]:
        local_vars = frame_info.frame.f_locals
        if 'self' in local_vars:
            caller_self = local_vars['self']
            if isinstance(caller_self, BaseNode) and id(caller_self) not in seen_ids:
                seen_ids.add(id(caller_self))
                node_names.append(type(caller_self).__name__)
    return node_names
```

----------------------------------------

TITLE: Running PocketFlow Example - Bash
DESCRIPTION: This command executes the `main.py` script, which serves as the entry point for the PocketFlow example. It initializes the database, creates a task, and lists all tasks, demonstrating the integrated functionality.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-database/README.md#_snippet_4

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Customizing PDF Path and Extraction Prompt (Python)
DESCRIPTION: Demonstrates how to configure the `shared` dictionary to specify the target PDF file path and a custom prompt for the Vision API text extraction. Modify these values to process a different file or use a specific extraction instruction.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-pdf-vision/README.md#_snippet_3

LANGUAGE: python
CODE:
```
shared = {
    "pdf_path": "your_file.pdf",
    "extraction_prompt": "Your custom prompt here"
}
```

----------------------------------------

TITLE: Running Default Text-to-SQL Workflow Example
DESCRIPTION: Executes the main script `main.py` without any command-line arguments. This runs the workflow using a predefined default natural language query and creates/uses the sample `ecommerce.db` database.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-text2sql/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Running Article Workflow with Custom Topic
DESCRIPTION: This command runs the `main.py` script, allowing you to specify a custom topic for the article generation workflow. Replace 'Climate Change' with your desired topic.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-workflow/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
python main.py Climate Change
```

----------------------------------------

TITLE: Running the FastAPI Application - Bash
DESCRIPTION: This command starts the FastAPI application, which includes the WebSocket endpoint for real-time chat communication and serves the web UI. Once executed, the application will be accessible via a web browser.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-websocket/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Creating Group Links (D3.js)
DESCRIPTION: Selects and appends 'path' elements for links connecting different groups (flows). Configures stroke width, color, and adds a specific arrowhead marker.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_5

LANGUAGE: javascript
CODE:
```
const groupLink = svg.append("g")
  .attr("class", "group-links")
  .selectAll("path")
  .data(data.group_links || [])
  .enter()
  .append("path")
  .attr("stroke-width", 2)
  .attr("stroke", "#333")
  .attr("marker-end", "url(#group-arrowhead)");
```

----------------------------------------

TITLE: Running the PocketFlow Summarization Example
DESCRIPTION: This command executes the main application entry point, `main.py`, which initiates the PocketFlow summarization process. It starts the flow and performs text summarization as configured.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-node/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Parsing URL Parameters and Initializing Progress Connection - JavaScript
DESCRIPTION: This snippet parses URL parameters to extract `job_id` and `topic`. It updates the topic title if available and initiates a connection to the progress updates if a `job_id` is present, otherwise it displays an error.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/static/progress.html#_snippet_1

LANGUAGE: JavaScript
CODE:
```
const urlParams = new URLSearchParams(window.location.search); const jobId = urlParams.get('job_id'); const topic = urlParams.get('topic'); if (topic) { document.getElementById('topicTitle').textContent = `"${topic}"`; } if (!jobId) { showError('No job ID provided'); } else { connectToProgress(); }
```

----------------------------------------

TITLE: Run FastAPI Server with Uvicorn (Bash)
DESCRIPTION: Starts the FastAPI application defined in server.py using Uvicorn, enabling auto-reload for development and listening on port 8000.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-hitl/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
uvicorn server:app --reload --port 8000
```

----------------------------------------

TITLE: Running Streamlit Application
DESCRIPTION: This command launches the Streamlit web application by executing the `app.py` script. The application will typically be accessible via a local URL provided in the console.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-streamlit-fsm/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
streamlit run app.py
```

----------------------------------------

TITLE: Setting OpenAI API Key via System Environment Variable
DESCRIPTION: This command sets the OpenAI API key as a system environment variable. This method is suitable for production environments or when the key needs to be accessible globally within the current shell session. The `export` command makes the variable available to child processes.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-embeddings/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY=your_api_key_here
```

----------------------------------------

TITLE: Defining Flowchart with Mermaid
DESCRIPTION: This snippet defines a simple directed flowchart using Mermaid syntax, illustrating the sequential flow from 'First Node' to 'Second Node' and then to 'Third Node'. It visually represents the project's flow design.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-hello-world/docs/design.md#_snippet_0

LANGUAGE: mermaid
CODE:
```
flowchart TD
    firstNode[First Node] --> secondNode[Second Node]
    secondNode --> thirdNode[Third Node]
```

----------------------------------------

TITLE: Setting OpenAI API Key (Bash)
DESCRIPTION: Sets the `OPENAI_API_KEY` environment variable with your OpenAI API key. This is required for the application to authenticate with the OpenAI API for LLM processing.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-map-reduce/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY=your_api_key_here
```

----------------------------------------

TITLE: Running PocketFlow with Default Problem
DESCRIPTION: Starts the PocketFlow Code Generator, which will automatically use the default 'Two Sum' problem to demonstrate its code generation and improvement capabilities.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-code-generator/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Run the Main Application
DESCRIPTION: Executes the main application script `main.py`. This script contains the implementation of the `ResumeParserNode` which processes the resume data.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-structured-output/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Running Agent with Default Question (Python)
DESCRIPTION: This command starts the main agent script, `main.py`, which will process a default question (about Nobel Prize winners). It demonstrates the basic operation of the research supervisor and its ability to generate answers.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-supervisor/README.md#_snippet_3

LANGUAGE: python
CODE:
```
python main.py
```

----------------------------------------

TITLE: Representing Dialogue with Escaped Characters (JSON)
DESCRIPTION: This JSON snippet illustrates the complexity of escaping special characters like double quotes and newlines within a string. Every internal quote requires `\"` and newlines require `\n`, making it less readable for LLMs.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/structure.md#_snippet_4

LANGUAGE: json
CODE:
```
{
  "dialogue": "Alice said: \"Hello Bob.\\nHow are you?\\nI am good.\""
}
```

----------------------------------------

TITLE: Updating Status Title and Content - JavaScript
DESCRIPTION: This function updates the main status display on the page. It sets the inner HTML of the status title element, including a spinner, and updates the text content of the status content element.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/static/progress.html#_snippet_5

LANGUAGE: JavaScript
CODE:
```
function updateStatus(title, content) {
  document.getElementById('statusTitle').innerHTML = `<span class="spinner"></span> ${title}`;
  document.getElementById('statusContent').textContent = content;
}
```

----------------------------------------

TITLE: Installing Pocket Flow with Pip
DESCRIPTION: This command facilitates the installation of the Pocket Flow library using Python's package installer, pip. It is the recommended and most straightforward method for setting up the framework in a development environment.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_0

LANGUAGE: Shell
CODE:
```
pip install pocketflow
```

----------------------------------------

TITLE: Server Log: PocketFlow A2A Interaction Flow
DESCRIPTION: This log snippet displays the internal steps of the PocketFlow A2A server, including server startup, receipt of a JSON-RPC request for a task, agent decision-making (searching, analyzing, answering), and the final JSON-RPC response with the generated answer. It illustrates the flow from request reception to task completion.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-a2a/README.md#_snippet_5

LANGUAGE: Log
CODE:
```
2025-04-12 17:20:40,893 - __main__ - INFO - Starting PocketFlow A2A server on http://localhost:10003
INFO:     Started server process [677223]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:10003 (Press CTRL+C to quit)
2025-04-12 17:20:57,647 - A2AServer - INFO - <- Received Request (ID: d3f3fb93350d47d9a94ca12bb62b656b):
{
  "jsonrpc": "2.0",
  "id": "d3f3fb93350d47d9a94ca12bb62b656b",
  "method": "tasks/send",
  "params": {
    "id": "46c3ce7b941a4fff9b8e3b644d6db5f4",
    "sessionId": "f3e12b8424c44241be881cd4bb8a269f",
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "Who won the Nobel Prize in Physics 2024?"
        }
      ]
    },
    "acceptedOutputModes": [
      "text",
      "text/plain"
    ]
  }
}
2025-04-12 17:20:57,647 - task_manager - INFO - Received task send request: 46c3ce7b941a4fff9b8e3b644d6db5f4
2025-04-12 17:20:57,647 - common.server.task_manager - INFO - Upserting task 46c3ce7b941a4fff9b8e3b644d6db5f4
2025-04-12 17:20:57,647 - task_manager - INFO - Running PocketFlow for task 46c3ce7b941a4fff9b8e3b644d6db5f4...
🤔 Agent deciding what to do next...
2025-04-12 17:20:59,213 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
🔍 Agent decided to search for: 2024 Nobel Prize in Physics winner
🌐 Searching the web for: 2024 Nobel Prize in Physics winner
2025-04-12 17:20:59,974 - primp - INFO - response: https://lite.duckduckgo.com/lite/ 200
📚 Found information, analyzing results...
🤔 Agent deciding what to do next...
2025-04-12 17:21:01,619 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
💡 Agent decided to answer the question
✍️ Crafting final answer...
2025-04-12 17:21:03,833 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
✅ Answer generated successfully
2025-04-12 17:21:03,834 - task_manager - INFO - PocketFlow completed for task 46c3ce7b941a4fff9b8e3b644d6db5f4
2025-04-12 17:21:03,834 - A2AServer - INFO - -> Response (ID: d3f3fb93350d47d9a94ca12bb62b656b):
{
  "jsonrpc": "2.0",
  "id": "d3f3fb93350d47d9a94ca12bb62b656b",
  "result": {
    "id": "46c3ce7b941a4fff9b8e3b644d6db5f4",
    "sessionId": "f3e12b8424c44241be881cd4bb8a269f",
    "status": {
      "state": "completed",
      "timestamp": "2025-04-12T17:21:03.834542"
    },
    "artifacts": [
      {
        "parts": [
          {
            "type": "text",
            "text": "The 2024 Nobel Prize in Physics was awarded to John J. Hopfield and Geoffrey Hinton for their foundational discoveries and inventions that have significantly advanced the field of machine learning through the use of artificial neural networks. Their pioneering work has been crucial in the development and implementation of algorithms that enable machines to learn and process information in a manner that mimics human cognitive functions. This advancement in artificial intelligence technology has had a profound impact on numerous industries, facilitating innovations across various applications, from image and speech recognition to self-driving cars."
          }
        ],
        "index": 0
      }
    ],
    "history": []
  }
}
```

----------------------------------------

TITLE: Installing PocketFlow with pip
DESCRIPTION: This command installs the PocketFlow package using pip, the Python package installer. It allows users to quickly set up and use the framework in their projects. Ensure that pip is installed and configured correctly in your environment before running this command.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_KOREAN.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install pocketflow
```

----------------------------------------

TITLE: Installing Pocket Flow with pip
DESCRIPTION: This command installs the Pocket Flow package using pip, the Python package installer. It allows users to quickly integrate Pocket Flow into their Python projects.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_SPANISH.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install pocketflow
```

----------------------------------------

TITLE: Installing PocketFlow with pip
DESCRIPTION: This command installs the PocketFlow package using pip, the Python package installer. It allows users to quickly integrate PocketFlow into their Python projects.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_CHINESE.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install pocketflow
```

----------------------------------------

TITLE: Installing PocketFlow with pip
DESCRIPTION: This command installs the PocketFlow package using pip, the Python package installer. This allows you to quickly integrate PocketFlow into your Python projects.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_JAPANESE.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install pocketflow
```

----------------------------------------

TITLE: PocketFlow Chat Application Flowchart (Mermaid)
DESCRIPTION: This Mermaid diagram illustrates the high-level data flow and interaction between the different specialized nodes within the PocketFlow chat application. It shows how user questions lead to retrieval, answering, and embedding processes, forming a continuous conversational loop.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-chat-memory/README.md#_snippet_2

LANGUAGE: Mermaid
CODE:
```
flowchart LR
    Question[GetUserQuestionNode] -->|retrieve| Retrieve[RetrieveNode]
    Retrieve -->|answer| Answer[AnswerNode]
    Answer -->|question| Question
    Answer -->|embed| Embed[EmbedNode]
    Embed -->|question| Question
```

----------------------------------------

TITLE: PocketFlow Agent Workflow Diagram (Mermaid)
DESCRIPTION: This Mermaid diagram illustrates the high-level workflow of the PocketFlow agent. It shows a sequence where tools are retrieved, a decision is made on which tool to use, and then the selected tool is executed, forming the core logic of the agent's interaction with tools.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-mcp/README.md#_snippet_2

LANGUAGE: mermaid
CODE:
```
flowchart LR
    tools[GetToolsNode] -->|decide| decide[DecideToolNode]
    decide -->|execute| execute[ExecuteToolNode]
```

----------------------------------------

TITLE: Updating Progress Bar Display - JavaScript
DESCRIPTION: This function updates the visual progress bar on the page. It sets the text content of an element to display the percentage and adjusts the width of a fill element to visually represent the progress.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/static/progress.html#_snippet_4

LANGUAGE: JavaScript
CODE:
```
function updateProgress(percentage) {
  document.getElementById('progressPercentage').textContent = `${percentage}%`;
  document.getElementById('progressFill').style.width = `${percentage}%`;
}
```

----------------------------------------

TITLE: Chat Application Flow Diagram (Mermaid)
DESCRIPTION: This Mermaid flowchart illustrates the high-level data flow within the travel advisor chat application. It shows how user input is validated by a GuardrailNode, which either retries invalid queries or processes valid ones through an LLMNode before continuing the conversation.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-chat-guardrail/README.md#_snippet_2

LANGUAGE: mermaid
CODE:
```
flowchart LR
    user[UserInputNode] -->|validate| guardrail[GuardrailNode]
    guardrail -->|retry| user
    guardrail -->|process| llm[LLMNode]
    llm -->|continue| user
```

----------------------------------------

TITLE: Installing Project Dependencies
DESCRIPTION: This command installs all required Python packages listed in the `requirements.txt` file. It ensures that all necessary libraries for the PocketFlow and OpenAI integration are available within the activated virtual environment.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-embeddings/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Installing Pocket Flow with pip
DESCRIPTION: This command installs the Pocket Flow package using pip, the Python package installer. It allows users to quickly integrate Pocket Flow into their Python projects.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_FRENCH.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install pocketflow
```

----------------------------------------

TITLE: Installing Project Dependencies
DESCRIPTION: This command uses pip to install all necessary Python packages listed in the `requirements.txt` file. This ensures that all required libraries for the PocketFlow summarization tool are available.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-node/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Installing PocketFlow with pip
DESCRIPTION: This command installs the PocketFlow package using pip, the Python package installer. It allows users to quickly integrate PocketFlow into their Python projects.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_PORTUGUESE.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install pocketflow
```

----------------------------------------

TITLE: Installing Pocket Flow with pip
DESCRIPTION: This command installs the Pocket Flow package using pip, the Python package installer. It allows users to quickly integrate Pocket Flow into their Python projects.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-parallel-batch/translations/README_FRENCH.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install pocketflow
```

----------------------------------------

TITLE: Installing PocketFlow with pip
DESCRIPTION: This command installs the PocketFlow package using pip, the Python package installer. It allows users to quickly integrate PocketFlow into their Python projects.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-parallel-batch/translations/README_CHINESE.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install pocketflow
```

----------------------------------------

TITLE: D3 Simulation Tick Function
DESCRIPTION: Defines the function executed on each tick of the D3 force simulation. It updates the positions of links, nodes, node labels, link labels, group containers, group labels, and group links based on the simulation's calculations.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_12

LANGUAGE: javascript
CODE:
```
simulation.on("tick", () => {
  // Update links with straight lines
  link.attr("d", d => {
    return `M${d.source.x},${d.source.y} L${d.target.x},${d.target.y}`;
  });

  // Update nodes
  node
    .attr("cx", d => d.x)
    .attr("cy", d => d.y);

  // Update node labels
  nodeLabel
    .attr("x", d => d.x)
    .attr("y", d => d.y);

  // Position link labels at midpoint
  linkLabel
    .attr("x", d => (d.source.x + d.target.x) / 2)
    .attr("y", d => (d.source.y + d.target.y) / 2);

  // Update group containers
  groupContainers.each(function(d) {
    // If there are nodes in this group
    if (d.nodes.length > 0) {
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

      // Find the bounding box for all nodes in the group
      d.nodes.forEach(n => {
        minX = Math.min(minX, n.x - 30);
        minY = Math.min(minY, n.y - 30);
        maxX = Math.max(maxX, n.x + 30);
        maxY = Math.max(maxY, n.y + 40); // Extra space for labels
      });

      // Add padding
      const padding = 20;
      minX -= padding;
      minY -= padding;
      maxX += padding;
      maxY += padding;

      // Save group dimensions
      d.x = minX;
      d.y = minY;
      d.width = maxX - minX;
      d.height = maxY - minY;
      d.centerX = minX + d.width / 2;
      d.centerY = minY + d.height / 2;

      // Set position and size of the group container
      d3.select(this)
        .attr("x", minX)
        .attr("y", minY)
        .attr("width", d.width)
        .attr("height", d.height);

      // Update group label position (top-left of group)
      groupLabels.filter(g => g.id === d.id)
        .attr("x", minX + 10)
        .attr("y", minY + 20);
    }
  });

  // Update group links between flows
  groupLink.attr("d", d => {
    const sourceGroup = groups[d.source];
    const targetGroup = groups[d.target];

    if (!sourceGroup || !targetGroup) return "";

    // Find intersection points with group boundaries
    // This ensures links connect to the group's border rather than its center

    // Calculate centers of groups
    const sx = sourceGroup.centerX;
    const sy = sourceGroup.centerY;
    const tx = targetGroup.centerX;
    const ty = targetGroup.centerY;

    // Calculate angle between centers - used to find intersection points
    const angle = Math.atan2(ty - sy, tx - sx);

    // Calculate intersection points with source group borders
    // We cast a ray from center in the direction of the target
    let sourceX, sourceY;
    const cosA = Math.cos(angle);
    const sinA = Math.sin(angle);

    // Check intersection with horizontal borders (top and bottom)
    const ts_top = (sourceGroup.y - sy) / sinA;
    const ts_bottom = (sourceGroup.y + sourceGroup.height - sy) / sinA;

    // Check intersection with vertical borders (left and right)
    const ts_left = (sourceGroup.x - sx) / cosA;
    const ts_right = (sourceGroup.x + sourceGroup.width - sx) / cosA;

    // Use the closest positive intersection (first hit with the bound
```

----------------------------------------

TITLE: Styling Article Generation UI with CSS
DESCRIPTION: This comprehensive CSS snippet provides the styling for the PocketFlow article generation interface. It includes global resets, defines the body's background and layout, styles the main content container, applies gradients and text effects to the logo, formats titles, implements animated progress bars with shimmer effects, designs status cards, creates step indicators, and styles interactive buttons, ensuring a responsive design across different screen sizes.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/static/progress.html#_snippet_0

LANGUAGE: CSS
CODE:
```
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
.container { background: white; border-radius: 20px; padding: 40px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1); max-width: 600px; width: 100%; text-align: center; }
.logo { font-size: 2rem; font-weight: 700; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 10px; }
.topic-title { color: #374151; font-size: 1.5rem; font-weight: 600; margin-bottom: 30px; }
.progress-container { margin: 30px 0; }
.progress-bar { width: 100%; height: 8px; background: #f3f4f6; border-radius: 10px; overflow: hidden; margin-bottom: 20px; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 10px; width: 0%; transition: width 0.5s ease; position: relative; }
.progress-fill::after { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent); animation: shimmer 2s infinite; }
@keyframes shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
.progress-text { color: #6b7280; font-size: 1rem; font-weight: 500; margin-bottom: 10px; }
.progress-percentage { color: #374151; font-size: 2rem; font-weight: 700; margin-bottom: 20px; }
.status-card { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; margin: 20px 0; text-align: left; }
.status-title { color: #374151; font-weight: 600; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }
.status-content { color: #6b7280; line-height: 1.5; }
.spinner { display: inline-block; width: 16px; height: 16px; border: 2px solid #e5e7eb; border-top: 2px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.step-indicator { display: flex; justify-content: space-between; margin: 30px 0; position: relative; }
.step-indicator::before { content: ''; position: absolute; top: 15px; left: 15px; right: 15px; height: 2px; background: #e5e7eb; z-index: 1; }
.step { display: flex; flex-direction: column; align-items: center; position: relative; z-index: 2; }
.step-circle { width: 30px; height: 30px; border-radius: 50%; background: #e5e7eb; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 0.8rem; margin-bottom: 8px; transition: all 0.3s ease; }
.step-circle.active { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
.step-circle.completed { background: #10b981; color: white; }
.step-label { font-size: 0.8rem; color: #6b7280; text-align: center; max-width: 80px; }
.result-section { display: none; text-align: left; margin-top: 30px; }
.result-section.show { display: block; }
.article-content { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 25px; line-height: 1.6; color: #374151; white-space: pre-wrap; max-height: 400px; overflow-y: auto; }
.action-buttons { display: flex; gap: 15px; margin-top: 20px; justify-content: center; }
.btn { padding: 12px 24px; border-radius: 10px; font-weight: 600; text-decoration: none; transition: all 0.3s ease; cursor: pointer; border: none; font-size: 0.95rem; }
.btn-primary { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3); }
.btn-secondary { background: #f3f4f6; color: #374151; border: 1px solid #e5e7eb; }
.btn-secondary:hover { background: #e5e7eb; }
.error-message { background: #fef2f2; border: 1px solid #fecaca; color: #dc2626; padding: 15px; border-radius: 10px; margin: 20px 0; }
@media (max-width: 480px) {
.container { padding: 30px 20px; }
.step-indicator { margin: 20px 0; }
.step-label { font-size: 0.7rem; max-width: 60px; }
.action-buttons { flex-direction: column; }
}
```

----------------------------------------

TITLE: Capturing Audio VAD Python
DESCRIPTION: Records audio input from the user using Voice Activity Detection (VAD). It checks the conversation state, potentially loads VAD parameters, calls the audio recording utility, and stores the resulting NumPy array and sample rate in the shared state.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-voice-chat/docs/design.md#_snippet_2

LANGUAGE: Python
CODE:
```
# CaptureAudioNode
# Purpose: Record audio input from the user using VAD.

# prep:
# Check shared["continue_conversation"].
# (Potentially load VAD parameters from shared["config"] if dynamic).

# exec:
# Call utils.audio_utils.record_audio() (passing VAD parameters if configured).
# This returns a NumPy array and sample rate.
exec_res = utils.audio_utils.record_audio(...)

# post:
# audio_numpy_array, sample_rate = exec_res
# Write audio_numpy_array to shared["user_audio_data"]
# Write sample_rate to shared["user_audio_sample_rate"]
# Returns "default"
```

----------------------------------------

TITLE: Mermaid Diagram Output
DESCRIPTION: This is an example of the Mermaid diagram generated by the build_mermaid function. It visualizes the structure of the DataScienceFlow, showing the connections between different nodes.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/viz.md#_snippet_2

LANGUAGE: Mermaid
CODE:
```
graph LR
    subgraph sub_flow_N1[DataScienceFlow]
    N2['DataPrepBatchNode']
    N3['ValidateDataNode']
    N2 --> N3
    N3 --> N4

    subgraph sub_flow_N5[ModelFlow]
    N4['FeatureExtractionNode']
    N6['TrainModelNode']
    N4 --> N6
    N7['EvaluateModelNode']
    N6 --> N7
    end

    end
```

----------------------------------------

TITLE: Styling Flow Visualization Elements (CSS)
DESCRIPTION: Defines the visual appearance of the flow visualization elements, including body, SVG container, links, nodes, labels, and group containers. Sets font styles, margins, SVG dimensions, link/node colors and strokes, label sizes, and group container appearance.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_0

LANGUAGE: css
CODE:
```
body { font-family: Arial, sans-serif; margin: 0; padding: 0; overflow: hidden; }
svg { width: 100vw; height: 100vh; }
.links path { fill: none; stroke: #999; stroke-opacity: 0.6; stroke-width: 1.5px; }
.group-links path { fill: none; stroke: #333; stroke-opacity: 0.8; stroke-width: 2px; stroke-dasharray: 5,5; }
.nodes circle { stroke: #fff; stroke-width: 1.5px; }
.node-labels { font-size: 12px; pointer-events: none; }
.link-labels { font-size: 10px; fill: #666; pointer-events: none; }
.group-link-labels { font-size: 11px; font-weight: bold; fill: #333; pointer-events: none; }
.group-container { stroke: #333; stroke-width: 1.5px; stroke-dasharray: 5,5; fill: rgba(200, 200, 200, 0.1); rx: 10; ry: 10; }
.group-label { font-size: 14px; font-weight: bold; pointer-events: none; }
```

----------------------------------------

TITLE: Calculate D3.js Group Link Path
DESCRIPTION: This code calculates the path data for a link between two groups in a D3.js force-directed graph. It determines the intersection points of a line connecting the group centers with the group boundaries to draw the link from border to border.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_13

LANGUAGE: javascript
CODE:
```
ary) let t_source = Infinity; if (ts_top > 0) t_source = Math.min(t_source, ts_top); if (ts_bottom > 0) t_source = Math.min(t_source, ts_bottom); if (ts_left > 0) t_source = Math.min(t_source, ts_left); if (ts_right > 0) t_source = Math.min(t_source, ts_right); // Target group: Find intersection in the opposite direction // We cast a ray from target center toward the source let targetX, targetY; const oppositeAngle = angle + Math.PI; const cosOpp = Math.cos(oppositeAngle); const sinOpp = Math.sin(oppositeAngle); // Check intersections for target group const tt_top = (targetGroup.y - ty) / sinOpp; const tt_bottom = (targetGroup.y + targetGroup.height - ty) / sinOpp; const tt_left = (targetGroup.x - tx) / cosOpp; const tt_right = (targetGroup.x + targetGroup.width - tx) / cosOpp; // Use the closest positive intersection let t_target = Infinity; if (tt_top > 0) t_target = Math.min(t_target, tt_top); if (tt_bottom > 0) t_target = Math.min(t_target, tt_bottom); if (tt_left > 0) t_target = Math.min(t_target, tt_left); if (tt_right > 0) t_target = Math.min(t_target, tt_right); // Calculate actual border points using parametric equation: // point = center + t * direction if (t_source !== Infinity) {
 sourceX = sx + cosA * t_source;
 sourceY = sy + sinA * t_source;
 } else {
 sourceX = sx;
 sourceY = sy;
 } if (t_target !== Infinity) {
 targetX = tx + cosOpp * t_target;
 targetY = ty + sinOpp * t_target;
 } else {
 targetX = tx;
 targetY = ty;
 } // Create a straight line between the border points return `M${sourceX},${sourceY} L${targetX},${targetY}`;
```

----------------------------------------

TITLE: Copying Article Content to Clipboard - JavaScript
DESCRIPTION: This function copies the generated article content to the user's clipboard. It uses the `navigator.clipboard.writeText` API and provides visual feedback to the user by temporarily changing the button text and background color upon successful copy, or showing an alert on failure.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/static/progress.html#_snippet_9

LANGUAGE: JavaScript
CODE:
```
function copyToClipboard() {
  const article = document.getElementById('articleContent').textContent;
  navigator.clipboard.writeText(article).then(() => {
    const btn = event.target;
    const originalText = btn.textContent;
    btn.textContent = 'Copied!';
    btn.style.background = '#10b981';
    setTimeout(() => {
      btn.textContent = originalText;
      btn.style.background = '';
    }, 2000);
  }).catch(err => {
    console.error('Failed to copy: ', err);
    alert('Failed to copy to clipboard');
  });
}
```

----------------------------------------

TITLE: Creating Group Container Rectangles (D3.js)
DESCRIPTION: Selects and appends 'rect' elements to represent group containers. These are drawn before nodes and styled with a semi-transparent fill based on group color.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_4

LANGUAGE: javascript
CODE:
```
const groupContainers = svg.append("g")
  .attr("class", "groups")
  .selectAll("rect")
  .data(Object.values(groups))
  .enter()
  .append("rect")
  .attr("class", "group-container")
  .attr("fill", d => d3.color(color(d.id)).copy({opacity: 0.2}));
```

----------------------------------------

TITLE: Running Text-to-SQL Workflow with Custom Query (Single Argument)
DESCRIPTION: Executes the main script `main.py` with a custom natural language query provided as command-line arguments. This example shows a query that might be treated as multiple arguments by the shell if not quoted.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-text2sql/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
python main.py What is the total stock quantity for products in the 'Accessories' category?
```

----------------------------------------

TITLE: Two Sum Problem Solution Implementation
DESCRIPTION: A Python function `run_code` that solves the 'Two Sum' problem. It uses a hash map to store numbers and their indices, efficiently finding two numbers that add up to the target in a single pass.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-code-generator/README.md#_snippet_5

LANGUAGE: python
CODE:
```
def run_code(nums, target):
    # Dictionary to store number -> index mapping
    num_to_index = {}
    
    # Iterate through the array
    for i, num in enumerate(nums):
        # Calculate what number we need to reach the target
        complement = target - num
        
        # Check if the complement exists in our map
        if complement in num_to_index:
            # Found the pair! Return indices
            return [num_to_index[complement], i]
        
        # Store current number and its index
        num_to_index[num] = i
    
    # Should never reach here given problem constraints
    return []
```

----------------------------------------

TITLE: Install Project Dependencies
DESCRIPTION: Installs the required Python packages for the project, including aiofiles, which is used for asynchronous file operations.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-parallel-batch/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Running the Visualization Script
DESCRIPTION: This bash script navigates to the example directory and runs the `visualize.py` script. This script generates visualization files in the `./viz` directory, which can then be viewed in a web browser.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/README.md#_snippet_1

LANGUAGE: Bash
CODE:
```
# Navigate to the directory
cd cookbook/pocketflow-minimal-flow2flow

# Run the visualization script
python visualize.py
```

----------------------------------------

TITLE: Printing Summary Result in Python
DESCRIPTION: This Python snippet demonstrates how to print the value associated with the 'summary' key from a 'shared' dictionary. The 'shared' dictionary likely holds common data or results accessible across different stages of a PocketFlow operation.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_4

LANGUAGE: Python
CODE:
```
print("Summary:", shared["summary"])
```

----------------------------------------

TITLE: Installing PocketFlow Agent Dependencies
DESCRIPTION: This snippet provides the necessary `pip` commands to install the core dependencies for the PocketFlow agent, including the PocketFlow framework itself, `aiohttp` for asynchronous HTTP requests, `openai` for LLM interactions, and `duckduckgo-search` for web searching capabilities.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/demo.ipynb#_snippet_0

LANGUAGE: python
CODE:
```
! pip install pocketflow>=0.0.1
! pip install aiohttp>=3.8.0
! pip install openai>=1.0.0
! pip install duckduckgo-search>=7.5.2
```

----------------------------------------

TITLE: Installing PocketFlow with pip
DESCRIPTION: This command installs the PocketFlow package using pip, the Python package installer. It allows users to quickly integrate PocketFlow into their Python projects.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-parallel-batch/translations/README_JAPANESE.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install pocketflow
```

----------------------------------------

TITLE: Installing Python Project Dependencies
DESCRIPTION: This command installs all necessary Python packages required for the project from the 'requirements.txt' file. It ensures that the environment has all the libraries needed for the Chain-of-Thought implementation to run correctly.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_0

LANGUAGE: Bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Installing Python Dependencies for PocketFlow Joke Generator
DESCRIPTION: This command installs all necessary Python packages listed in the `requirements.txt` file. It's a standard step to set up the project's environment before running the application.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-cmd-hitl/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Installing Dependencies with pip
DESCRIPTION: This command installs the necessary Python packages required to run the PocketFlow communication example. It reads the dependencies listed in the 'requirements.txt' file and installs them using the pip package manager.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-communication/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Installing Dependencies with pip (Bash)
DESCRIPTION: This command installs all required Python packages listed in the `requirements.txt` file. It's a standard practice for setting up Python project environments by ensuring all necessary libraries are available.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch-node/README.md#_snippet_0

LANGUAGE: Bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Installing Python Dependencies
DESCRIPTION: This command installs all necessary Python packages listed in the `requirements.txt` file. It's the first step to set up the project environment.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Installing Dependencies with pip
DESCRIPTION: This command installs all required Python packages listed in the `requirements.txt` file. It ensures that the PocketFlow environment has all necessary libraries for execution.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch-flow/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Running Research Agent with Custom Question
DESCRIPTION: This command allows users to run the research agent with a custom question provided as a command-line argument. The agent will then process and answer the specified query.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/README.md#_snippet_4

LANGUAGE: python
CODE:
```
python main.py --"What is quantum computing?"
```

----------------------------------------

TITLE: Installing Dependencies and Running Application (Bash)
DESCRIPTION: This snippet provides the commands to install the necessary Python dependencies from `requirements.txt` and then execute the main application script `main.py`. These steps are essential for setting up and launching the travel advisor chatbot.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-chat-guardrail/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
python main.py
```

----------------------------------------

TITLE: Running the LLM Streaming Demo
DESCRIPTION: This command installs the necessary dependencies from the requirements.txt file and then executes the main.py script, which demonstrates real-time LLM response streaming with user interrupt capability.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-llm-streaming/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
python main.py
```

----------------------------------------

TITLE: Applying Custom Forces to D3 Simulation
DESCRIPTION: Applies custom 'group' and 'groupLayout' forces to the D3 force simulation. These forces likely influence the positioning of nodes based on their group membership.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_2

LANGUAGE: javascript
CODE:
```
simulation.force("group", groupForce);
simulation.force("groupLayout", groupLayoutForce);
```

----------------------------------------

TITLE: Setting Anthropic API Key Environment Variable
DESCRIPTION: This command sets the 'ANTHROPIC_API_KEY' environment variable, which is crucial for authenticating with the Anthropic API. Replace 'your-api-key-here' with your actual API key to allow the LLM interactions.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_1

LANGUAGE: Bash
CODE:
```
export ANTHROPIC_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Running the PocketFlow Joke Generator Application
DESCRIPTION: This command executes the main entry point of the PocketFlow command-line joke generator. It starts the interactive application, allowing users to request jokes and provide feedback.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-cmd-hitl/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Running the Translation Process - Bash
DESCRIPTION: This command executes the main Python script, `main.py`, which initiates the batch translation workflow. It triggers the LLM-based translation of markdown documents as configured.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Running the Application (Bash)
DESCRIPTION: Executes the main Python script to start the multi-agent Taboo game. This initiates the AsyncHinter and AsyncGuesser nodes and manages the game flow.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-multi-agent/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Install Python Dependencies (Bash)
DESCRIPTION: Installs the necessary Python libraries listed in the requirements.txt file using pip. These include libraries like openai, pocketflow, sounddevice, etc.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-voice-chat/README.md#_snippet_1

LANGUAGE: Bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Install Python Dependencies (Bash)
DESCRIPTION: Installs the required Python packages listed in the requirements.txt file using pip.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-hitl/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Installing Dependencies for PocketFlow Text Converter - Bash
DESCRIPTION: This command installs all necessary Python packages listed in the `requirements.txt` file. It's a prerequisite for running the PocketFlow text converter application, ensuring all required libraries are available in the environment.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-flow/README.md#_snippet_0

LANGUAGE: Bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Installing Python Dependencies
DESCRIPTION: This command installs all necessary Python packages listed in the `requirements.txt` file. It's the first step to set up the project environment.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-workflow/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Installing Python Dependencies
DESCRIPTION: This command installs all required Python packages listed in the `requirements.txt` file. These dependencies are essential for the PocketFlow FastAPI application to function correctly.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Installing Project Dependencies - Bash
DESCRIPTION: This command uses pip to install all Python packages listed in the `requirements.txt` file. This ensures that all necessary libraries for the project are available within the active virtual environment.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-database/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Installing Project Dependencies - Bash
DESCRIPTION: This command installs all necessary Python packages listed in the 'requirements.txt' file. It ensures that all project dependencies are met, allowing the application to run without missing modules.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-websocket/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Adding Tooltip to Nodes (D3.js)
DESCRIPTION: Appends a 'title' element to each node circle to provide a native browser tooltip displaying the node's name on hover.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_11

LANGUAGE: javascript
CODE:
```
node.append("title")
  .text(d => d.name);
```

----------------------------------------

TITLE: Creating Link Labels (D3.js)
DESCRIPTION: Selects and appends 'text' elements to label the individual graph links. The text content is the 'action' property of the link data.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_8

LANGUAGE: javascript
CODE:
```
const linkLabel = svg.append("g")
  .attr("class", "link-labels")
  .selectAll("text")
  .data(data.links)
  .enter()
  .append("text")
  .text(d => d.action)
  .attr("font-size", "10px")
  .attr("fill", "#666");
```

----------------------------------------

TITLE: Transition Probability Matrix for Markov Chain
DESCRIPTION: This matrix P represents the transition probabilities between the four states of the Markov chain. Each element P[i][j] denotes the probability of transitioning from state i to state j in one roll. The states are: 0 (no sequence), 1 (just rolled 3), 2 (rolled 3,4), and 3 (success with 3,4,5).
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_5

LANGUAGE: Mathematics
CODE:
```
P = [
    [5/6, 1/6, 0,   0  ],
    [4/6, 1/6, 1/6, 0  ],
    [4/6, 1/6, 0,   1/6],
    [0,   0,   0,   1  ]
]
```

----------------------------------------

TITLE: Example Flow Design with Mermaid
DESCRIPTION: This Mermaid diagram illustrates a high-level flow for an AI system, demonstrating how different nodes (Start, Batch, Check, Process, Fix, End) are orchestrated. It includes conditional branching and a subgraph to represent a multi-step process, providing a visual outline of the system's logic.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/guide.md#_snippet_0

LANGUAGE: mermaid
CODE:
```
flowchart LR
    start[Start] --> batch[Batch]
    batch --> check[Check]
    check -->|OK| process
    check -->|Error| fix[Fix]
    fix --> check
    
    subgraph process[Process]
      step1[Step 1] --> step2[Step 2]
    end
    
    process --> endNode[End]
```

----------------------------------------

TITLE: Running Article Workflow with Default Topic
DESCRIPTION: This command executes the `main.py` script, initiating the article writing workflow using the default topic 'AI Safety'. It's the simplest way to run the application.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-workflow/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Running Nested BatchFlow Example - Bash
DESCRIPTION: This snippet provides the command-line instructions to set up and execute the PocketFlow Nested BatchFlow example. It first installs required Python packages from 'requirements.txt' and then runs the main script 'main.py' to start the grade calculation process.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-nested-batch/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
python main.py
```

----------------------------------------

TITLE: Running Custom Reasoning Problem (Bash)
DESCRIPTION: Executes the `main.py` script, allowing users to provide their own complex reasoning problem and specify the number of attempts (`--tries`) for the majority vote. This command facilitates testing the system with new, custom scenarios and observing its performance.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-majority-vote/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
python main.py --problem "Your complex reasoning problem here" --tries 5
```

----------------------------------------

TITLE: Running the Web Crawler
DESCRIPTION: This command executes the main script of the web crawler, initiating the crawling and content analysis process. Users will be prompted for input after execution.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-crawler/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Running the PocketFlow Text Converter Application - Bash
DESCRIPTION: This command executes the main Python script (`main.py`) to start the interactive text converter application. It initiates the PocketFlow workflow, allowing users to interact with the text transformation features.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-flow/README.md#_snippet_1

LANGUAGE: Bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Displaying Final Article Result - JavaScript
DESCRIPTION: This function hides the progress status card and displays the final generated article. It sets the text content of the article display area and makes the result section visible.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/static/progress.html#_snippet_7

LANGUAGE: JavaScript
CODE:
```
function showResult(article) {
  document.getElementById('statusCard').style.display = 'none';
  document.getElementById('articleContent').textContent = article;
  document.getElementById('resultSection').classList.add('show');
}
```

----------------------------------------

TITLE: Running PocketFlow Hello World Application (Bash)
DESCRIPTION: This command executes the main Python script 'main.py', which serves as the entry point for the PocketFlow 'Hello World' application, initiating its core functionality.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-hello-world/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Verify Anthropic API Key
DESCRIPTION: Runs a utility script to verify that the Anthropic API key is correctly set and functional. This requires a valid API key to be set as an environment variable.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-parallel-batch/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python utils.py
```

----------------------------------------

TITLE: Testing LLM and Web Search Functionality
DESCRIPTION: This command executes the `utils.py` script to verify that both the LLM call and web search features are working correctly. Successful responses indicate proper setup.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/README.md#_snippet_2

LANGUAGE: python
CODE:
```
python utils.py
```

----------------------------------------

TITLE: Styling for Article Generator Web Page - CSS
DESCRIPTION: This CSS snippet defines the visual appearance and layout of the article generator web page. It includes styles for general elements, container, logo, form inputs, buttons, and responsive adjustments for smaller screens, ensuring a modern and user-friendly interface.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/static/index.html#_snippet_0

LANGUAGE: css
CODE:
```
* { margin: 0; padding: 0; box-sizing: border-box; } body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; } .container { background: white; border-radius: 20px; padding: 40px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1); max-width: 500px; width: 100%; text-align: center; } .logo { font-size: 2.5rem; font-weight: 700; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 10px; } .subtitle { color: #6b7280; font-size: 1.1rem; margin-bottom: 40px; font-weight: 400; } .form-group { margin-bottom: 30px; text-align: left; } label { display: block; font-weight: 600; color: #374151; margin-bottom: 8px; font-size: 0.95rem; } input[type="text"] { width: 100%; padding: 16px 20px; border: 2px solid #e5e7eb; border-radius: 12px; font-size: 1rem; transition: all 0.3s ease; background: #f9fafb; } input[type="text"]:focus { outline: none; border-color: #667eea; background: white; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); } .submit-btn { width: 100%; padding: 16px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; border-radius: 12px; font-size: 1.1rem; font-weight: 600; cursor: pointer; transition: all 0.3s ease; margin-top: 10px; } .submit-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3); } .submit-btn:active { transform: translateY(0); } .example-topics { margin-top: 30px; padding-top: 30px; border-top: 1px solid #e5e7eb; } .example-topics h3 { color: #6b7280; font-size: 0.9rem; font-weight: 600; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 0.5px; } .topic-tags { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; } .topic-tag { background: #f3f4f6; color: #6b7280; padding: 6px 12px; border-radius: 20px; font-size: 0.85rem; cursor: pointer; transition: all 0.2s ease; border: 1px solid transparent; } .topic-tag:hover { background: #e5e7eb; color: #374151; } @media (max-width: 480px) { .container { padding: 30px 20px; } .logo { font-size: 2rem; }
```

----------------------------------------

TITLE: Project Directory Structure - Filesystem
DESCRIPTION: This snippet outlines the directory structure of the `pocket-google-calendar` project. It details the purpose of key files and directories, such as the application entry point (`main.py`), Pocket Flow node definitions (`nodes.py`), and configuration files (`.env`, `credentials.json`).
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-google-calendar/README.md#_snippet_6

LANGUAGE: text
CODE:
```
pocket-google-calendar/
├── main.py           # Application entry point
├── nodes.py          # Pocket Flow node definitions
├── utils/            # Utilities and helper functions
├── Pipfile           # Pipenv configuration
├── credentials.json  # Google Calendar API credentials
├── .env             # Environment variables
└── token.pickle      # Google Calendar authentication token
```

----------------------------------------

TITLE: Running the A2A Client to Interact with PocketFlow Agent
DESCRIPTION: This command launches the A2A client, which connects to the running A2A server at the specified URL (`http://localhost:10003`). The client allows users to send queries to the PocketFlow agent and receive responses.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-a2a/README.md#_snippet_4

LANGUAGE: bash
CODE:
```
python a2a_client.py --agent-url http://localhost:10003
```

----------------------------------------

TITLE: Running the PocketFlow Example
DESCRIPTION: This command executes the main Python script ('main.py') to start the PocketFlow communication example application. The script will initialize the flow and nodes, prompting the user for input to begin the word counting process.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-communication/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Install PortAudio on Linux (Bash)
DESCRIPTION: Installs the PortAudio development libraries on Debian/Ubuntu-based Linux systems, which may be required for the sounddevice Python library.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-voice-chat/README.md#_snippet_2

LANGUAGE: Bash
CODE:
```
sudo apt-get update && sudo apt-get install -y portaudio19-dev
```

----------------------------------------

TITLE: Styling PocketFlow Chat Interface with CSS
DESCRIPTION: This CSS snippet defines the visual presentation and layout of the PocketFlow chat application. It includes styles for the overall container, header, message display area, individual message bubbles (user and AI), and the input field with a send button, ensuring a responsive and modern chat UI.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-websocket/static/index.html#_snippet_0

LANGUAGE: CSS
CODE:
```
* { margin: 0; padding: 0; box-sizing: border-box; } body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; } .chat-container { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-radius: 20px; width: 100%; max-width: 600px; height: 80vh; display: flex; flex-direction: column; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden; } .header { padding: 20px; background: rgba(255, 255, 255, 0.1); border-bottom: 1px solid rgba(255, 255, 255, 0.2); text-align: center; } .header h1 { font-size: 24px; font-weight: 600; color: #333; margin-bottom: 5px; } .status { font-size: 14px; color: #666; font-weight: 500; } .messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 16px; } .message { max-width: 80%; padding: 12px 16px; border-radius: 18px; font-size: 15px; line-height: 1.4; word-wrap: break-word; } .user-message { background: linear-gradient(135deg, #667eea, #764ba2); color: white; align-self: flex-end; border-bottom-right-radius: 4px; } .ai-message { background: #f1f3f4; color: #333; align-self: flex-start; border-bottom-left-radius: 4px; } .input-container { padding: 20px; background: rgba(255, 255, 255, 0.1); border-top: 1px solid rgba(255, 255, 255, 0.2); display: flex; gap: 12px; } #messageInput { flex: 1; padding: 12px 16px; border: none; border-radius: 25px; background: white; font-size: 15px; outline: none; box-shadow: 0 2px 10px rgba(0,0,0,0.1); } #messageInput::placeholder { color: #999; } #sendButton { padding: 12px 24px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; border-radius: 25px; cursor: pointer; font-size: 15px; font-weight: 600; transition: all 0.2s ease; box-shadow: 0 2px 10px rgba(0,0,0,0.1); } #sendButton:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 15px rgba(0,0,0,0.2); } #sendButton:disabled { background: #ccc; cursor: not-allowed; transform: none; } .messages::-webkit-scrollbar { width: 6px; } .messages::-webkit-scrollbar-track { background: transparent; } .messages::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.2); border-radius: 3px; }
```

----------------------------------------

TITLE: Cloning the Repository - Bash
DESCRIPTION: This command clones the project repository from the specified URL and then changes the current directory into the newly cloned project folder, preparing for dependency installation.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-google-calendar/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
git clone [REPOSITORY_URL]
cd pocket-google-calendar
```

----------------------------------------

TITLE: Updating Multi-Step Progress Indicators - JavaScript
DESCRIPTION: This function visually updates a series of step indicators (e.g., 1, 2, 3) to reflect the current stage of a process. It marks previous steps as 'completed' with a checkmark, the current step as 'active' or 'completed', and future steps with their number.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/static/progress.html#_snippet_6

LANGUAGE: JavaScript
CODE:
```
function updateStepIndicator(step, completed = false) {
  // Reset all steps
  for (let i = 1; i <= 3; i++) {
    const stepElement = document.getElementById(`step${i}`);
    stepElement.className = 'step-circle';
    if (i < step) {
      stepElement.classList.add('completed');
      stepElement.innerHTML = '✓';
    } else if (i === step) {
      stepElement.classList.add(completed ? 'completed' : 'active');
      stepElement.innerHTML = completed ? '✓' : i;
    } else {
      stepElement.innerHTML = i;
    }
  }
}
```

----------------------------------------

TITLE: Client Log: PocketFlow A2A Request and Response
DESCRIPTION: This log snippet shows the client-side interaction with the PocketFlow A2A server, detailing the connection, the user's question input, the JSON-RPC request sent to the server, and the subsequent JSON-RPC response received from the server. It provides a view of the communication from the client's perspective.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-a2a/README.md#_snippet_6

LANGUAGE: Log
CODE:
```
Connecting to agent at: http://localhost:10003
Using Session ID: f3e12b8424c44241be881cd4bb8a269f

Enter your question (:q or quit to exit) > Who won the Nobel Prize in Physics 2024?
Sending task 46c3ce7b941a4fff9b8e3b644d6db5f4...
2025-04-12 17:20:57,643 - A2AClient - INFO - -> Sending Request (ID: d3f3fb93350d47d9a94ca12bb62b656b, Method: tasks/send):
{
  "jsonrpc": "2.0",
  "id": "d3f3fb93350d47d9a94ca12bb62b656b",
  "method": "tasks/send",
  "params": {
    "id": "46c3ce7b941a4fff9b8e3b644d6db5f4",
    "sessionId": "f3e12b8424c44241be881cd4bb8a269f",
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "Who won the Nobel Prize in Physics 2024?"
        }
      ]
    },
    "acceptedOutputModes": [
      "text",
      "text/plain"
    ]
  }
}
2025-04-12 17:21:03,835 - httpx - INFO - HTTP Request: POST http://localhost:10003 "HTTP/1.1 200 OK"
2025-04-12 17:21:03,836 - A2AClient - INFO - <- Received HTTP Status 200 for Request (ID: d3f3fb93350d47d9a94ca12bb62b656b)
2025-04-12 17:21:03,836 - A2AClient - INFO - <- Received Success Response (ID: d3f3fb93350d47d9a94ca12bb62b656b):
{
  "jsonrpc": "2.0",
  "id": "d3f3fb93350d47d9a94ca12bb62b656b",
  "result": {
    "id": "46c3ce7b941a4fff9b8e3b644d6db5f4",
    "sessionId": "f3e12b8424c44241be881cd4bb8a269f",
    "status": {
      "state": "completed",
      "timestamp": "2025-04-12T17:21:03.834542"
    },
    "artifacts": [
      {
        "parts": [
          {
            "type": "text",
```

----------------------------------------

TITLE: Generated SQL Query
DESCRIPTION: This SQL query is generated by the text-to-SQL workflow to count the total number of products within each category in the 'products' table.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-text2sql/README.md#_snippet_5

LANGUAGE: SQL
CODE:
```
SELECT category, COUNT(*) AS total_products
FROM products
GROUP BY category
```

----------------------------------------

TITLE: Creating Graph Links with Arrowheads (D3.js)
DESCRIPTION: Selects and appends 'path' elements for graph links based on the provided data. Configures stroke width, color, and adds an arrowhead marker.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_3

LANGUAGE: javascript
CODE:
```
const link = svg.append("g")
  .attr("class", "links")
  .selectAll("path")
  .data(data.links)
  .enter()
  .append("path")
  .attr("stroke-width", 2)
  .attr("stroke", "#999")
  .attr("marker-end", "url(#arrowhead)");
```

----------------------------------------

TITLE: Position D3.js Group Link Labels
DESCRIPTION: This code updates the position of text labels associated with group links in a D3.js visualization. It places each label near the midpoint of the line connecting the centers of the source and target groups.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_14

LANGUAGE: javascript
CODE:
```
}); // Update group link labels groupLinkLabel.attr("x", d => { const sourceGroup = groups[d.source]; const targetGroup = groups[d.target]; if (!sourceGroup || !targetGroup) return 0; return (sourceGroup.centerX + targetGroup.centerX) / 2; })
 .attr("y", d => { const sourceGroup = groups[d.source]; const targetGroup = groups[d.target]; if (!sourceGroup || !targetGroup) return 0; return (sourceGroup.centerY + targetGroup.centerY) / 2 - 10; });
```

----------------------------------------

TITLE: Creating Group Link Labels (D3.js)
DESCRIPTION: Selects and appends 'text' elements to label the group links. The text content is the 'action' property of the group link data.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_6

LANGUAGE: javascript
CODE:
```
const groupLinkLabel = svg.append("g")
  .attr("class", "group-link-labels")
  .selectAll("text")
  .data(data.group_links || [])
  .enter()
  .append("text")
  .text(d => d.action)
  .attr("font-size", "11px")
  .attr("font-weight", "bold")
  .attr("fill", "#333");
```

----------------------------------------

TITLE: Creating Group Labels (D3.js)
DESCRIPTION: Selects and appends 'text' elements to label the group containers. The text content is the 'name' property of the group data.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_7

LANGUAGE: javascript
CODE:
```
const groupLabels = svg.append("g")
  .attr("class", "group-labels")
  .selectAll("text")
  .data(Object.values(groups))
  .enter()
  .append("text")
  .attr("class", "group-label")
  .text(d => d.name)
  .attr("fill", d => d3.color(color(d.id)).darker());
```

----------------------------------------

TITLE: Starting the A2A Server for PocketFlow Agent
DESCRIPTION: This command starts the A2A server, which hosts the PocketFlow agent and exposes it via the A2A protocol on `http://localhost:10003`. The server listens for incoming A2A requests from clients.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-a2a/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
python a2a_server.py --port 10003
```

----------------------------------------

TITLE: PocketFlow Code Generator Workflow Diagram
DESCRIPTION: This Mermaid flowchart visually represents the sequential steps of the PocketFlow code generation and testing process. It illustrates the flow from problem input through test generation, function implementation, test execution, and the revision loop until all tests pass.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-code-generator/doc/design.md#_snippet_0

LANGUAGE: mermaid
CODE:
```
flowchart TD
    start[Problem Input] --> generateTests[Generate Test Cases]
    generateTests --> implement[Implement Function]
    implement --> runTests[Run Tests - Batch]
    runTests --> decision{All Tests Pass?}
    decision -->|Yes| success[Success!]
    decision -->|No| revise[Revise]
    revise --> runTests
```

----------------------------------------

TITLE: Testing Anthropic API Key
DESCRIPTION: Executes a Python script to verify that the configured Anthropic API key is correctly set up and functional, ensuring connectivity to the LLM service.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-code-generator/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python utils/call_llm.py
```

----------------------------------------

TITLE: Running Custom Chain-of-Thought Problem
DESCRIPTION: This command allows you to provide your own complex reasoning problem to the Chain-of-Thought system. Replace 'Your complex reasoning problem here' with the specific problem you want the LLM to solve using the structured reasoning process.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_4

LANGUAGE: Bash
CODE:
```
python main.py --"Your complex reasoning problem here"
```

----------------------------------------

TITLE: Running the PocketFlow BatchNode Example (Bash)
DESCRIPTION: This command executes the main entry point of the PocketFlow BatchNode example. It initiates the CSV processing flow, which reads a large CSV file, processes it in chunks, and aggregates the results.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch-node/README.md#_snippet_1

LANGUAGE: Bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Running Default Test Problem (Bash)
DESCRIPTION: Executes the `main.py` script without any additional arguments, running a predefined test problem. This command serves as a quick way to verify the project setup and observe the majority voting mechanism in action with a standard example.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-majority-vote/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Illustrating TranslateTextNode Flow - Mermaid
DESCRIPTION: This Mermaid diagram visually represents the `TranslateTextNode`, a key component in the PocketFlow implementation. It shows the node responsible for processing batches of translation requests.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/README.md#_snippet_3

LANGUAGE: mermaid
CODE:
```
flowchart LR
    batch[TranslateTextNode]
```

----------------------------------------

TITLE: Running the Web Search Tool
DESCRIPTION: This command executes the main script of the web search tool. After running, the user will be prompted to enter a search query and specify the number of results to fetch.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-search/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Running Default Chain-of-Thought Example
DESCRIPTION: This command executes the main project script ('main.py') without any arguments. It will run the Chain-of-Thought process using a predefined, default reasoning problem, demonstrating the system's core functionality.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_3

LANGUAGE: Bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Running the PocketFlow BatchFlow Example
DESCRIPTION: This command executes the main entry point of the PocketFlow BatchFlow example. It initiates the image processing workflow, applying various filters to multiple images as defined in the application logic.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch-flow/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Setting Anthropic API Key Environment Variable
DESCRIPTION: This command sets the `ANTHROPIC_API_KEY` environment variable, which is required for the application to authenticate with the Anthropic Claude API for joke generation. Replace `your-anthropic-api-key-here` with your actual API key.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-cmd-hitl/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export ANTHROPIC_API_KEY="your-anthropic-api-key-here"
```

----------------------------------------

TITLE: Setting Anthropic API Key - Bash
DESCRIPTION: This command sets the `ANTHROPIC_API_KEY` environment variable, which is crucial for authenticating requests to the Anthropic LLM. Users must replace the placeholder with their actual API key.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export ANTHROPIC_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Setting OpenAI API Key Environment Variable
DESCRIPTION: This command sets the `OPENAI_API_KEY` environment variable, which is required for the application to authenticate with the OpenAI API. Replace `your_api_key_here` with your actual API key.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-workflow/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY=your_api_key_here
```

----------------------------------------

TITLE: Setting OpenAI API Key - Bash
DESCRIPTION: This command sets the OpenAI API key as an environment variable, which is a prerequisite for the application to authenticate with the OpenAI API and generate LLM responses. Replace 'your-openai-api-key' with your actual key.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-websocket/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY="your-openai-api-key"
```

----------------------------------------

TITLE: Setting OpenAI API Key (Bash)
DESCRIPTION: This snippet shows how to set the OpenAI API key as an environment variable in a Bash shell. This key is required for the application to authenticate with the OpenAI API for language model interactions.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-chat-memory/README.md#_snippet_0

LANGUAGE: Bash
CODE:
```
export OPENAI_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Installing Dependencies with Pipenv - Bash
DESCRIPTION: This command uses Pipenv to install all project dependencies specified in the `Pipfile`. Pipenv automatically creates and manages a virtual environment for the project.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-google-calendar/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
pipenv install
```

----------------------------------------

TITLE: Installing Dependencies and Running Application - Bash
DESCRIPTION: These commands install the necessary Python dependencies listed in 'requirements.txt' and then execute the main application script 'main.py'. This is the standard procedure for setting up and running a Python project after cloning its repository.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-chat/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Installing Dependencies (Bash)
DESCRIPTION: Installs the required Python packages listed in the `requirements.txt` file using pip. This is a necessary setup step before running the application.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-map-reduce/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Installing Python Dependencies
DESCRIPTION: This command installs all required Python packages listed in the `requirements.txt` file, which are necessary for the web crawler to function.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-crawler/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Printing Summaries in Python
DESCRIPTION: This Python snippet iterates through a dictionary of summaries, likely stored in a 'shared' object, and prints each filename followed by its corresponding summary. It's used for displaying results after a process.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_6

LANGUAGE: Python
CODE:
```
print("Summaries:")
for filename, summary in shared["summaries"].items():
    print(f"\n{filename}:")
    print(summary)
```

----------------------------------------

TITLE: Simplified Generating Function Equation for State 2
DESCRIPTION: This snippet shows the simplified form of the generating function equation for State 2, G₂(z), after substituting G₃(z) = 1. This simplification is a step towards solving the system of equations for the generating functions.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_7

LANGUAGE: Mathematics
CODE:
```
G₂(z) = z·(4/6·G₀(z) + 1/6·G₁(z) + 1/6)
```

----------------------------------------

TITLE: Derived Equation for G₀(z) in terms of G₁(z)
DESCRIPTION: This equation, labeled (1), is derived by isolating G₀(z) from its initial definition, expressing it in terms of G₁(z). This is the first step in algebraically solving the system of generating function equations.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_8

LANGUAGE: Mathematics
CODE:
```
G₀(z) = (z/6·G₁(z))/(1 - 5z/6)
```

----------------------------------------

TITLE: Derived Equation for G₁(z) after Substitution
DESCRIPTION: This equation, labeled (4), is the result of substituting equation (3) (for G₂(z)) into equation (2) (for G₁(z)). This step further reduces the system, expressing G₁(z) in terms of G₀(z) and 'z' only, moving closer to a closed-form solution for G₀(z).
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_11

LANGUAGE: Mathematics
CODE:
```
G₁(z) = (4z/6·G₀(z)(1 + z/6) + z²/36)/(1 - z/6 - z²/36)
```

----------------------------------------

TITLE: Derived Equation for G₁(z) in terms of G₀(z) and G₂(z)
DESCRIPTION: This equation, labeled (2), is derived by rearranging the initial definition of G₁(z). It expresses G₁(z) in a form that facilitates substitution and further algebraic manipulation to solve the system of generating function equations.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_9

LANGUAGE: Mathematics
CODE:
```
G₁(z)(1 - z/6) = 4z/6·G₀(z) + z/6·G₂(z)
```

----------------------------------------

TITLE: Example Application Output - Console
DESCRIPTION: This snippet illustrates the expected console output when the application is run. It shows the listing of configured calendars and a confirmation message for a successfully created event, including its ID.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-google-calendar/README.md#_snippet_5

LANGUAGE: text
CODE:
```
=== Listing your calendars ===
- Primary Calendar
- Work
- Personal

=== Creating an example event ===
Event created successfully!
Event ID: abc123xyz
```

----------------------------------------

TITLE: Derived Equation for G₂(z) in terms of G₀(z) and G₁(z)
DESCRIPTION: This equation, labeled (3), is the explicit form of G₂(z) after distributing 'z' and substituting G₃(z)=1. It is used for substitution into other equations to reduce the number of unknown generating functions.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_10

LANGUAGE: Mathematics
CODE:
```
G₂(z) = 4z/6·G₀(z) + z/6·G₁(z) + z/6
```

----------------------------------------

TITLE: Initial Generating Function Equations for Markov States
DESCRIPTION: These equations define the generating functions G₀(z), G₁(z), G₂(z), and G₃(z) for reaching the success state (State 3) from each respective starting state. Each equation accounts for the probability of transitioning to a new state after one roll (represented by 'z') and the subsequent generating function from that new state. G₃(z) is 1 as it's the absorbing success state.
SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_6

LANGUAGE: Mathematics
CODE:
```
G₃(z) = 1
G₀(z) = z·(5/6·G₀(z) + 1/6·G₁(z))
G₁(z) = z·(4/6·G₀(z) + 1/6·G₁(z) + 1/6·G₂(z))
G₂(z) = z·(4/6·G₀(z) + 1/6·G₁(z) + 1/6·G₃(z))
```