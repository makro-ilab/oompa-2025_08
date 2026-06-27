from oompa_types.action.action import Action
from oompa_types.goal_network.goal import Goal
from oompa_types.goal_network.gtn_node import GTNNode


class AbstractGTNNode[NODE_T](GTNNode[NODE_T]):
    def __init__(self, content: NODE_T):
        self.content = content

    def get_content(self) -> NODE_T:
        return self.content

    def __hash__(self) -> int:
        return id(self)


class GoalNode(AbstractGTNNode[Goal]):
    pass


class ActionNode(AbstractGTNNode[Action]):
    pass


class TaskNode(AbstractGTNNode):
    def __init__(self):
        raise NotImplementedError()
