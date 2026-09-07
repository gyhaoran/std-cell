"""Executable teaching graph models, not LibreCell algorithm implementations."""
import heapq
import json
from collections import Counter


def dijkstra(graph, start, goal, penalties=None):
    penalties = penalties or {}
    distance, previous = {start: 0}, {}
    heap = [(0, start)]
    while heap:
        cost, node = heapq.heappop(heap)
        if cost != distance[node]:
            continue
        if node == goal:
            path = [goal]
            while path[-1] != start:
                path.append(previous[path[-1]])
            return cost, path[::-1]
        for neighbor, weight in graph[node].items():
            candidate = cost + weight + penalties.get(neighbor, 0)
            if candidate < distance.get(neighbor, float('inf')):
                distance[neighbor], previous[neighbor] = candidate, node
                heapq.heappush(heap, (candidate, neighbor))
    raise ValueError('no path')


def euler_trails(edges, start):
    # Edges have distinct IDs even when the endpoints are equal (parallel MOS).
    result = []
    def visit(node, used, gates, nets):
        if len(used) == len(edges):
            result.append({'gates': gates, 'nets': nets})
            return
        for i, (u, v, gate) in enumerate(edges):
            if i not in used and node in (u, v):
                other = v if node == u else u
                visit(other, used | {i}, gates+[gate], nets+[other])
    visit(start, set(), [], [start])
    return result


def main():
    n = euler_trails([('VSS','X','A'),('X','Y','B')], 'VSS')
    p = euler_trails([('VDD','Y','A'),('VDD','Y','B')], 'VDD')
    common = sorted({tuple(t['gates']) for t in n} & {tuple(t['gates']) for t in p})
    assert common == [('A','B')]
    graph = {'S':{'A':1,'B':3}, 'A':{'T':9}, 'B':{'C':1}, 'C':{'T':1}, 'T':{}}
    cost, path = dijkstra(graph, 'S','T')
    assert (cost, path) == (5,['S','B','C','T'])
    grid = {(x,y): {} for x in range(5) for y in range(5) if (x,y) != (2,0)}
    for x,y in grid:
        for point in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
            if point in grid:
                grid[x,y][point] = 1
    a_cost, a = dijkstra(grid,(0,1),(4,1))
    b_cost, b = dijkstra(grid,(1,0),(3,0))
    shared_before = sorted(set(a)&set(b))
    assert shared_before == [(1,1),(2,1),(3,1)]
    new_cost, new_a = dijkstra(grid,(0,1),(4,1),{point:10 for point in b})
    assert not set(new_a)&set(b)
    assert (a_cost,b_cost,new_cost) == (4,4,6)
    counts = Counter(new_a+b)
    assert max(counts.values()) == 1
    print(json.dumps({'nand_n_trails':n,'nand_p_trails':p,'common_gate_order':common,'weighted_path':path,'weighted_cost':cost,'route_a_before':a,'route_b':b,'shared_nodes_before':shared_before,'route_a_after':new_a,'route_costs':[a_cost,b_cost,new_cost],'scope':'node-capacity teaching example, not PathFinder source'},indent=2))
    print('PASS: Euler, weighted shortest path, capacity conflict and reroute')


if __name__ == '__main__':
    main()
