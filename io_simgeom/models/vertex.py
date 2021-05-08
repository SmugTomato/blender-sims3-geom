from typing import List


class Vertex:
    

    def __init__(self):
        self.position:      List[float]         = None
        self.normal:        List[float]         = None
        self.uv:            List[List[float]]   = None
        self.assignment:    List[int]           = None
        self.weights:       List[float]         = None
        self.tangent:       List[float]         = None
        self.tagvalue:      List[int]           = None
        self.vertex_id:     List[int]           = None
