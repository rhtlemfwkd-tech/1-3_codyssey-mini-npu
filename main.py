
import time
import json


# 1. MAC 연산
def mac(pattern, filter_data):
    score = 0

    for i in range(len(pattern)):
        for j in range(len(pattern[i])):
            score += pattern[i][j] * filter_data[i][j]

    return score


# 2. 연산 시간 측정
def benchmark(pattern, filter_data):
    total_time = 0

    for i in range(10):
        start = time.perf_counter()
        mac(pattern, filter_data)
        end = time.perf_counter()

        total_time += (end - start) * 1000

    return total_time / 10


# 3. 점수 비교
def classify(score_a, score_b, label_a, label_b):
    epsilon = 1e-9

    if abs(score_a - score_b) < epsilon:
        return "UNDECIDED"

    if score_a > score_b:
        return label_a

    return label_b


# 4. 3x3 행렬 입력
def input_matrix(name):
    matrix = []
    print(f"\n{name} 입력")

    for i in range(3):
        while True:
            row = input(f"{i + 1}번째 행: ")
            numbers = row.replace(",", " ").split()

            if len(numbers) != 3:
                print("입력 오류: 숫자를 3개 입력하세요.")
                continue

            try:
                result = []

                for number in numbers:
                    result.append(float(number))

                matrix.append(result)
                break

            except ValueError:
                print("입력 오류: 숫자만 입력하세요.")

    return matrix


# 5. 라벨 정규화
def normalize_label(label):
    label = label.strip().lower()

    if label == "+" or label == "cross":
        return "Cross"

    if label == "x":
        return "X"

    raise ValueError(f"알 수 없는 라벨: {label}")


# 6. 행렬 검증
def validate_matrix(matrix, n, name):
    if not isinstance(matrix, list) or len(matrix) != n:
        raise ValueError(f"{name}: 행 개수가 {n}개가 아닙니다.")

    for i in range(n):
        row = matrix[i]

        if not isinstance(row, list) or len(row) != n:
            raise ValueError(
                f"{name}: {i + 1}번째 행의 열 개수가 {n}개가 아닙니다."
            )

        for number in row:
            if type(number) not in (int, float):
                raise ValueError(f"{name}: 숫자가 아닌 값이 있습니다.")


# 7. 크기별 성능 분석
def print_benchmark_table():
    print("\n=== 크기별 성능 분석 ===")
    print("크기\t평균 시간(ms)\t연산 횟수")

    for n in [3, 5, 13, 25]:
        matrix = []

        for i in range(n):
            matrix.append([1] * n)

        average = benchmark(matrix, matrix)
        operations = n * n

        print(f"{n}x{n}\t{average:.6f}\t{operations}")


# 8. 사용자 입력 모드
def run_manual_mode():
    # 개발 중에만 True로 변경
    TEST_MODE = False

    if TEST_MODE:
        filter_a = [
            [0, 1, 0],
            [1, 1, 1],
            [0, 1, 0]
        ]

        filter_b = [
            [1, 0, 1],
            [0, 1, 0],
            [1, 0, 1]
        ]

        pattern = filter_a
        print("테스트 데이터 자동 적용")

    else:
        filter_a = input_matrix("필터 A")
        filter_b = input_matrix("필터 B")

        print("\n필터 저장 완료")

        pattern = input_matrix("입력 패턴")

    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)

    average = benchmark(pattern, filter_a)
    result = classify(score_a, score_b, "A", "B")

    print("\n=== MAC 결과 ===")
    print("A 점수:", score_a)
    print("B 점수:", score_b)
    print("판정 결과:", result)
    print(f"평균 연산 시간(10회): {average:.6f} ms")
    print("연산 횟수:", len(pattern) ** 2)


# 9. JSON 분석 모드
def run_json_mode():
    try:
        with open("data.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        filter_sets = data["filters"]
        patterns = data["patterns"]

        if not isinstance(filter_sets, dict) or not isinstance(patterns, dict):
            raise ValueError("filters와 patterns는 객체여야 합니다.")

    except (OSError, ValueError, KeyError, TypeError) as error:
        print("JSON 로드 오류:", error)
        return

    print("\n=== JSON 전체 패턴 분석 ===")

    total = 0
    passed = 0
    failures = []

    for key, value in patterns.items():
        total += 1

        try:
            # 패턴 키 분석
            parts = key.split("_")

            if (len(parts) != 3
                    or parts[0] != "size"
                    or not parts[2].isdigit()):
                raise ValueError("잘못된 패턴 키 형식")

            size = int(parts[1])

            # 필터와 패턴 선택
            filters = filter_sets[f"size_{size}"]
            pattern = value["input"]

            # 필터 라벨 정규화
            normalized = {}

            for label, matrix in filters.items():
                normalized[normalize_label(label)] = matrix

            cross_filter = normalized["Cross"]
            x_filter = normalized["X"]

            # 크기 검증
            validate_matrix(pattern, size, "패턴")
            validate_matrix(cross_filter, size, "Cross 필터")
            validate_matrix(x_filter, size, "X 필터")

            # MAC 연산
            cross_score = mac(pattern, cross_filter)
            x_score = mac(pattern, x_filter)

            # 결과 판정
            result = classify(
                cross_score, x_score, "Cross", "X"
            )
            expected = normalize_label(value["expected"])

            print(f"\n{key}")
            print("Cross 점수:", cross_score)
            print("X 점수:", x_score)

            if result == expected:
                print(f"판정: {result} | expected: {expected} | PASS")
                passed += 1

            else:
                if result == "UNDECIDED":
                    reason = (
                        f"epsilon 동점 처리: "
                        f"점수 차이 {abs(cross_score - x_score):.3g}, "
                        f"expected={expected}"
                    )
                else:
                    reason = f"판정 불일치: {result} != {expected}"

                print(f"판정: {result} | expected: {expected} | FAIL")
                failures.append((key, reason))

        except (ValueError, KeyError, TypeError,
                IndexError, AttributeError) as error:
            print(f"\n{key} | FAIL: {error}")
            failures.append((key, str(error)))

    # 성능 분석
    print_benchmark_table()

    # 전체 결과 요약
    print("\n=== 결과 요약 ===")
    print("전체 테스트:", total)
    print("통과:", passed)
    print("실패:", len(failures))

    if failures:
        print("\n실패 케이스:")

        for key, reason in failures:
            print(f"- {key}: {reason}")
# 10. 2차원->1차원 변환 함수 (보너스)
def flatten(matrix):
    result = []

    for row in matrix:
        for number in row:
            result.append(number)

    return result

# 11. 1차원 MAC 연산
def mac_1d(pattern, filter_data):
    score = 0

    for i in range(len(pattern)):
        score += pattern[i] * filter_data[i]

    return score

# 12. 1차원 MAC 테스트
def test_mac_1d():
    matrix = [
        [0, 1, 0],
        [1, 1, 1],
        [0, 1, 0]
    ]

    flat_matrix = flatten(matrix)

    score_2d = mac(matrix, matrix)
    score_1d = mac_1d(flat_matrix, flat_matrix)

    print("\n=== 1차원 MAC 테스트 ===")
    print("변환 결과:", flat_matrix)
    print("2차원 점수:", score_2d)
    print("1차원 점수:", score_1d)

    if abs(score_2d - score_1d) < 1e-9:
        print("PASS: 계산 결과 일치")
    else:
        print("FAIL: 계산 결과 불일치")

# 13. 1차원 MAC 연산 시간 측정
def measure_mac(func, pattern, filter_data, repeats=1000):
    start = time.perf_counter()

    for i in range(repeats):
        func(pattern, filter_data)

    end = time.perf_counter()

    average = (end - start) * 1000 / repeats

    return average

# 14. 1차원 MAC 성능 비교
def compare_mac_performance():
    print("\n=== 2D vs 1D MAC 성능 비교 ===")
    print("크기\t2D(ms)\t\t1D(ms)\t\t결과")

    for n in [3, 5, 13, 25]:
        # 같은 테스트 데이터 생성
        matrix = [[1] * n for i in range(n)]

        # 1차원 배열로 변환
        flat_matrix = flatten(matrix)

        # 계산 결과 검증
        score_2d = mac(matrix, matrix)
        score_1d = mac_1d(flat_matrix, flat_matrix)

        if abs(score_2d - score_1d) >= 1e-9:
            print(f"{n}x{n}: 점수 불일치 (FAIL)")
            continue

        # 동일한 횟수로 시간 측정
        time_2d = measure_mac(mac, matrix, matrix)
        time_1d = measure_mac(mac_1d, flat_matrix, flat_matrix)

        if time_1d < time_2d:
            result = "1D 빠름"
        else:
            result = "2D 빠름"

        print(
            f"{n}x{n}\t"
            f"{time_2d:.6f}\t"
            f"{time_1d:.6f}\t"
            f"{result}"
        )

# 15. 패턴 생성 함수 (보너스2)
def generate_pattern(n, shape):
    if n < 3 or n % 2 == 0:
        raise ValueError("3 이상의 홀수를 입력하세요.")

    matrix = []
    center = n // 2

    for i in range(n):
        row = []

        for j in range(n):
            if shape == "Cross":
                value = 1 if i == center or j == center else 0

            elif shape == "X":
                value = 1 if i == j or i + j == n - 1 else 0

            else:
                raise ValueError("Cross 또는 X만 지원합니다.")

            row.append(value)

        matrix.append(row)

    return matrix

# 16. 패턴 생성 모드
def run_generator_mode():
    while True:
        try:
            n = int(input("행렬 크기 N (3 이상의 홀수): "))

            cross = generate_pattern(n, "Cross")
            x_filter = generate_pattern(n, "X")
            break

        except ValueError as error:
            print("입력 오류:", error)

    print(f"\n=== Cross ({n}x{n}) ===")
    for row in cross:
        print(*row)

    print(f"\n=== X ({n}x{n}) ===")
    for row in x_filter:
        print(*row)

    cross_score = mac(cross, cross)
    x_score = mac(cross, x_filter)

    print("\n=== Cross 패턴 판정 ===")
    print("Cross 점수:", cross_score)
    print("X 점수:", x_score)
    print(
        "판정:",
        classify(cross_score, x_score, "Cross", "X")
    )

# 메인 메뉴
def main():
    print("=== Mini NPU Simulator ===")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    print("3. 패턴 자동 생성 (보너스)")
    print("4. 2D vs 1D MAC 성능 비교 (보너스)")

    while True:
        choice = input("선택: ")

        if choice == "1":
            run_manual_mode()
            break

        elif choice == "2":
            run_json_mode()
            break

        elif choice == "3":
            run_generator_mode()
            break

        elif choice == "4":
            compare_mac_performance()
            break

        else:
            print("1, 2, 3 또는 4를 입력하세요.")


if __name__ == "__main__":
    main()
