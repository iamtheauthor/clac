import pathlib
from typing import Tuple


__project_root__ = pathlib.Path(__file__).resolve().parents[1]


def _rm_dir_tree(root: pathlib.Path, pattern: str = '*') -> Tuple[int, int]:
    count_file = 0
    count_dir = 0
    for path in root.glob(pattern):
        if path.is_file():
            print(f'Deleting file: {path}')
            count_file += 1
            path.unlink()
        else:
            counts = _rm_dir_tree(path, pattern)
            count_file += counts[0]
            count_dir += counts[1]
    if root.is_dir():
        print(f'Deleting dir: {root}')
        count_dir += 1
        root.rmdir()
    return count_file, count_dir


def remove_bytecode_files(root: pathlib.Path) -> Tuple[int, int]:
    count_file = 0
    count_dir = 0
    for path in root.glob('**/__pycache__'):
        counts = _rm_dir_tree(path)
        count_file += counts[0]
        count_dir += counts[1]
    return count_file, count_dir


def remove_log_files(root: pathlib.Path) -> Tuple[int, int]:
    return _rm_dir_tree(root / '.logs')


def remove_pytest_cache_files(root: pathlib.Path) -> Tuple[int, int]:
    count_file, count_dir = _rm_dir_tree(root / '.cache')
    counts = _rm_dir_tree(root / '.pytest_cache')
    count_file += counts[0]
    count_dir += counts[1]
    return count_file, count_dir


def remove_mypy_cache_files(root: pathlib.Path) -> Tuple[int, int]:
    return _rm_dir_tree(root / '.mypy_cache')


def report_counts(files: int, dirs: int) -> None:
    print(f'Number of files deleted: {files}')
    print(f'Number of directories deleted: {dirs}')
    return


def main():
    count_file = 0
    count_dir = 0

    counts = remove_bytecode_files(__project_root__)
    count_file += counts[0]
    count_dir += counts[1]

    counts = remove_log_files(__project_root__)
    count_file += counts[0]
    count_dir += counts[1]

    # counts = remove_rope_files(__project_root__)
    # count_file += counts[0]
    # count_dir += counts[1]

    counts = remove_pytest_cache_files(__project_root__)
    count_file += counts[0]
    count_dir += counts[1]

    counts = remove_mypy_cache_files(__project_root__)
    count_file += counts[0]
    count_dir += counts[1]

    report_counts(count_file, count_dir)

    print('Finished with project cleanup. Exiting...')

    return


if __name__ == '__main__':
    main()
