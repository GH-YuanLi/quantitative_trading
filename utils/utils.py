import json
import re
import traceback
from datetime import datetime


def get_timestamp(time_type="%Y-%m-%d_%H:%M:%S"):
    return datetime.now().strftime(time_type)


def load_json(json_file, show_info=True):
    with open(json_file, "r", encoding="utf8") as fin:
        data = json.load(fin)
    if show_info:
        print("load {} from {}".format(len(data), json_file))
    return data


def json2markdown(json_dict, start_prefix="#### ", item_prefix="- "):
    markdown_text = ""
    if type(json_dict) is list:
        return "\n".join([json2markdown(sample, start_prefix, item_prefix) for sample in json_dict]).strip()
    elif type(json_dict) is dict:
        for curr_key, item_info_dict in json_dict.items():
            markdown_text += f"{start_prefix}{curr_key}\n"
            markdown_text += json2markdown(item_info_dict, start_prefix=f"#{start_prefix}", item_prefix=item_prefix)
            markdown_text += "\n"
        return markdown_text.strip()
    else:
        # print(f"{type(json_dict)} is not supported!")
        return f"{item_prefix}{json_dict}".strip()


def find_between_singal(
    generate_str,
    start_signal: str,
    end_signal: str,
):
    pattern = fr'{start_signal}(.*?){end_signal}'
    matches = re.findall(pattern, generate_str, re.DOTALL)
    return matches


def postprocess_json(
    generate_str,
    start_signal: str = "```json",
    end_signal: str = "```",
    mode: str = "last"
):
    candidate_list = find_between_singal(
        generate_str=generate_str,
        start_signal=start_signal,
        end_signal=end_signal,
    )
    if len(candidate_list) == 0:
        """match failed"""
        start_pos = generate_str.find(start_signal)
        if start_pos == -1:
            pure_str = generate_str.strip()
        else:
            pure_str = generate_str[start_pos+len(start_signal):]
            end_pos = pure_str.find(end_signal)
            pure_str = pure_str[:end_pos].strip()
        candidate_list = [pure_str]
    """select target"""
    mode_mappings = {
        "first": (0, 1),
        "last": (len(candidate_list)-1, len(candidate_list)),
        "all": (0, len(candidate_list)),
    }
    all_result = []
    for pure_str in candidate_list[mode_mappings[mode][0]: mode_mappings[mode][1]]:
        try:
            result = json.loads(pure_str)
            all_result.append(result)
        except Exception as e:
            print(f"Error: {e}\ndecode response: {pure_str}\n{traceback.format_exc()}")
    if len(all_result) == 0:
        """no valid json block"""
        end_pos = generate_str.rfind(end_signal)
        if end_pos == -1:
            pure_str = generate_str.strip()
        else:
            pure_str = generate_str[:end_pos].strip()
            start_pos = pure_str.find(start_signal)
            pure_str = pure_str[start_pos+len(start_signal):].strip()
        try:
            all_result.append(json.loads(pure_str))
        except Exception as e:
            print(f"Error: {e}\ndecode response: {pure_str}\n{traceback.format_exc()}")
            all_result = [pure_str]
    return all_result[-1]


def write2json(data_list, data_path, data_name="data", write_mode="w"):
    try:
        if write_mode == "w":
            with open(data_path, "w", encoding="utf-8") as fout:
                fout.write(json.dumps(data_list, ensure_ascii=False, indent=2))
                print("{}({}) saved into {}".format(data_name, len(data_list), data_path))
        elif write_mode == "a":
            try:
                old_data_list = load_json(data_path)
            except Exception as e:
                print(f"{e}")
                old_data_list = []
            with open(data_path, "w", encoding="utf-8") as fout:
                old_data_list.extend(data_list)
                fout.write(json.dumps(old_data_list, ensure_ascii=False, indent=2))
                print(f"{data_name}({len(old_data_list)}) (added {len(data_list)} samples) into {data_path}")
        else:
            raise NotImplementedError(f"write mode {write_mode} is not supported!")
    except Exception as e:
        print(f"Error {e} while write {data_list} into file {data_path}\n{traceback.format_exc()}")
