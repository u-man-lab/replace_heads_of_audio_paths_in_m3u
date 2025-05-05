import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Self, Tuple

import yaml
from pydantic import BaseModel, ConfigDict, field_validator


class AudioPath:
    """
    音楽ファイルのパスを表すクラス。
    """

    __path: Path

    def __init__(self, path: Path):
        """
        Args:
            path (Path): 音楽ファイルのファイルパス。
        """
        self.__path = path

    def __str__(self) -> str:
        """文字列表現としてパスを返す。"""
        return self.__path.__str__()

    def __trim_relative_path_from_base_path(self, base_path_candidates: Tuple[Path, ...]) -> Path:
        """
        指定されたベースパスを基準にして、音楽ファイルの相対パスを取得する。

        Args:
            base_path_candidates (Tuple[Path, ...]): 基準となるベースディレクトリのパスの候補。

        Returns:
            Path: ベースパスからの相対パス。

        Raises:
            ValueError: 音楽ファイルのパスがベースパスに含まれていない場合。
        """
        relative_path = None
        for base_path_before in base_path_candidates:
            try:
                relative_path = self.__path.relative_to(base_path_before)
            except ValueError:
                pass
            else:
                break
        else:  # すべてが親ディレクトリでなかった場合
            raise ValueError(
                f'M3Uファイル内の楽曲ファイルパス"{self.__path}"のフォルダが想定外です。'
            )
        return relative_path

    def __pick_existing_path(self, existing_path_candidates: Tuple[Path, ...]) -> Path:
        """
        指定された音楽ファイルのファイルパスリストから実在するパスを特定する。

        Args:
            existing_path_candidates (Tuple[Path, ...]): 音楽ファイルパスの候補。

        Returns:
            Path: 実在するファイルのパス。

        Raises:
            FileNotFoundError: 実在するパスが見つからない場合。
            FileExistsError: 複数の実在するパスが見つかった場合。
        """
        existing_paths = set()
        for candidate_path in existing_path_candidates:
            if candidate_path.exists():
                existing_paths.add(candidate_path)

        existing_paths_len = len(existing_paths)
        if existing_paths_len == 0:
            raise FileNotFoundError(
                f'M3Uファイル内の楽曲ファイルパス"{self.__path}"の現在の場所を確認できません。'
            )
        elif existing_paths_len > 1:
            raise FileExistsError(
                f'M3Uファイル内の楽曲ファイルパス"{self.__path}"の現在の場所の候補が複数あります。: '
                + ', '.join(f'"{path}"' for path in existing_paths)
            )

        return existing_paths.pop()

    def search_existing_path(
        self,
        base_paths_before_replace: Tuple[Path, ...],
        base_paths_after_replace: Tuple[Path, ...],
    ) -> 'AudioPath':
        """
        指定された元のベースパス群に対する相対パスを使い、置換後の候補から実在するパスを検索する。

        Args:
            base_paths_before_replace (Tuple[Path, ...]): 元のベースディレクトリパスの候補。
            base_paths_after_replace (Tuple[Path, ...]): 置換後のベースディレクトリパスの候補。

        Returns:
            AudioPath: 実在する新しいパスを保持するAudioPathオブジェクト。

        Raises:
            ValueError: パスが元のいずれのベースパスにも属さない場合。
            FileNotFoundError: 実在する新パスが見つからない場合。
            FileExistsError: 実在する新パスの候補が複数存在する場合。
        """
        if self.__path.exists():
            return self

        relative_path = self.__trim_relative_path_from_base_path(base_paths_before_replace)
        existing_path_candidates = tuple(
            base_path / relative_path for base_path in base_paths_after_replace
        )
        existing_path = self.__pick_existing_path(existing_path_candidates)
        return AudioPath(existing_path)


class Diacritics:
    """
    Unicodeの結合文字に関するユーティリティクラス。
    """

    # Unicodeの全ての結合文字（正規結合クラスが0でない文字）を文字列としてつなげる
    __ALL_COMBINING_CHARS = ''.join(
        chr(cp) for cp in range(0x110000) if unicodedata.combining(chr(cp)) != 0
    )

    @classmethod
    def replace_combining_chars_to_precomposed(cls, text: str) -> str:
        """
        文字列に含まれる結合文字（Combining Character）を合成済み（Precomposed）文字列に変換する。
        ※iTunesからエクスポートしたM3Uファイルで、基底文字+結合文字が1文字ずつに分離するため。

        Args:
            text (str): 対象となる文字列。

        Returns:
            str: 合成済み文字列に変換された文字列。
        """
        new_text_as_chars: List[str] = []
        for char in text:

            new_char = char
            if char in cls.__ALL_COMBINING_CHARS and new_text_as_chars:
                chars_to_compose = (
                    new_text_as_chars.pop() + char
                )  # 直前の基底文字と結合文字を並べる
                new_char = unicodedata.normalize('NFC', chars_to_compose)  # 対応する合成文字を取得

            new_text_as_chars.append(new_char)

        return ''.join(new_text_as_chars)


class M3uFile:
    """
    M3Uファイルの読み取り、解析、パス置換、および書き出しを行うクラス。
    インスタンス化はread_file()メソッドを通じて行う。

    Attributes:
        __content (str): M3Uファイルの中身の文字列。
        __path_lines (List[str]): コメントアウトと空行を除く行の文字列のリスト。
        __audio_paths (Tuple[AudioPath, ...]): 正規化した音楽ファイルのパスリスト。
    """

    __content: str
    __path_lines: List[str]
    __audio_paths: Tuple[AudioPath, ...]

    def __new__(cls, *args, **kwargs):
        raise AttributeError('このクラスのコンストラクタは非公開です。')

    def __init__(self, *args, **kwargs):
        raise AttributeError('このクラスのコンストラクタは非公開です。')

    @classmethod
    def __private_constructor(cls, content: str) -> Self:
        """
        M3uFileのインスタンスを内部的に生成するためのプライベートコンストラクタ。

        Args:
            content (str): M3Uファイルの中身の文字列。

        Returns:
            M3uFile: 初期化されたM3uFileインスタンス。
        """
        self = super().__new__(cls)

        self.__content = content

        lines = self.__content.splitlines()
        self.__path_lines = [line for line in lines if line[:1] not in ('', '#')]

        audio_paths_list = []
        for path_line in self.__path_lines:
            path_line_normalized = Diacritics.replace_combining_chars_to_precomposed(
                path_line.strip()
            )
            audio_paths_list.append(AudioPath(Path(path_line_normalized)))
        self.__audio_paths = tuple(audio_paths_list)

        return self

    def __replace_audio_paths(self, paths_replace_dict: Dict[AudioPath, AudioPath]) -> 'M3uFile':
        """
        M3Uファイル内のオーディオファイルパスを指定された置換辞書に基づいて更新し、
        新しいM3uFileインスタンスを生成する。

        Args:
            paths_replace_dict (Dict[AudioPath, AudioPath]): 置換対象のパスと新しいパスの対応を示す辞書。

        Returns:
            M3uFile: パスが置換された新しいM3uFileインスタンス。

        Raises:
            ValueError: 置換対象のパスがM3Uファイル内に存在しない場合。
        """
        replaced_content = self.__content
        not_exist_audio_paths = set()
        for original_audio_path, existing_audio_path in paths_replace_dict.items():
            if original_audio_path not in self.__audio_paths:
                not_exist_audio_paths.add(original_audio_path)
                continue

            # そのまま置換すると結合文字を含むパスが置換されないので、
            # Diacritics.replace_combining_chars_to_precomposed()で変換前の文字列を取得
            target_line_id = self.__audio_paths.index(original_audio_path)
            target_path_line = self.__path_lines[target_line_id]

            replaced_content = replaced_content.replace(target_path_line, str(existing_audio_path))

        if len(not_exist_audio_paths) != 0:
            raise ValueError(
                '1つ以上の置換対象のファイルパスがM3Uファイル上に存在しません。: '
                + ', '.join(f'"{str(path)}"' for path in not_exist_audio_paths)
            )

        return M3uFile.__private_constructor(replaced_content)

    def replace_heads_of_audio_paths(
        self,
        base_paths_before_replace: Tuple[Path, ...],
        base_paths_after_replace: Tuple[Path, ...],
    ) -> 'M3uFile':
        """
        M3Uファイル内の音楽ファイルパスのベースディレクトリ部分を置換し、新たなM3uFileインスタンスを生成する。
        置換後のベースディレクトリに基づく新しいファイルパスがサーバ上で1つ以上特定できない場合はエラーとなる。
        特定できなかった音楽ファイルについては、標準エラー出力する。

        Args:
            base_paths_before_replace (Tuple[Path, ...]): 元のベースディレクトリの候補。
            base_paths_after_replace (Tuple[Path, ...]): 置換後のベースディレクトリの候補。

        Returns:
            M3uFile: パスが置換された新しいM3uFileインスタンス。

        Raises:
            FileNotFoundError: 1つ以上のファイルのパスがサーバ上で特定できなかった場合。
            ValueError: 置換対象のパスがM3Uファイル内に存在しない場合。
        """
        original_audio_path_tuple = self.__audio_paths

        paths_replace_dict = {}
        search_fail_paths = set()
        for original_audio_path in original_audio_path_tuple:
            try:
                existing_audio_path = original_audio_path.search_existing_path(
                    base_paths_before_replace, base_paths_after_replace
                )
            except Exception as err:
                search_fail_paths.add(original_audio_path)
                print(f'{err.__class__.__name__}: {err}', file=sys.stderr)
                continue

            paths_replace_dict[original_audio_path] = existing_audio_path

        if len(search_fail_paths) > 0:
            raise FileNotFoundError(
                '1つ以上の楽曲ファイルの特定ができなかったため、M3Uファイルの置換に失敗しました。'
            )

        replaced_m3u = self.__replace_audio_paths(paths_replace_dict)

        return replaced_m3u

    def write_file(self, path: Path):
        """
        M3Uファイルの内容を指定されたパスに保存する。

        Args:
            path (Path): 書き出し先のファイルパス。

        Raises:
            FileExistsError: 出力先に既にファイルが存在する場合。
        """
        if path.exists():
            raise FileExistsError(f'既にファイルが存在するため上書きできません。: "{path}"')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.__content, encoding='UTF-8')

    @classmethod
    def read_file(cls, path: Path) -> 'M3uFile':
        """
        指定されたパスのM3Uファイルを読み込み、M3uFileオブジェクトを生成する。

        Args:
            path (Path): 読み込むM3Uファイルのパス。

        Returns:
            M3uFile: 初期化されたM3uFileインスタンス。
        """
        content = path.read_text(encoding='UTF-8')
        return cls.__private_constructor(content)


class Config(BaseModel):
    """
    設定ファイル(YAML)のクラス。
    設定値の検証処理も内包し、pydanticにより外部から変更不可に設計したデータクラス。
    """

    DIR_PATH_FOR_INPUT_M3U_FILES: Path
    DIR_PATH_FOR_OUTPUT_M3U_FILES: Path
    BASE_PATHS_BEFORE_REPLACE: Tuple[Path, ...]
    BASE_PATHS_AFTER_REPLACE: Tuple[Path, ...]

    model_config = ConfigDict(frozen=True, extra='forbid', strict=True)

    @field_validator(
        'DIR_PATH_FOR_INPUT_M3U_FILES', 'DIR_PATH_FOR_OUTPUT_M3U_FILES', mode='before'
    )
    @classmethod
    def __validate_and_convert_to_path(cls, arg: str) -> Path:
        """
        設定ファイルの"DIR_PATH_FOR_INPUT_M3U_FILES"および"DIR_PATH_FOR_OUTPUT_M3U_FILES"に
        指定された値を検証し、問題なければPathオブジェクトに変換する。

        Args:
            arg (str): 設定ファイルの該当フィールドに指定された文字列。

        Returns:
            Path: 検証済みのPathオブジェクト。

        Raises:
            TypeError: 設定ファイルで指定された値の型が文字列型ではない場合。
            FileNotFoundError: 設定ファイルで指定された値に対応するパスが存在しない場合。
        """
        if not isinstance(arg, str):
            raise TypeError(f'設定ファイルに指定された値の型が想定外です。: "{arg}" [{type(arg)}]')
        path = Path(arg.strip())
        if not path.exists():
            raise FileNotFoundError(
                f'設定ファイルに指定されたディレクトリパスがサーバ上に存在しません。: "{path}"'
            )
        return path

    @field_validator('BASE_PATHS_BEFORE_REPLACE', mode='before')
    @classmethod
    def __convert_to_path_tuple(cls, args: List[str]) -> Tuple[Path, ...]:
        """
        設定ファイルの"BASE_PATHS_BEFORE_REPLACE"に指定された値を検証し、
        問題なければPathオブジェクトのタプルに変換する。

        Args:
            args (List[str]): 設定ファイルの該当フィールドに指定された文字列のリスト。

        Returns:
            Tuple[Path, ...]: 検証済みのPathオブジェクトのタプル。

        Raises:
            TypeError: 設定ファイルで指定された値の型が文字列のリスト型ではない場合。
        """
        if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
            raise TypeError(f'設定ファイルに指定された値の型が想定外です。: "{args}"')
        return tuple(Path(arg.strip()) for arg in args)

    @field_validator('BASE_PATHS_AFTER_REPLACE', mode='before')
    @classmethod
    def __validate_and_convert_to_path_tuple(cls, args: List[str]) -> Tuple[Path, ...]:
        """
        設定ファイルの"BASE_PATHS_AFTER_REPLACE"に指定された値を検証し、
        問題なければPathオブジェクトのタプルに変換する。

        Args:
            args (List[str]): 設定ファイルの該当フィールドに指定された文字列のリスト。

        Returns:
            Tuple[Path, ...]: 検証済みのPathオブジェクトのタプル。

        Raises:
            TypeError: 設定ファイルで指定された値の型が文字列のリスト型ではない場合。
            FileNotFoundError: 設定ファイルで指定された値に対応するパスが1つでも存在しない場合。
        """
        if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
            raise TypeError(f'設定ファイルに指定された値の型が想定外です。: "{args}"')
        path_tuple = tuple(Path(arg.strip()) for arg in args)
        not_exist_paths = [path for path in path_tuple if not path.exists()]
        if len(not_exist_paths) != 0:
            raise FileNotFoundError(
                '設定ファイルに記載されたいくつかのディレクトリパスがサーバ上に存在しません。: '
                + ', '.join(f'"{str(path)}"' for path in not_exist_paths)
            )
        return path_tuple

    @classmethod
    def from_yaml(cls, path: Path) -> 'Config':
        """
        YAMLファイルから設定を読み取り、Configインスタンスを生成する。

        Args:
            path (Path): YAMLファイルのパス。

        Returns:
            Config: 初期化された設定インスタンス。

        Raises:
            FileNotFoundError: 指定されたYAMLファイルのパスが存在しない場合。
            ValidationError: YAMLファイルの設定内容に異常がある場合。
        """
        with open(path, 'r', encoding='UTF-8') as fr:
            content = yaml.safe_load(fr)
        return cls(**content)


def replace_heads_of_audio_paths_in_m3u():
    """
    コマンドライン引数で指定された設定ファイルをもとに、M3Uファイル内の音楽ファイルの親ディレクトリのパスを一括置換する。
    1つのM3Uファイルの処理過程でExceptionが発生した場合は標準エラー出力し、次以降のM3Uファイルの処理を継続する。

    Raises:
        ValueError: 設定ファイルの読み取りに失敗した場合や、引数の個数が不正な場合。
        FileNotFoundError: M3Uファイルや置換候補のファイルパスが見つからない場合。
    """
    if len(sys.argv) != 2:
        raise ValueError('設定ファイルのファイルパス1つのみを引数として指定してください。')
    config_path = Path(sys.argv[1])

    try:
        config = Config.from_yaml(config_path)
    except Exception as err:
        raise ValueError('設定ファイルの読み取りに失敗しました。') from err

    original_m3u_paths_pattern1 = list(config.DIR_PATH_FOR_INPUT_M3U_FILES.rglob('*.m3u'))
    original_m3u_paths_pattern2 = list(config.DIR_PATH_FOR_INPUT_M3U_FILES.rglob('*.m3u8'))
    original_m3u_paths = original_m3u_paths_pattern1 + original_m3u_paths_pattern2
    original_m3u_paths_len = len(original_m3u_paths)
    if original_m3u_paths_len == 0:
        raise FileNotFoundError(
            f'設定ファイルに記載されたパス"{config.DIR_PATH_FOR_INPUT_M3U_FILES}"配下にはM3Uファイルが1件も存在しません。'
        )

    for i, original_m3u_path in enumerate(original_m3u_paths):

        print(f'---\n処理中 [{i + 1}/{original_m3u_paths_len}] <- "{original_m3u_path}"')

        try:
            original_m3u = M3uFile.read_file(original_m3u_path)
        except Exception as err:
            print(
                f'処理失敗(読み込み) [{i + 1}/{original_m3u_paths_len}] '
                + f'{err.__class__.__name__}: {err}: "{original_m3u_path}"',
                file=sys.stderr,
            )
            continue

        try:
            replaced_m3u = original_m3u.replace_heads_of_audio_paths(
                config.BASE_PATHS_BEFORE_REPLACE, config.BASE_PATHS_AFTER_REPLACE
            )
        except Exception as err:
            print(
                f'処理失敗(変換) [{i + 1}/{original_m3u_paths_len}] '
                + f'{err.__class__.__name__}: {err}: "{original_m3u_path}"',
                file=sys.stderr,
            )
            continue

        relative_path = original_m3u_path.relative_to(config.DIR_PATH_FOR_INPUT_M3U_FILES)
        replaced_m3u_path = config.DIR_PATH_FOR_OUTPUT_M3U_FILES / relative_path

        try:
            replaced_m3u.write_file(replaced_m3u_path)
        except Exception as err:
            print(
                f'処理失敗(書き込み) [{i + 1}/{original_m3u_paths_len}] '
                + f'{err.__class__.__name__}: {err}: "{replaced_m3u_path}"',
                file=sys.stderr,
            )
            continue

        print(f'処理完了 [{i + 1}/{original_m3u_paths_len}] -> "{replaced_m3u_path}"')


if __name__ == '__main__':
    replace_heads_of_audio_paths_in_m3u()
