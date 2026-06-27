from typing import Protocol


class GTNNode[NODE_T](Protocol):
    def get_content(self) -> NODE_T: ...
