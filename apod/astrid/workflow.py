from vellum.workflows import BaseWorkflow
from vellum.workflows.state import BaseState

from .agent import AstridAgent
from .inputs import Inputs


class AstridWorkflow(BaseWorkflow[Inputs, BaseState]):
    graph = AstridAgent

    class Outputs(BaseWorkflow.Outputs):
        response = AstridAgent.Outputs.text
