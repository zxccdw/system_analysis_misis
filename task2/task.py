from typing import Tuple, List
import csv
import math


def create_matrix(n: int) -> List[List[bool]]:
    return [[False] * n for _ in range(n)]


def clone_matrix(matrix: List[List[bool]]) -> List[List[bool]]:
    return [row[:] for row in matrix]


def transpose_matrix(matrix: List[List[bool]]) -> List[List[bool]]:
    n = len(matrix)
    result = create_matrix(n)
    for i in range(n):
        for j in range(n):
            result[j][i] = matrix[i][j]
    return result


def transitive_closure(adj: List[List[bool]]) -> List[List[bool]]:
    n = len(adj)
    closure = clone_matrix(adj)
    for k in range(n):
        for i in range(n):
            for j in range(n):
                closure[i][j] = closure[i][j] or (closure[i][k] and closure[k][j])
    return closure


def get_levels(root_idx: int, adj: List[List[bool]]) -> List[int]:
    n = len(adj)
    levels = [-1] * n
    queue = [root_idx]
    levels[root_idx] = 0

    while queue:
        v = queue.pop(0)
        for i in range(n):
            if adj[v][i] and levels[i] == -1:
                levels[i] = levels[v] + 1
                queue.append(i)

    return levels


def get_relations(s: str, e: str) -> Tuple[
    List[List[bool]],
    List[List[bool]],
    List[List[bool]],
    List[List[bool]],
    List[List[bool]]
]:
    edges = []
    with open(s, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            edges.append((int(row[0]), int(row[1])))

    vertices = sorted(set(v for edge in edges for v in edge))
    n = len(vertices)
    index = {v: i for i, v in enumerate(vertices)}

    adj = create_matrix(n)
    for a, b in edges:
        adj[index[a]][index[b]] = True

    r1 = clone_matrix(adj)

    r2 = transpose_matrix(r1)

    reachable = transitive_closure(adj)
    r3 = create_matrix(n)
    for i in range(n):
        for j in range(n):
            if reachable[i][j] and not r1[i][j]:
                r3[i][j] = True

    r4 = transpose_matrix(r3)

    root_idx = index[int(e)]
    levels = get_levels(root_idx, adj)
    r5 = create_matrix(n)
    for i in range(n):
        for j in range(n):
            if i != j and levels[i] != -1 and levels[i] == levels[j]:
                r5[i][j] = True

    return (r1, r2, r3, r4, r5)


def count_relations(matrix: List[List[bool]]) -> int:
    count = 0
    for row in matrix:
        for val in row:
            if val:
                count += 1
    return count


def calculate_entropy(relations: Tuple[List[List[bool]], ...]) -> float:
    n = len(relations[0])
    max_links = n - 1

    if max_links == 0:
        return 0.0

    total_entropy = 0.0

    for j in range(n):
        for relation in relations:
            outgoing_count = sum(1 for i in range(n) if relation[j][i])

            if outgoing_count > 0:
                p = outgoing_count / max_links
                h = -p * math.log2(p)
                total_entropy += h

    return total_entropy


def calculate_complexity(relations: Tuple[List[List[bool]], ...], entropy: float) -> float:
    n = len(relations[0])
    k = 5

    c = 1 / (math.e * math.log(2))
    h_ref = c * n * k

    if h_ref == 0:
        return 0.0

    return entropy / h_ref


def main(s: str, e: str) -> Tuple[float, float]:
    relations = get_relations(s, e)

    entropy = calculate_entropy(relations)
    complexity = calculate_complexity(relations, entropy)

    return (round(entropy, 1), round(complexity, 2))
