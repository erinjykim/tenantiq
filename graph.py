from langgraph.graph import StateGraph, END
from state import TenantIQState
from agents.intake import intake_agent
from agents.retrieval import retrieval_agent
from agents.reasoning import reasoning_agent
from agents.skeptic import skeptic_agent
from agents.synthesis import synthesis_agent

def build_graph():
    # create the graph with your state schema
    graph = StateGraph(TenantIQState)
    
    # add each agent as a node
    graph.add_node("intake", intake_agent)
    graph.add_node("retrieval", retrieval_agent)
    graph.add_node("reasoning", reasoning_agent)
    graph.add_node("skeptic", skeptic_agent)
    graph.add_node("synthesis", synthesis_agent)
    
    # define the execution order with edges
    graph.set_entry_point("intake")
    graph.add_edge("intake", "retrieval")
    graph.add_edge("retrieval", "reasoning")
    graph.add_edge("reasoning", "skeptic")
    graph.add_edge("skeptic", "synthesis")
    graph.add_edge("synthesis", END)
    
    return graph.compile()

# compile once at import time
tenantiq_graph = build_graph()