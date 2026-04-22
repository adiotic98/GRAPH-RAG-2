 
import asyncio
from openai import AsyncAzureOpenAI
import os

from agents.mcp.server import MCPServerStdio
from agents import set_default_openai_client,set_tracing_disabled

from agents import Agent, Runner
import ssl,httpx
import urllib3
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context=ssl._create_unverified_context

os.environ['CURL_CA_BUNDLE'] = ''
os.environ['PYTHONHTTPSVERIFY'] = '0'
AZURE_OPENAI_API_KEY="f0e56505e5594c9db822a6e7addc7209"
AZURE_OPENAI_ENDPOINT="https://ims-openai-qa.openai.azure.com/"
AZURE_OPENAI_API_VERSION="2024-02-15-preview"
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

set_tracing_disabled(True)
azure_client = AsyncAzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=AZURE_OPENAI_API_VERSION,
    max_retries=5,
    http_client=httpx.AsyncClient(verify=False,proxy=None)
)
set_default_openai_client(azure_client)
print(" Azure OpenAI client configured for Agents SDK")

async def main():
    async with MCPServerStdio(
        params={
            "command": "mcp-neo4j-memory",
            "args": [],
            "env": {
                "NEO4J_URI": "neo4j://awsaidnval000z.jnj.com:7687",
                "NEO4J_USERNAME": "neo4j",
                "NEO4J_PASSWORD": "MVP2026!",
                "NEO4J_DATABASE": "newone",
            },
        },
        client_session_timeout_seconds=30,
    ) as mcp_server:
        await mcp_server.connect()
        print("MCP server session active")
        
        tools = await mcp_server.list_tools()
        
        print("Tools count:", len(tools))

        # for tool in tools:
        #     if tool.name=="read_graph":
        #         res=await tool.call({})
        #         print(res)
        
        
        # for tool in tools:
        #     if tool.name == "search_memories":
        #         res = await tool.call({"query": "death"})
        #         print(res)
    
        try:
            response = await azure_client.chat.completions.create(
            model="iMS_GPT4o_QA",
            messages=[{"role": "user", "content": "test"}]
        )
            print(" Model accessible:", response.choices[0].message.content[:50])
        except Exception as e:
            print(" Model error:", e)
        
        print("First 10 tool names:", [t.name for t in tools[:10]])
        
        
    #async def mcp_agent_query(query: str, prior_context: str = ""):
        #async with mcp_server:
        agent = Agent(
                        name="GraphRAG-MCP-Agent",
            instructions=f"""You are a biomedical data assistant with access to a Neo4j memory graph.

IMPORTANT RULES:
1. ALWAYS use the MCP tools provided — do not answer from general knowledge alone.
2. To STORE data: use create_entities first, then add_observations to attach stats.
3. To RETRIEVE data: use search_memories or find_memories_by_name first, then read_graph if needed.
4. Always confirm which tool you used and what it returned.
5. If the graph is empty, say so explicitly — do not make up data.
6. Entity names must be specific (e.g., 'ADA_Week16_Cohort', not just 'study').

Tool usage instructions:
- create_entities: provide a list of entities, each with a name, entityType, and list of observations
- add_observations: provide entityName and a list of observation contents to attach
- search_memories: provide a query string to search stored memories
- find_memories_by_name: provide the exact entity name to look up
- read_graph: use for Cypher-style graph traversal queries on the Neo4j database""",
            
            

            


            model=OpenAIChatCompletionsModel(
            model="iMS_GPT4o_QA",
            openai_client=azure_client   # ← pass client explicitly
    ),
            mcp_servers=[mcp_server],  # Enables all 9 tools
        )
        print("reading existing graph details")
        try :
            check=await Runner.run(agent,"use read_graph tool to show all entities stored in graph.List every node and It's property")
        except Exception as e:
            print(f"Graph read error:{e}")
        try:
            result = await Runner.run(agent, "How many deaths were reported?")
            print(result.final_output)
            
        except Exception as e:
            print(f"AGENT response 1:{e}")
        # print(result.final_output)
        # result2=await Runner.run(agent,"total death is mentioned in database I want to know ")
        # print(result2.final_output)
            # return result.final_output

# Test multi-turn memory
    #print(await mcp_agent_query("Subjects who first became ADA at week 16: store key stats (mean trough week 36)."))
    #print(await mcp_agent_query("Recall ADA week 16 subjects' trough stats from memory."))




    print("MCP server started and connected")

if __name__ == "__main__":
    asyncio.run(main())
