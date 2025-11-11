"""
Enhancer Graph Definition
-------------------------
LangGraph pipeline for the Input Enhancer Agent.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from agents.input_enhancer import EnhancerState, generate_queries_and_domains


class EnhancerGraph:
    """Encapsulates the LangGraph for the Input Enhancer Agent."""

    def __init__(self):
        self.memory = MemorySaver()
        self.graph_builder = StateGraph(EnhancerState)

        # Define the flow
        self.graph_builder.add_node("enhance", generate_queries_and_domains)
        self.graph_builder.add_edge(START, "enhance")
        self.graph_builder.add_edge("enhance", END)

        # Compile the runnable graph
        self.graph = self.graph_builder.compile(checkpointer=self.memory)

    def invoke(self, initial_state, thread_id="default-session"):
        """Execute the enhancer graph."""
        return self.graph.invoke(initial_state, config={"configurable": {"thread_id": thread_id}})
