"""请使用nuitka或Cython打包此程序；未经允许禁止使用"""
import json
import random
import sys
import os
from pathlib import Path
from datetime import datetime as dt
from pynput import keyboard
import msvcrt
from openai import OpenAI
# import subprocess

# WHITELIST = ['F211E8E8-6C10-11EF-A4F7-40C2BA813B17','4C4C4544-0032-4810-8054-C8C04F393034','AE308556-497D-11EF-A4F7-40C2BA62FFCE']

class Database:
    def __init__(self):
        self.start_time = None
        self.db = None
        self.rand_list = []
        self.subject_name = ""
        self.wrong = []
        self.test_count = []  # 考试题数量
        self.score_val = []  # 类型分值
        self.point = 0
        self.sg = 0
        self.mt = 0
        self.other = 0
        self.data = {'done': [], 'wrong': []}
        self.type = 0
        # output = subprocess.check_output(
        #     ["powershell", "-Command", "(Get-CimInstance Win32_ComputerSystemProduct).UUID"],
        #     text=True,
        #     timeout=10
        # )
        # os.system('cls')
        # if output.strip() in WHITELIST:

        # else:
        #     sys.exit(1)


    def selector(self):
        print("------复习不------")
        candidate = []
        base_path = Path(__file__).parent
        for file in os.listdir(base_path):
            if file.endswith(".json") and file[0:2] == "db":
                with open(os.path.join(base_path, file), 'r', encoding='utf-8') as f:
                    print(f"{file[2]}.{json.load(f)['header']['title']}")# 输出课程名称
                    f.close()
                candidate.append(int(file[2]))
        temp = int(input())
        self.type = temp if temp in candidate else sys.exit(1)
        with open(os.path.join(base_path, f"db{self.type}.json"), 'r', encoding='utf-8') as f:
            all_data = json.load(f)
            self.db = all_data["body"]
            self.test_count = all_data['header']['test_count']
            self.score_val = all_data['header']['score_val']
            f.close()
        try:
            with open(f"index{self.type}.json", 'r') as f:
                self.data = json.load(f)
                f.close()
        except FileNotFoundError:
            print("没有错题记录，请先做题")
            with open(f"index{self.type}.json", 'w') as f:
                json.dump(self.data, f)
                f.close()
        except json.decoder.JSONDecodeError:
            print("错题记录错误,已重置")
            with open(f"index{self.type}.json", 'w') as f:
                json.dump(self.data, f)
                f.close()
        self.shuffle()

    def shuffle(self):
        for item in self.db:
            option_keys = ['a', 'b', 'c', 'd']
            # 获取正确答案内容
            if 'e' in item:
                option_keys.append('e')
            if item['type'] == 2:
                correct_contents = [item[chr(96 + ans)] for ans in item['answer']]
            elif item['type'] == 4:
                continue
            else:
                correct_contents = [item[chr(96 + item['answer'])]]
            if item['type'] == 3:
                continue
            else:
                # 获取所有选项并打乱
                try:
                    all_options = [item[key] for key in option_keys]
                except KeyError:
                    print(f'错误：index={item["index"]}')
                    exit()
            random.shuffle(all_options)

            # 更新选项
            for key, option in zip(option_keys, all_options):
                item[key] = option

            # 更新答案
            if item['type'] == 2:
                item['answer'] = [all_options.index(content) + 1 for content in correct_contents]
            else:
                item['answer'] = all_options.index(correct_contents[0]) + 1

    def save(self, option, index):
        if option == 1:
            if index + 1 in self.data['wrong']:
                self.data['wrong'].remove(index + 1)
                self.data['done'].append(index)
            elif index not in self.data['done']:
                self.data['done'].append(index)
        elif option == 0 and index + 1 not in self.data['wrong']:
            self.data['wrong'].append(index + 1)
        with open(f"index{self.type}.json", 'w') as f:
            json.dump(self.data, f)
            f.close()

    def printf(self, index):
        print(self.db[index]['title'])
        if self.db[index]['type'] < 4:
            print(f"A:{self.db[index]['a']}")
            print(f"B:{self.db[index]['b']}")
            if self.db[index]['type'] < 3:
                print(f"C:{self.db[index]['c']}")
                print(f"D:{self.db[index]['d']}")

    def sequence(self,shuffle:bool,skip:bool):
        for i in range(0, len(self.db)):
            if self.db[i]['index'] - 1 not in self.data['done']:
                self.rand_list.append(i)
        if shuffle:
            random.shuffle(self.rand_list)
        self.do(skip=skip)


    def query(self,item:dict):
        print("解析生成中……\n按Ctrl+C跳过")
        try:
            with open("api-key.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                base_url = data['base_url']
                model = data["model"]
                api_key = data["api-key"]
        except FileNotFoundError:
            print("当前版本仅支持deepseek-v4-flash，请输入您的api-key:",end='')
            api_key = input()
            model="deepseek-v4-flash"
            base_url = "https://api.deepseek.com"
            with open('api-key.json', 'w', encoding='utf-8') as f:
                json.dump({'base_url': base_url, 'model': model,'api-key':api_key}, f)

        client = OpenAI(
            api_key=api_key,
            base_url=base_url)
        tp = ""
        match item['type']:
            case 1:
                tp="[单选题]"
            case 2:
                tp="[\033[1;6;33m多选题\033[0m]"
            case 3:
                tp="[\033[1;34m判断题\033[0m]"
            case 4:
                tp="[\033[1;35m填空题\033[0m]"

        if item['type'] == 2:
            correct_contents = [item[chr(96 + ans)] for ans in item['answer']]
        elif item['type'] in [1,3]:
            correct_contents = [item[chr(96 + item['answer'])]]
        if item['type'] in [1,2]:
            options = f"{tp}A:{item['a']}\nB:{item['b']}\nC:{item['c']}\nD:{item['d']}\n"
            if 'e' in item:
                options += f"E:{item['e']}\n"
        elif item['type'] == 3:
            options = "A:对\nB:错\n"
        else:
            options=""
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system",
                     "content": f"你是{self.subject_name}科目备考导师，当用户给出相关题目时，务必解释该题目每个选项的对错、并给出解题思路，不要使用Markdown格式输出。"},
                    {"role": "user", "content": f"题目：{item['title']}\n{options}答案：{correct_contents}"},
                ],
                stream=False,
                reasoning_effort="high"
            )
        except KeyboardInterrupt:
            return
        os.system('cls')
        print(tp,end='')
        self.printf(item['index']-1)
        print(f"\n\nAI解析:{response.choices[0].message.content}")
        os.system('pause')


    def single(self, index):
        print("按Esc退出")
        ans = None
        with keyboard.Events() as events:
            for event in events:
                if event.key == keyboard.Key.esc:
                    raise KeyboardInterrupt
                elif isinstance(event, keyboard.Events.Press):
                    if event.key not in keyboard.Key:
                        ans = event.key
                        break

        ans = format(ans)
        if ans == "'a'" or ans == '<97>':
            ans = 'A'
        elif ans == "'b'" or ans == '<98>':
            ans = 'B'
        elif ans == "'c'" or ans == '<99>':
            ans = 'C'
        elif ans == "'d'" or ans == '<100>':
            ans = 'D'
        elif ans == "'e" or ans == '<101>':
            ans = 'E'
        par = self.judge(ans)
        if par != self.db[index]['answer']:
            self.false_handler(index)
            self.sg += 1
        else:
            self.point += self.score_val[0] if self.db[index]['type']==1 else self.score_val[2] # 得分添加json定义的单选/判断分值
            print("\033[1;32m正确\033[0m")
            self.save(1, index)
        while msvcrt.kbhit():
            msvcrt.getch()

    def multiple(self, index):
        while msvcrt.kbhit():
            msvcrt.getch()
        ans = input("请输入选项:")
        ans = ans.upper()
        if len(ans) != len(self.db[index]['answer']):
            self.false_handler(index)
            self.mt += 1
            return
        flag = 0
        for i in ans:
            par = self.judge(i)
            if par not in self.db[index]['answer']:
                self.false_handler(index)
                self.mt += 1
                flag = 1
                break
        if flag != 1:
            self.point += self.score_val[1] # 得分添加json定义的多选分值
            print("\033[1;32m正确\033[0m")
            self.save(1, index)

    @staticmethod
    def answer_convert(i, word):
        match i:
            case 1:
                word.append('A')
            case 2:
                word.append('B')
            case 3:
                word.append('C')
            case 4:
                word.append('D')
            case 5:
                word.append('E')
        return word

    def false_handler(self, index,skip:bool=False):
        word = []
        if self.db[index]['type'] == 2:
            for i in self.db[index]['answer']:
                self.answer_convert(i, word)
        if self.db[index]['type'] == 4:
            word = self.db[index]['answer']
        else:
            self.answer_convert(self.db[index]['answer'], word)
        print(f"\033[1;31m答案{word}\033[0m")
        self.save(0, index)
        if skip:
            print("按Esc以退出")
            with keyboard.Events() as events:
                for event in events:
                    if event.key == keyboard.Key.esc:
                        raise KeyboardInterrupt
                    elif isinstance(event, keyboard.Events.Press):
                        break
        else:
            print("按1查看AI解析\n按Esc键退出\n按其他键开始下一道")
            ans = None
            with keyboard.Events() as events:
                for event in events:
                    if event.key == keyboard.Key.esc:
                        raise KeyboardInterrupt
                    elif isinstance(event, keyboard.Events.Press):
                        if event.key not in keyboard.Key:
                            ans = event.key
                            break

            ans = format(ans)
            if ans == "'1'" or ans == '<97>':
                self.query(self.db[index])
        os.system('cls') if os.name == 'nt' else os.system('clear')

    def rand_gen(self):
        """ 从全部没做过的试题集内选每种类型题的一半 """
        sg = []  # 单选题集合
        mt = []  # 多选题集合
        sl = []  # 判断题集合
        fb = []  # 填空题集合
        for i in self.test_count:
            print(i)

        for item in self.db:
            if item['index'] - 1 not in self.data['done']:
                match item['type']:
                    case 1:
                        sg.append(int(item['index'])-1)
                    case 2:
                        mt.append(int(item['index'])-1)
                    case 3:
                        sl.append(int(item['index'])-1)
                    case 4:
                        fb.append(int(item['index'])-1)
        if len(sg)>0:
            random.shuffle(sg)
            self.rand_list+=sg[0:int(self.test_count[0])]
        if len(mt)>0:
            random.shuffle(mt)
            self.rand_list += mt[0:int(self.test_count[1])]
        if len(sl)>0:
            random.shuffle(sl)
            self.rand_list += sl[0:int(self.test_count[2])]
        if len(fb)>0:
            random.shuffle(fb)
            self.rand_list += fb[0:int(self.test_count[3])]
        print("题目已生成")
        self.do(test=True)

    def wrong_sequence(self):
        wrong_data = self.data['wrong']
        for data in wrong_data:
            self.rand_list.append(int(data) - 1)
        self.do()

    @staticmethod
    def judge(ans):
        if ans == 'A' or ans == '1':
            par = 1
            print("\033[1;33m您的选择：A\033[0m")
        elif ans == 'B' or ans == '2':
            par = 2
            print("\033[1;33m您的选择：B\033[0m")
        elif ans == 'C' or ans == '3':
            par = 3
            print("\033[1;33m您的选择：C\033[0m")
        elif ans == 'D' or ans == '4':
            par = 4
            print("\033[1;33m您的选择：D\033[0m")
        else:
            par = 0
            print("\033[1;31m您的选择：[无效]\033[0m")
        return par

    def do(self,test=False,skip=False):
        j = 0
        self.start_time = dt.now()
        try:
            for index in self.rand_list:
                j += 1
                print(f"{j}/{len(self.rand_list)}   序号：{self.db[index]['index']}  章节：{self.db[index]['chapter']}")
                match self.db[index]['type']:
                    case 1:
                        print("[单选题]", end='')
                    case 2:
                        print("[\033[1;6;33m多选题\033[0m]", end='')
                    case 3:
                        print("[\033[1;34m判断题\033[0m]", end='')
                    case 4:
                        print("[\033[1;35m填空题\033[0m]", end='')
                self.printf(index)
                if skip:
                    self.false_handler(index,skip)
                    continue
                if self.db[index]['type'] in [1, 3]:
                    self.single(index)
                elif self.db[index]['type'] == 2:
                    self.multiple(index)
                else:
                    self.fill_blank(index)
                os.system('cls') if os.name == 'nt' else os.system('clear')
        except KeyboardInterrupt:
            return j - 2
        finally:
            self.result(test)
        return -10

    def fill_blank(self,index):
        while msvcrt.kbhit():
            msvcrt.getch()
        ans = input("请输入答案，多个空用空格隔开：")
        if ans in self.db[index]['answer']:
            self.point += self.score_val[3] # 得分添加json定义的填空分值
            print("\033[1;32m正确\033[0m")
            self.save(1, index)
        else:
            self.false_handler(index)
            self.other += 1

    def result(self, test_mode = False):
        end_time = dt.now()
        diff = end_time - self.start_time
        if test_mode:
            ok = 0
            for i in range(len(self.test_count)):
                ok+=self.test_count[i]*self.score_val[i]
            if self.point < ok * 0.9:
                print("\033[1;31m很遗憾，考试不合格\033[0m")
            else:
                print("\033[1;32m恭喜您，考试合格\033[0m")
        print(
            f"您的最终得分：{self.point},其中错{self.sg}道单选，{self.mt}道多选，{self.other}道填空，用时{int(diff.seconds / 60):02}分{diff.seconds % 60:02}秒")
        os.system('pause')

    def clear(self):
        self.data['done'].clear()
        with open(f"index{self.type}.json", 'w') as f:
            json.dump(self.data, f)
            f.close()
        print("已清除")


if __name__ == "__main__":
    try:
        root = Database()
        root.selector()
        print("1.顺序刷题")
        print("2.乱序刷题")
        print("3.错题集")
        print("4.模拟考试")
        print("5.背题模式")
        print("6.清除数据")
        a = input()
        match a:
            case '1':
                root.sequence(shuffle=False,skip=False)
            case '2':
                root.sequence(shuffle=True,skip=False)
            case '3':
                root.wrong_sequence()
            case '4':
                root.rand_gen()
            case '5':
                root.sequence(shuffle=False,skip=True)
            case '6':
                root.clear()
            case _:
                sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(1)