import argparse
import csv

def main(**kwargs):
    nodes = []
    mx_number_in_row = -1e9
    with open(kwargs["csv"], "r") as f:
        reader = csv.reader(f)
        for row in reader:
            a, b = map(int, row)
            mx_number_in_row = max(mx_number_in_row, a, b)
            nodes.append((a, b))
    matrix = [[0] * (mx_number_in_row + 1) for i in range(mx_number_in_row + 1)]
    for node in nodes:
        matrix[node[0]][node[1]] = 1
    return matrix


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=str)
    args = parser.parse_args()
    print(main(csv=args.csv))
