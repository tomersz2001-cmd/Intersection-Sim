# graph.py
import math


class Node:
    """A physical point on the map (Spawn point, Intersection, Exit)"""

    def __init__(self, node_id, x, y):
        self.id = node_id
        self.x = x
        self.y = y
        self.out_edges = []  # List of roads you can take from this node

    def add_out_edge(self, edge):
        self.out_edges.append(edge)


class Edge:
    """A road connecting two Nodes (Replaces the old Lane class)"""

    def __init__(self, edge_id, start_node, end_node, control_node=None):
        self.id = edge_id
        self.start_node = start_node
        self.end_node = end_node
        self.cars = []

        # --- AUTO-GENERATE WAYPOINTS ---
        # If we pass a 3rd "control node", it automatically builds a curved Bezier path!
        if control_node:
            self.waypoints = self._create_bezier(start_node, control_node, end_node)
        else:
            self.waypoints = [(start_node.x, start_node.y), (end_node.x, end_node.y)]

        self.length = self._calculate_length()

        # Tell the start node that this edge leaves from it
        self.start_node.add_out_edge(self)

    def _create_bezier(self, p0, p1, p2, num_points=20):
        """Generates a smooth curve for turning edges"""
        points = []
        for i in range(num_points):
            t = i / (num_points - 1)
            x = (1 - t) ** 2 * p0.x + 2 * (1 - t) * t * p1.x + t ** 2 * p2.x
            y = (1 - t) ** 2 * p0.y + 2 * (1 - t) * t * p1.y + t ** 2 * p2.y
            points.append((x, y))
        return points

    def _calculate_length(self):
        """Calculates the total distance of this edge (useful for A* pathfinding later)"""
        dist = 0.0
        for i in range(len(self.waypoints) - 1):
            x1, y1 = self.waypoints[i]
            x2, y2 = self.waypoints[i + 1]
            dist += math.hypot(x2 - x1, y2 - y1)
        return dist

    def add_car(self, car):
        self.cars.append(car)