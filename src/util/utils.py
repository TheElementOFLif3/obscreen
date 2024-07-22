import os
import re
import sys
import time
import inspect
import subprocess
import unicodedata
import platform


from datetime import datetime, timedelta
from typing import Optional, List, Dict
from enum import Enum
from cron_descriptor import ExpressionDescriptor
from cron_descriptor.Exception import FormatException, WrongArgumentException, MissingFieldException

CAMEL_CASE_TO_SNAKE_CASE_PATTERN = re.compile(r'(?<!^)(?=[A-Z])')


def is_wrapped_by(s: str, head: str = '', tail: str = '') -> bool:
    return s[0] == head and s[-1] == tail if len(s) > 0 else None


def wrap_if(s: str, condition: bool = True, quote_type: str = "'") -> str:
    if not condition or is_wrapped_by(s, quote_type, quote_type):
        return s
    return "{}{}{}".format(
        quote_type,
        s,
        quote_type
    )


def am_i_in_docker():
    docker_env = os.path.exists('/.dockerenv')
    docker_cgroup = False
    try:
        with open('/proc/1/cgroup', 'rt') as f:
            for line in f:
                if 'docker' in line:
                    docker_cgroup = True
                    break
    except Exception:
        pass

    return docker_env or docker_cgroup


def enum_to_dict(enum_class) -> Dict:
    values = {}

    for enum_item in enum_class:
        values[enum_item.value] = enum_item.value

    return values


def camel_to_snake(camel: str) -> str:
    return CAMEL_CASE_TO_SNAKE_CASE_PATTERN.sub('_', camel).lower()


def is_cron_in_datetime_moment(expression: str) -> bool:
    pattern = re.compile(r'^(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+\*\s+(\d+)$')
    return bool(pattern.match(expression))


def is_cron_in_week_moment(expression: str) -> bool:
    pattern = re.compile(r'^(\d+)\s+(\d+)\s+\*\s+\*\s+(\d+)$')
    return bool(pattern.match(expression))


def is_cron_in_year_moment(expression: str) -> bool:
    pattern = re.compile(r'^(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+\*\s+\*$')
    return bool(pattern.match(expression))


def is_cron_in_month_moment(expression: str) -> bool:
    pattern = re.compile(r'^(\d+)\s+(\d+)\s+(\d+)\s+\*\s+\*\s+\*$')
    return bool(pattern.match(expression))


def is_cron_in_day_moment(expression: str) -> bool:
    pattern = re.compile(r'^(\d+)\s+(\d+)\s+\*\s+\*\s+\*\s+\*$')
    return bool(pattern.match(expression))


def is_now_after_cron_date_time_moment(expression: str) -> bool:
    minutes, hours, day, month, _, year = expression.split(' ')
    formatted_date_time = f"{year}-{month.zfill(2)}-{day.zfill(2)} {hours.zfill(2)}:{minutes.zfill(2)}"
    start_date = datetime.strptime(formatted_date_time, '%Y-%m-%d %H:%M')
    return datetime.now() >= start_date


def is_now_after_cron_week_moment(cron_expression: str) -> bool:
    minutes, hours, day, month, day_of_week = cron_expression.split(' ')
    now = datetime.now()
    week_start = now - timedelta(days=now.isoweekday() - 1)

    for day_offset in range(7):
        check_date = week_start + timedelta(days=day_offset)
        if check_date.isoweekday() == int(day_of_week):
            check_date = check_date.replace(hour=int(hours), minute=int(minutes), second=0, microsecond=0)
            if datetime.now() >= check_date:
                return True
    return False


def get_safe_cron_descriptor(expression: str, use_24hour_time_format=True, locale_code: Optional[str] = None) -> str:
    if is_cron_in_datetime_moment(expression):
        [minutes, hours, day, month, _, year] = expression.split(' ')
        return "{}-{}-{} at {}:{}".format(
            year,
            month.zfill(2),
            day.zfill(2),
            hours.zfill(2),
            minutes.zfill(2)
        )

    options = {
        "expression": expression,
        "use_24hour_time_format": use_24hour_time_format
    }

    if locale_code:
        options["locale_code"] = locale_code
    try:
        return str(ExpressionDescriptor(**options))
    except FormatException:
        return ''
    except WrongArgumentException:
        return ''
    except MissingFieldException:
        return ''


def get_optional_string(var: Optional[str]) -> Optional[str]:
    if var is None:
        return None

    var = var.strip()

    if var:
        return var

    return None


def get_keys(dict_or_object, key_list_name: str, key_attr_name: str = 'key') -> Optional[List]:
    if dict_or_object is None:
        return None

    is_dict = isinstance(dict_or_object, dict)
    is_object = not is_dict and isinstance(dict_or_object, object)

    if is_dict:
        iterable = dict_or_object[key_list_name]
        if iterable is None:
            return None
        return [item[key_attr_name] for item in iterable]

    if is_object:
        iterable = getattr(dict_or_object, key_list_name)
        if iterable is None:
            return None
        return [getattr(item, key_attr_name) for item in iterable]

    return None


def enum_to_str(enum: Optional[Enum]) -> Optional[str]:
    if enum:
        return str(enum.value)

    return None


def str_to_enum(str_val: str, enum_class) -> Enum:
    for enum_item in enum_class:
        if enum_item.value == str_val:
            return enum_item
    raise ValueError(f"{str_val} is not a valid {enum_class.__name__} item")


def regex_search(pattern: str, string: str, group: int):
    """Shortcut method to search a string for a given pattern.
    :param str pattern:
        A regular expression pattern.
    :param str string:
        A target string to search.
    :param int group:
        Index of group to return.
    :rtype:
        str or tuple
    :returns:
        Substring pattern matches.
    """
    regex = re.compile(pattern)
    results = regex.search(string)
    if not results:
        return False

    return results.group(group)


def get_yt_video_id(url: str) -> str:
    if len(url) <= 14:
        return url

    """Extract the ``video_id`` from a YouTube url.
    This function supports the following patterns:
    - :samp:`https://youtube.com/watch?v={video_id}`
    - :samp:`https://youtube.com/embed/{video_id}`
    - :samp:`https://youtu.be/{video_id}`
    :param str url:
        A YouTube url containing a video id.
    :rtype: str
    :returns:
        YouTube video id.
    """
    return regex_search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url, group=1)


def slugify(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)


def seconds_to_hhmmss(seconds):
    if not seconds:
        return ""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:02}"


def get_working_directory():
    return os.getcwd()


def run_system_command(commands: list, shell: bool = False, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
    return subprocess.run(commands, shell=shell, stdout=stdout, stderr=stderr)


def sudo_run_system_command(commands: list, shell: bool = False, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
    if commands[0] != 'sudo':
        commands.insert(0, 'sudo')
    return run_system_command(commands, shell=shell, stdout=stdout, stderr=stderr)


def get_function_caller(depth: int = 3) -> str:
    return inspect.getmodulename(inspect.stack()[depth][1])


def clamp(x: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(x, maximum))


def restart(debug=False) -> None:
    time.sleep(1)

    if platform.system().lower() == 'darwin':
        python = sys.executable
        os.execl(python, python, *sys.argv)
    elif am_i_in_docker():
        python = sys.executable
        os.execl(python, python, *sys.argv)
    else:
        try:
            subprocess.run(["sudo", "systemctl", "restart", 'obscreen-studio'], check=True, timeout=10, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            pass
        except subprocess.TimeoutExpired:
            pass
        except subprocess.CalledProcessError:
            pass


def truncate(s, length, ellipsis=None):
    if ellipsis and len(s) > length:
        return s[:length].strip() + ellipsis
    return s[:length]


def merge_dicts(dict1, dict2):
    result = dict1.copy()
    result.update(dict2)
    return result


def dictsort(dict1, attribute="position"):
    return dict(sorted(dict1.items(), key=lambda item: item[1][attribute]))


def slugify_next(slug: str) -> str:
    parts = slug.rsplit('-', 1)

    if len(parts) > 1 and parts[-1].isdigit():
        next_number = int(parts[-1]) + 1
        return f"{parts[0]}-{next_number}"
    else:
        return f"{slug}-1"
