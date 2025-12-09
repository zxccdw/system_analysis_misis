import json
from typing import Union

Element = Union[int, str]
RankingElement = Union[Element, list[Element]]
Ranking = list[RankingElement]


def get_all_elements(ranking: Ranking) -> list[Element]:
    elements: list[Element] = []
    for item in ranking:
        if isinstance(item, list):
            elements.extend(item)
        else:
            elements.append(item)
    return elements


def get_positions(ranking: Ranking) -> dict[Element, int]:
    positions: dict[Element, int] = {}
    for pos, item in enumerate(ranking):
        if isinstance(item, list):
            for element in item:
                positions[element] = pos
        else:
            positions[item] = pos
    return positions


def build_strict_preference_matrix(
    elements: list[Element],
    positions: dict[Element, int]
) -> dict[Element, dict[Element, int]]:
    matrix: dict[Element, dict[Element, int]] = {}
    for i in elements:
        matrix[i] = {}
        for j in elements:
            matrix[i][j] = 1 if positions[i] < positions[j] else 0
    return matrix


def transpose(
    matrix: dict[Element, dict[Element, int]],
    elements: list[Element]
) -> dict[Element, dict[Element, int]]:
    result: dict[Element, dict[Element, int]] = {}
    for i in elements:
        result[i] = {}
        for j in elements:
            result[i][j] = matrix[j][i]
    return result


def matrix_and(
    m1: dict[Element, dict[Element, int]],
    m2: dict[Element, dict[Element, int]],
    elements: list[Element]
) -> dict[Element, dict[Element, int]]:
    result: dict[Element, dict[Element, int]] = {}
    for i in elements:
        result[i] = {}
        for j in elements:
            result[i][j] = m1[i][j] & m2[i][j]
    return result


def matrix_or(
    m1: dict[Element, dict[Element, int]],
    m2: dict[Element, dict[Element, int]],
    elements: list[Element]
) -> dict[Element, dict[Element, int]]:
    result: dict[Element, dict[Element, int]] = {}
    for i in elements:
        result[i] = {}
        for j in elements:
            result[i][j] = m1[i][j] | m2[i][j]
    return result


def find_contradiction_core(
    YA: dict[Element, dict[Element, int]],
    YB: dict[Element, dict[Element, int]],
    elements: list[Element]
) -> list[list[Element]]:
    core: list[list[Element]] = []
    n = len(elements)
    for i in range(n):
        for j in range(i + 1, n):
            ei, ej = elements[i], elements[j]
            # i лучше j в A, но j лучше i в B (или наоборот)
            if (YA[ei][ej] == 1 and YB[ej][ei] == 1) or \
               (YA[ej][ei] == 1 and YB[ei][ej] == 1):
                core.append([ei, ej])
    return core


def warshall_closure(
    E: dict[Element, dict[Element, int]],
    elements: list[Element]
) -> dict[Element, dict[Element, int]]:
    result: dict[Element, dict[Element, int]] = {}
    for i in elements:
        result[i] = {j: E[i][j] for j in elements}

    for k in elements:
        for i in elements:
            for j in elements:
                result[i][j] = result[i][j] | (result[i][k] & result[k][j])

    return result


def find_clusters_from_contradictions(
    elements: list[Element],
    contradiction_core: list[list[Element]]
) -> list[list[Element]]:
    E: dict[Element, dict[Element, int]] = {}
    for i in elements:
        E[i] = {j: (1 if i == j else 0) for j in elements}

    for pair in contradiction_core:
        i, j = pair[0], pair[1]
        E[i][j] = 1
        E[j][i] = 1

    E_star = warshall_closure(E, elements)

    visited: set[Element] = set()
    clusters: list[list[Element]] = []

    for start in elements:
        if start in visited:
            continue

        cluster: list[Element] = []
        for other in elements:
            if E_star[start][other] == 1:
                cluster.append(other)
                visited.add(other)

        if cluster:
            clusters.append(cluster)

    return clusters


def build_consensus_order_matrix(
    YA: dict[Element, dict[Element, int]],
    YB: dict[Element, dict[Element, int]],
    elements: list[Element]
) -> dict[Element, dict[Element, int]]:
    C: dict[Element, dict[Element, int]] = {}
    for i in elements:
        C[i] = {}
        for j in elements:
            # i не хуже j, если j не строго лучше i
            not_worse_in_A = 1 - YA[j][i]  # j не строго лучше i в A
            not_worse_in_B = 1 - YB[j][i]  # j не строго лучше i в B
            C[i][j] = not_worse_in_A & not_worse_in_B
    return C


def order_clusters(
    clusters: list[list[Element]],
    pos1: dict[Element, int],
    pos2: dict[Element, int]
) -> list[list[Element]]:
    def cluster_avg_pos(cluster: list[Element]) -> float:
        total = sum(pos1[e] + pos2[e] for e in cluster)
        return total / (2 * len(cluster))

    return sorted(clusters, key=cluster_avg_pos)


def format_ranking(clusters: list[list[Element]]) -> Ranking:
    result: Ranking = []
    for cluster in clusters:
        sorted_cluster = sorted(cluster, key=lambda x: (isinstance(x, str), x))
        if len(sorted_cluster) == 1:
            result.append(sorted_cluster[0])
        else:
            result.append(sorted_cluster)
    return result


def main(json_str1: str, json_str2: str) -> str:
    ranking1: Ranking = json.loads(json_str1)
    ranking2: Ranking = json.loads(json_str2)

    elements = get_all_elements(ranking1)
    pos1 = get_positions(ranking1)
    pos2 = get_positions(ranking2)

    YA = build_strict_preference_matrix(elements, pos1)
    YB = build_strict_preference_matrix(elements, pos2)

    # Этап 1: Ядро противоречий
    contradiction_core = find_contradiction_core(YA, YB, elements)

    # Этап 2: Согласованная кластерная ранжировка
    clusters = find_clusters_from_contradictions(elements, contradiction_core)
    ordered_clusters = order_clusters(clusters, pos1, pos2)
    consensus_ranking = format_ranking(ordered_clusters)

    result = {
        "core": contradiction_core,
        "ranking": consensus_ranking
    }

    return json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    ranking_a = '[1,[2,3],4,[5,6,7],8,9,10]'
    ranking_b = '[[1,2],[3,4,5],6,7,9,[8,10]]'

    result = main(ranking_a, ranking_b)
    print(f"Результат: {result}")
    print()
    print("Ожидаемое ядро противоречий: [[8, 9]]")
    print("Ожидаемая ранжировка:        [1, 2, 3, 4, 5, 6, 7, [8, 9], 10]")
