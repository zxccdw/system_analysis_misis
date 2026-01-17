import json
from math import isclose

def main(LVinput, LVoutput, rules, T, verbose=False):
    EPSILON = 1e-9

    def log_msg(*args):
        if verbose:
            print("[LOG]", *args)

    def decode_lv(json_data):
        content = json.loads(json_data) if isinstance(json_data, str) else json_data
        
        terms_list = []
        if isinstance(content, dict):
            for val in content.values():
                if isinstance(val, list):
                    terms_list = val
                    break
        elif isinstance(content, list):
            terms_list = content

        parsed_vars = {}
        for term in terms_list:
            term_id = term.get('id')
            raw_points = term.get('points', [])
            sorted_points = sorted([(float(x), float(y)) for x, y in raw_points], key=lambda p: p[0])
            parsed_vars[term_id] = sorted_points
        return parsed_vars

    def get_membership(points, x_val):
        if not points:
            return 0.0
        x_val = float(x_val)
        
        if x_val <= points[0][0]:
            return float(points[0][1])
        if x_val >= points[-1][0]:
            return float(points[-1][1])

        for i in range(len(points) - 1):
            px1, py1 = points[i]
            px2, py2 = points[i+1]
            
            if px1 <= x_val <= px2:
                if isclose(px2, px1):
                    return float(py2)
                factor = (x_val - px1) / (px2 - px1)
                return float(py1 + (py2 - py1) * factor)
        return 0.0

    def normalize_rules(rules_input):
        data = json.loads(rules_input) if isinstance(rules_input, str) else rules_input
        normalized = []

        if isinstance(data, dict):
            for key, val in data.items():
                inputs = [k.strip() for k in str(key).split(',') if k.strip()]
                for inp in inputs:
                    normalized.append((inp, val))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    normalized.append((item[0], item[1]))
                elif isinstance(item, dict):
                    if 'if' in item and 'then' in item:
                        normalized.append((item['if'], item['then']))
                    elif 'from' in item and 'to' in item:
                        normalized.append((item['from'], item['to']))
                    elif 'input' in item and 'output' in item:
                        normalized.append((item['input'], item['output']))
                    else:
                        keys = list(item.keys())
                        if len(keys) >= 2:
                            normalized.append((item[keys[0]], item[keys[1]]))
        
        return [(str(a), str(b)) for a, b in normalized]

    def find_x_intersect(p1, p2, level):
        x1, y1 = p1
        x2, y2 = p2
        if isclose(y2, y1):
            return None
        t = (level - y1) / (y2 - y1)
        if -1e-12 <= t <= 1 + 1e-12:
            return x1 + t * (x2 - x1)
        return None

    def clip_shape(points, level):
        if not points:
            return []
        level = float(level)
        temp_points = []
        
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i+1]
            
            temp_points.append((float(p1[0]), min(p1[1], level)))
            
            if (p1[1] - level) * (p2[1] - level) < -EPSILON:
                ix = find_x_intersect(p1, p2, level)
                if ix is not None:
                    temp_points.append((float(ix), level))
        
        last = points[-1]
        temp_points.append((float(last[0]), min(last[1], level)))
        
        temp_points.sort(key=lambda p: p[0])

        unique_points = []
        for x, y in temp_points:
            if unique_points and isclose(unique_points[-1][0], x, abs_tol=EPSILON):
                unique_points[-1] = (unique_points[-1][0], max(unique_points[-1][1], y))
            else:
                unique_points.append((x, y))

        final_points = []
        idx = 0
        n = len(unique_points)
        while idx < n:
            curr_x, curr_y = unique_points[idx]
            if isclose(curr_y, level, abs_tol=EPSILON):
                j = idx
                while j + 1 < n and isclose(unique_points[j+1][1], level, abs_tol=EPSILON):
                    j += 1
                
                final_points.append((curr_x, level))
                if not isclose(unique_points[j][0], curr_x, abs_tol=EPSILON):
                    final_points.append((unique_points[j][0], level))
                idx = j + 1
            else:
                final_points.append((curr_x, curr_y))
                idx += 1
        
        result = []
        for p in final_points:
            if result and isclose(result[-1][0], p[0], abs_tol=1e-12) and isclose(result[-1][1], p[1], abs_tol=1e-12):
                continue
            result.append(p)
        return result

    inputs_map = decode_lv(LVinput)
    outputs_map = decode_lv(LVoutput)
    rules_list = normalize_rules(rules)

    input_memberships = {name: get_membership(pts, T) for name, pts in inputs_map.items()}
    
    log_msg("T =", float(T))
    log_msg("Степени входа =", json.dumps(input_memberships, ensure_ascii=False))

    output_levels = {k: 0.0 for k in outputs_map}
    for inp_term, out_term in rules_list:
        deg = input_memberships.get(inp_term, 0.0)
        if deg > output_levels.get(out_term, 0.0):
            output_levels[out_term] = float(deg)
    
    log_msg("Alpha уровни выходов =", json.dumps(output_levels, ensure_ascii=False))

    clipped_functions = {}
    for name, points in outputs_map.items():
        alpha = output_levels.get(name, 0.0)
        if alpha <= EPSILON:
            clipped_functions[name] = []
            log_msg(f"Clipping[{name}]: пропущен (0)")
        else:
            clipped_pts = clip_shape(points, alpha)
            clipped_functions[name] = clipped_pts
            debug_pts = [(round(x, 6), round(y, 6)) for x, y in clipped_pts]
            log_msg(f"Clipping[{name}]:", debug_pts)

    all_heights = [pt[1] for shape in clipped_functions.values() for pt in shape]
    global_max_y = max(all_heights) if all_heights else 0.0
    log_msg("Global Max Y =", round(global_max_y, 6))

    if global_max_y <= EPSILON:
        centers = []
        for pts in outputs_map.values():
            if pts:
                centers.append((pts[0][0] + pts[-1][0]) / 2.0)
        fallback_val = float(sum(centers) / len(centers)) if centers else 0.0
        log_msg("Fallback centroid =", round(fallback_val, 6))
        return fallback_val

    max_intervals = []
    for name, pts in clipped_functions.items():
        if not pts:
            continue
        i = 0
        n_pts = len(pts)
        while i < n_pts:
            if isclose(pts[i][1], global_max_y, abs_tol=1e-7):
                j = i
                while j + 1 < n_pts and isclose(pts[j+1][1], global_max_y, abs_tol=1e-7):
                    j += 1
                
                left_bound = float(pts[i][0])
                right_bound = float(pts[j][0])
                max_intervals.append((left_bound, right_bound))
                i = j + 1
            else:
                i += 1
    
    log_msg("Raw max intervals =", [(round(l, 6), round(r, 6)) for l, r in max_intervals])

    sorted_intervals = sorted(max_intervals, key=lambda x: x[0])
    merged_intervals = []
    for l, r in sorted_intervals:
        if not merged_intervals:
            merged_intervals.append([l, r])
        else:
            last = merged_intervals[-1]
            if l <= last[1] + EPSILON:
                last[1] = max(last[1], r)
            else:
                merged_intervals.append([l, r])
    
    final_intervals = [(float(a), float(b)) for a, b in merged_intervals]
    log_msg("Merged intervals =", [(round(a, 6), round(b, 6)) for a, b in final_intervals])

    total_len = sum(max(0.0, r - l) for l, r in final_intervals)
    log_msg("Total Length L =", round(total_len, 6))

    if total_len <= EPSILON:
        points_x = [(l + r) / 2.0 for l, r in final_intervals]
        if not points_x:
            xs_exact = []
            for pts in clipped_functions.values():
                for x, y in pts:
                    if isclose(y, global_max_y, abs_tol=1e-7):
                        xs_exact.append(x)
            if not xs_exact:
                return 0.0
            res = sum(xs_exact) / len(xs_exact)
            return float(res)
        
        res = sum(points_x) / len(points_x)
        log_msg("Degenerate centroid =", round(res, 6))
        return float(res)

    moment_sum = 0.0
    for l, r in final_intervals:
        moment_sum += (r * r - l * l)
    
    x_optimal = 0.5 * moment_sum / total_len
    log_msg("Moment sum =", round(moment_sum, 6))
    log_msg("Result X_opt =", round(x_optimal, 6))

    return float(x_optimal)


if __name__ == '__main__':
    print(main('''
{
    "температура": [
        {
            "id": "холодно",
            "points": [
                [0,1],
                [18,1],
                [22,0],
                [50,0]
            ]
        },
        {
            "id": "комфортно",
            "points": [
                [18,0],
                [22,1],
                [24,1],
                [26,0]
            ]
        },
        {
            "id": "жарко",
            "points": [
                [0,0],
                [24,0],
                [26,1],
                [50,1]
            ]
        }
    ]
}
''',
'''
{
  "управление": [
      {
        "id": "слабо",
        "points": [
            [0,0],
            [0,1],
            [5,1],
            [8,0]
        ]
      },
      {
        "id": "умеренно",
        "points": [
            [5,0],
            [8,1],
            [13,1],
            [16,0]
        ]
      },
      {
        "id": "интенсивно",
        "points": [
            [13,0],
            [18,1],
            [23,1],
            [26,0]
        ]
      }
  ]
}
''',
'''
{
  "холодно": "интенсивно",
  "комфортно": "умеренно",
  "жарко": "слабо"
}
''',
25, verbose=True))
