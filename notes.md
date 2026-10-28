* How this secures your multi-tenancy:

Instead of trying to magically intercept the tool call, 
we simply require workspace_id in the tool's schema (which you did in ai/tools.py), 
and then inject the actual workspace_id into the SystemMessage on every single turn of the graph. ]
The LLM will reliably pluck that ID from its system instructions and pass it into the tool call, ensuring data isolation.

from langchain_core.messages import HumanMessage, AIMessage - how do these work?