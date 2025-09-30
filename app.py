from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.errors import GraphRecursionError
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit

# Initialize FastAPI
app = FastAPI()

# Allow frontend (JS) to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request body
class ChatRequest(BaseModel):
    message: str

# Connect to DB
db = SQLDatabase.from_uri("sqlite:///argo.db")

# Initialize LLM
llm = ChatGroq(groq_api_key="give_your_groq_api_key_here", model_name="Gemma2-9b-It", temperature=0)

# Setup tools
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
tools = toolkit.get_tools()

# System prompt
system_message = """
You are an agent designed to interact with a SQLite database.

The database has 3 main tables:
- floats(id, platform_number)
- profiles(id, float_id, cycle_number, latitude, longitude, time)
- measurements(id, profile_id, pressure, temperature, salinity, time)

Relationships:
- A float can have many profiles (linked by profiles.float_id).
- A profile can have many measurements (linked by measurements.profile_id).

When the user asks about temperature, salinity, or pressure, you must query the
measurements table and JOIN with profiles if filtering by time, latitude, or longitude.

To filter by year or month, use SQLite functions like:
  strftime('%Y', measurements.time) and strftime('%m', measurements.time).

Do not invent tables or columns that do not exist.
""".format(
    dialect="SQLite",
    top_k=5,
)

# Create agent
agent_executor = create_react_agent(llm, tools, prompt=system_message)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.errors import GraphRecursionError

app = FastAPI()

# Allow CORS so frontend can call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://127.0.0.1:5500"] if serving via Live Server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Run query through your agent
        response_text = ""
        for step in agent_executor.stream(
            {"messages": [{"role": "user", "content": request.message}]},
            stream_mode="values",
            config={"recursion_limit": 10}  # Avoids GraphRecursionError
        ):
            response_text = step["messages"][-1].content

        return {"response": response_text}

    except GraphRecursionError:
        return {"response": "⚠️ The query was too complex. Please try rephrasing."}




'''You are an agent designed to interact with a SQLite database.

The database has 3 main tables:
- floats(id, platform_number)
- profiles(id, float_id, cycle_number, latitude, longitude, time)
- measurements(id, profile_id, pressure, temperature, salinity, time)

Relationships:
- A float can have many profiles (linked by profiles.float_id).
- A profile can have many measurements (linked by measurements.profile_id).

When the user asks about temperature, salinity, or pressure, you must query the
measurements table and JOIN with profiles if filtering by time, latitude, or longitude.

To filter by year or month, use SQLite functions like:
  strftime('%Y', measurements.time) and strftime('%m', measurements.time).

Do not invent tables or columns that do not exist.'''