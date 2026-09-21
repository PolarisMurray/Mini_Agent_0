# Mini_agent：OpenAI Python SDK 项目接口手册

本手册回答的是：**这份程序里的名字从哪里来、去哪个官方页面查、页面里找什么、代码怎样把它们连起来。**

核对范围：项目当前的 [code.py][code]，共 151 行；本地安装的 `openai` 版本为 **3.16.2**。核对日期：2026-09-20（美国东部时间）。后续代码改动可能使行号变化。

正文依据项目代码和本地 SDK 定义逐项解释，并附上已经打开核对的官方文档入口。官网示例负责展示公开用法，本地 SDK 定义补充当前安装版本中的精确来源。文中演示数据均为构造的教学示例，没有运行模型请求。

## 1. 先确定“哪个名字归谁管”

这份程序实际上有四种来源：

| 来源 | 本程序中的例子 | 应该到哪里查 |
|---|---|---|
| OpenAI Python SDK | `OpenAI`、`.chat`、`.completions`、`.create()`、`.choices`、`.tool_calls` | OpenAI 官网接口文档、SDK 类型定义 |
| Python 自带功能 | `os.getenv`、`subprocess.run`、`json.loads`、`list.append`、`input`、`print` | Python 官方文档 |
| 另一个第三方包 | `load_dotenv()` | python-dotenv 文档 |
| 这份程序自己定义的名字 | `client`、`response`、`assistant_message`、`run_bash`、`agent_loop`、`TOOLS` | 当前的 `code.py` |

**`client` 是作者起的变量名；`client` 所指对象提供的 `.chat` 属性，才来自 SDK。**

```python
client = OpenAI(...)
# 左边 client：作者命名。
# 右边 OpenAI：从 openai 包导入的类。
# OpenAI(...)：创建客户端对象，并让 client 指向它。
```

类可以类比“设备的设计类型”，对象是“按该类型创建的具体设备”，变量名是“贴在设备上的标签”。修改标签不会改变设备支持的功能。

还有一层必须分清：本程序使用的是 **OpenAI SDK，但配置的服务器是 DeepSeek**。

```text
code.py
   → OpenAI Python SDK（组织请求、解析响应）
   → https://api.deepseek.com（代码配置的请求目的地）
   → 由 MODEL_ID 指定的模型
```

依据：[code.py 第 14–20 行][code17]。因此，OpenAI 官网用于查 SDK 和请求/响应结构；DeepSeek 是否支持某个模型、参数或特性，应以实际服务端为准。包名不决定请求一定发往 OpenAI。本手册没有读取 `.env` 的内容，也不假定 `MODEL_ID` 的实际值。

## 2. 官网入口：打开哪里、搜索什么

Mac 浏览器可用 **⌘F** 搜索下表中的字符串。页面可能折叠嵌套类型；此时先展开 `Parameters`、`Returns` 或 `View schema details`，再搜索。代码示例应选择 **Python**；函数调用指南如果提供接口切换，应选择 **Chat Completions**。

| 编号 | 已核对的官方入口 | 页面里查找什么 | 对应疑问 |
|---|---|---|---|
| D0 | [OpenAI Python API library][D0] | `Usage`、`api_key`、`base_url`、`Using types` | 客户端怎样初始化？怎样指定服务器？为何返回值有属性？ |
| D1 | [SDKs and CLI][D1] | `pip install openai`、`from openai import OpenAI`、`client = OpenAI()` | 安装哪个包？怎样导入并创建客户端？ |
| D2 | [Create chat completion：Python][D2] | `chat.completions.create`；示例中的 `from openai import OpenAI` | 完整调用链在哪里展示？ |
| D2 | 同上 | `Parameters` → `model`、`messages`、`tools`、`tool_choice` | 本程序传入的四个参数是什么？ |
| D2 | 同上 | `Returns` → `ChatCompletion` → `choices`，展开其结构 | 返回对象里有哪些层级？ |
| D3 | [Chat：Python 类型索引][D3] | `ChatCompletion`、`ChatCompletionMessage`、`ChatCompletionMessageFunctionToolCall` | 返回类型和属性的定义在哪里？ |
| D3 | 同上 | `ChatCompletionToolMessageParam`、`ChatCompletionFunctionToolParam` | 工具结果消息和工具声明需要哪些字段？ |
| D4 | [Function calling][D4] | `Defining functions`、`Handling function calls`、`tool_call_id` | 工具如何声明、执行、回传？ |
| D5 | [Conversation state][D5] | `Chat Completions`、`messages` | 为什么下一轮还要附上已有消息？ |

阅读顺序：**先找完整示例 → 确认调用对象 → 查 Parameters → 沿 Returns 展开返回属性。** 单看参数表，只能知道括号里填什么，不能知道客户端在前面怎样创建。

## 3. 本程序用到的全部 SDK 入口和返回属性

这张表覆盖当前 `code.py` 中实际使用的 SDK 构造入口、资源属性、请求方法和响应属性。参数及字典字段见后面两节。

| 代码中的名字或表达式 | 代码位置 | 属于什么 | 在本程序中做什么 | 官网定位 |
|---|---|---|---|---|
| `OpenAI` | 4、17 行 | SDK 提供的类 | 创建同步客户端 | D1 的 Python 示例 |
| `client.chat` | 90 行 | 客户端的资源属性，得到 `Chat` 对象 | 访问聊天接口资源 | D2 的完整调用示例 |
| `client.chat.completions` | 90 行 | `Chat` 的资源属性，得到 `Completions` 对象 | 访问聊天回复资源 | D2 的完整调用示例 |
| `client.chat.completions.create(...)` | 90–101 行 | 请求方法 | 提交对话和工具声明，得到回复 | D2 顶部方法签名、Parameters、Returns |
| `response.choices` | 103 行 | `ChatCompletion` 的属性；列表 | 取得候选结果列表 | D2 Returns → choices |
| `response.choices[0].message` | 103 行 | `Choice` 的属性；`ChatCompletionMessage` | 取得第一份候选结果中的助手消息 | D2 choices 的嵌套结构；D3 `ChatCompletionMessage` |
| `assistant_message.tool_calls` | 109、114 行 | 消息属性；工具调用列表或 `None` | 判断是否有工具调用并逐个处理 | D3 `ChatCompletionMessage`；D4 Handling function calls |
| `assistant_message.content` | 110 行 | 消息属性；字符串或 `None` | 打印模型的正文 | D3 `ChatCompletionMessage` |
| `tool_call.function` | 116、118 行 | 函数工具调用的属性；嵌套对象 | 取得被请求函数的名称与参数 | D3 `ChatCompletionMessageFunctionToolCall` |
| `tool_call.function.name` | 116 行 | 嵌套对象的字符串属性 | 判断请求的是不是 `"bash"` | D4 Handling function calls |
| `tool_call.function.arguments` | 118 行 | 嵌套对象的字符串属性 | 取得 JSON 编码的参数文本 | D4 Handling function calls |
| `tool_call.id` | 132 行 | 工具调用的字符串属性 | 把执行结果关联回这一次调用 | D4 `tool_call_id` 示例 |

**`[0]` 属于 Python 的列表索引语法；它不是 SDK 函数。** 本程序没有传入 `stream=True`，这里按普通的非流式返回结构读取。

## 4. 从导入到请求：每一步从哪里来

### 4.1 `from openai import OpenAI`

位置：[第 4 行][code4]。

- `openai`：安装的包名。
- `OpenAI`：该包导出的类名，大小写有区别。
- `from ... import ...`：Python 的导入语法。

官网证据：D1 的 Python 示例直接使用这条导入语句。本地证据：[`openai/__init__.py` 第 12 行][sdkexport] 从 `_client` 导出 `OpenAI`。

当前环境已经安装 `openai`。但项目的 [requirements.txt][requirements] 目前只列出 `anthropic` 和 `python-dotenv`，没有列出 `openai`。这解释了“当前环境可以有这个包，但仅按依赖文件重新安装不一定有”的差异。本次仅记录该情况，没有修改依赖或程序。

### 4.2 `OpenAI(api_key=API_KEY, base_url=...)`

位置：[第 17 行][code17]。

```python
client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com",
)
```

| 部分 | 谁规定的 | 解释 |
|---|---|---|
| `client` | 程序作者 | 保存客户端对象的变量，可以改名 |
| `api_key` | SDK | 构造器参数，接收访问服务所需的密钥 |
| `API_KEY` | 程序作者 | 第 14 行读取环境变量后保存的值 |
| `base_url` | SDK | 构造器参数，决定请求所用的基础地址 |
| `"https://api.deepseek.com"` | 程序配置 | 本项目指定的基础地址 |

`api_key=API_KEY` 左边是参数名，右边是表达式的值；两者无需同名。

构造客户端本身不会生成模型回复。程序到第 90 行调用 `.create(...)` 时，才执行这里讨论的模型请求。

官网入口：**D0 搜索 `api_key` 可找到初始化示例；搜索 `base_url` 可找到指定自定义服务器地址的客户端示例。** D1 也展示基本客户端创建。D0 是 SDK 使用说明，D2 是某一个远程接口的参考页，两个页面承担不同职责。本地完整构造参数：[`OpenAI.__init__` 第 162 行][sdkinit]。

### 4.3 `.chat.completions.create(...)` 不是一整块魔法名字

位置：[第 90 行][code90]。

```text
client                         作者命名的变量，指向 OpenAI 对象
  └─ .chat                     SDK 属性，取得 Chat 对象
       └─ .completions        SDK 属性，取得 Completions 对象
            └─ .create(...)   SDK 方法，发起请求
```

本地来源也可以一路追下去：

1. [`OpenAI.chat` 第 368 行][sdkchat] 返回 `Chat(self)`。
2. [`Chat.completions` 第 21 行][sdkcompletions] 返回 `Completions(self._client)`。
3. [`Completions.create` 的非流式签名第 252 行][sdkcreate] 声明输入和 `ChatCompletion` 返回类型；[实现第 1309 行][sdkrequest] 使用 `/chat/completions` 请求路径。

这就是“哪里来的属性”的完整追踪链。源码里属性可能用带装饰器的 `def` 实现，但使用者仍按 `.chat`、`.completions` 访问，无需写成 `.chat()`。

### 4.4 本程序的四个请求参数

```python
response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": SYSTEM},
        *messages,
    ],
    tools=TOOLS,
    tool_choice="auto",
)
```

| 参数名 | 本程序传的值 | 本程序中的作用 | 官网查找词 |
|---|---|---|---|
| `model` | `MODEL` | 指定模型；该变量由第 15 行读取 `MODEL_ID` 得到 | D2 `model` |
| `messages` | 一个新建的列表 | 系统说明在前，已有对话在后 | D2 `messages` |
| `tools` | `TOOLS` | 向模型描述程序允许请求的工具 | D2 `tools`；D4 Defining functions |
| `tool_choice` | `"auto"` | 允许模型自行选择回复或请求工具 | D2 `tool_choice` |

这里的 `*messages` 是列表展开：把旧列表中的每条消息依次放进新列表。它不会把旧列表本身作为一个嵌套元素放进去，也不是乘法。

例如旧列表是 `[用户消息, 助手消息]`，新请求里就是 `[系统说明, 用户消息, 助手消息]`。本程序每次请求临时在前面附加系统说明，而没有把它反复追加到历史列表。

消息字典里的 `role` 和 `content` 也是接口规定的字段。当前程序中，`system` 承载 SYSTEM，`user` 承载 query，模型返回的消息角色为 `assistant`，命令执行结果使用 `tool`。这里描述当前代码使用的角色，具体模型对角色的支持由服务端决定。

## 5. `TOOLS` 里面的字段：哪些固定，哪些自定义

位置：[第 41 行][code41]。`TOOLS` 是本程序的变量名。里面的结构则需要遵守函数工具的格式。

```python
TOOLS = [{
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Run a shell command in the current working directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute.",
                }
            },
            "required": ["command"],
        },
    },
}]
```

| 字段或值 | 来源 | 本程序里的含义 |
|---|---|---|
| 外层 `"type": "function"` | 工具接口格式 | 声明这是函数工具 |
| `"function"` | 工具接口字段 | 放该工具的说明 |
| `"name"` | 工具接口字段 | 工具叫什么 |
| `"bash"` | 作者自定义的工具名 | 模型要请求这个工具时使用的名称 |
| `"description"` | 接口/Schema 描述字段 | 给模型看的用途说明 |
| `"parameters"` | 工具接口字段 | 描述该工具接收什么参数 |
| `"type": "object"` | JSON Schema | 参数整体应是一个 JSON 对象 |
| `"properties"` | JSON Schema | 列出对象中每个参数的定义 |
| `"command"` | 作者自定义的参数名 | 这里表示要执行的命令；第 123 行按这个键取值 |
| `"type": "string"` | JSON Schema | `command` 的值应是字符串 |
| `"required": ["command"]` | JSON Schema | 声明 `command` 为必需参数 |

JSON Schema 可以理解为“表格的填写规则”。`parameters` 描述规则；模型稍后返回的 `arguments` 是按规则填写的一份具体数据。两者不是同一件东西。

**写出 `"name": "bash"` 不会自动创建 Python 函数，也不会让 SDK 自动执行命令。** 本程序第 116 行识别这个名字，第 127 行才转交给自定义 `run_bash`。`bash` 和 `run_bash` 名字不同仍能工作，因为连接它们的是这段程序逻辑。

官网：D4 的函数声明和参数 Schema 说明；D3 的 `ChatCompletionFunctionToolParam`。本地定义：[`chat_completion_function_tool_param.py`][sdktoolparam]、[`FunctionDefinition`][sdkfunctiondef]。

## 6. 模型返回后：每个 attribute 从哪里来

### 6.1 `response.choices[0].message`

位置：[第 103 行][code103]。

```text
response                       ChatCompletion 对象
  └─ choices                   Choice 对象的列表
       └─ [0]                  第一份候选结果
            └─ message         ChatCompletionMessage 对象
                 ├─ content    回复正文；可能为 None
                 └─ tool_calls 工具调用列表；可能为 None
```

`response`、`assistant_message` 都是作者给对象起的名字。`choices`、`message`、`content`、`tool_calls` 是 SDK 定义的属性。

第一份候选结果不等于第一句话，也不等于第一轮历史消息。这里的“候选”是同一次请求返回的候选回复。

官网：D2 Returns；D3 `ChatCompletion` 和 `ChatCompletionMessage`。本地精确定义：[`choices`][sdkchoices]、[`Choice.message`][sdkmessagefield]、[`content` 与 `tool_calls`][sdkmessage]。

### 6.2 `if not assistant_message.tool_calls`

位置：[第 109 行][code109]。

这句检查工具调用列表是否为空或为 `None`。没有工具调用时，程序打印 `.content` 并退出 `agent_loop`；有工具调用时，程序继续执行下面的循环。

这是**本程序写出的控制逻辑**。没有工具调用，并不从逻辑上证明用户任务一定成功；只是该程序把它作为结束条件。

### 6.3 `.function.name`、`.function.arguments` 和 `.id`

位置：[第 114 行起][code114]。以下是便于阅读的模拟结构，不是真实请求结果：

```text
tool_call
  ├─ id = "call_demo_001"
  ├─ type = "function"
  └─ function
       ├─ name = "bash"
       └─ arguments = '{"command": "pwd"}'
```

这里 `function` 是保存调用信息的对象，不是直接可执行的 Python 函数。`name` 是请求的工具名；`arguments` 是 JSON 字符串；`id` 标记这一次具体调用。

假设连续请求两次 `bash`，名称可以相同，但它们是两次不同调用，需要各自的调用 ID。名称像“工种”，ID 像“这张工单的编号”。

官网：D4 Handling function calls。本地：[`ChatCompletionMessageFunctionToolCall` 及嵌套 `Function`][sdkfunctioncall]。

本项目只声明了函数工具，所以按 `.function` 读取。当前 SDK 也有其他工具调用类型；若以后增加 custom tool，不能假定每种工具调用都具有 `.function`。

### 6.4 `arguments` 为什么还要经过 `json.loads`

```python
command = tool_call.function.arguments
arguments = json.loads(command)
bash_command = arguments["command"]
```

三步分别得到：

| 变量 | 示例值 | Python 类型 |
|---|---|---|
| `command` | `'{"command": "pwd"}'` | `str`，一段 JSON 文本 |
| `arguments` | `{"command": "pwd"}` | `dict`，可按键读取的字典 |
| `bash_command` | `"pwd"` | `str`，真正交给执行器的命令 |

第 118 行的变量名 `command` 容易造成误解：它此时保存整段参数 JSON，尚不是命令本身。`json.loads` 的作用是解析文本，**不会执行其中的 shell 命令**。

`tool_call.function.arguments` 是属性访问；`arguments["command"]` 是字典取值。虽然两者都在“取数据”，对象形式不同，写法也不同。

Python 官方：[json.loads][Pjson]。SDK 本地类型明确将 `.arguments` 声明为 `str`。本程序没有捕获 JSON 解析异常，也没有在解析后检查字段类型；Schema 声明本身不等同于本地执行了校验。

## 7. 工具执行结果如何回到模型

位置：[第 129 行][code129]。

```python
messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": output,
})
```

| 部分 | 来源 | 作用 |
|---|---|---|
| `messages` | 当前函数收到的 Python 列表 | 保存对话历史 |
| `.append(...)` | Python 列表方法 | 在列表末尾追加一项 |
| `"role": "tool"` | 消息接口格式 | 标记这是工具结果 |
| `"tool_call_id"` | 消息接口字段 | 指明结果对应哪一次工具调用 |
| `tool_call.id` | SDK 返回属性 | 提供那个调用 ID |
| `"content"` | 消息接口字段 | 承载工具结果内容 |
| `output` | 程序变量 | 接收 `run_bash` 返回的文本 |

**`.append` 只修改内存中的列表，不会向服务器发送消息。** 下一次 `while` 循环再次执行 `.create(...)`，新历史才随请求发送。

第 105 行还先追加了 `assistant_message`：它记录模型发出的工具请求。随后追加工具结果，两者一起形成完整上下文。SDK 可以把返回的消息模型对象序列化后用于后续请求；官方 D4 的 Chat Completions 示例也使用这种追加方式。

官网：D4 的执行与回传示例；D5 的历史管理。工具结果字段的本地定义：[`ChatCompletionToolMessageParam`][sdktoolmessage]。

完整流程可写成：

```text
用户消息
  → create：模型生成消息
  → 追加助手消息
  → 有 tool_calls？
       有：解析参数 → run_bash → 追加 tool 消息 → 再次 create
       无：打印 content → return
```

若用 H 表示历史、A 表示助手消息、T 表示工具结果，一轮工具交互相当于：`H下一轮 = H当前 + [A, T]`；多个工具调用就追加多个 T。代码中 `+` 的意义是消息序列拼接，不是数字相加。

## 8. 其余函数和属性的来源：在 OpenAI 官网查不到的部分

这些名字也都出现在当前程序中，但不是 OpenAI SDK 接口。

| 名字 | 代码行 | 来源 | 作用与对应文档 |
|---|---|---|---|
| `load_dotenv()` | 5、12 | `python-dotenv` 包 | 将 `.env` 配置加载到环境；[项目官方文档][Pdotenv] |
| `os.getenv(...)` | 14、15 | Python 标准库 `os` | 读环境变量；未找到且未指定默认值时返回 `None`；[官方文档][Pos] |
| `subprocess.run(...)` | 67 | Python 标准库 `subprocess` | 执行子进程并等待完成；[官方文档][Psubprocess] |
| `result.stdout` | 75 | `CompletedProcess` 对象属性 | 取得捕获的标准输出；[官方文档][Pstdout] |
| `result.stderr` | 77、78 | `CompletedProcess` 对象属性 | 取得捕获的标准错误流；[官方文档][Pstderr] |
| `json.loads(...)` | 121 | Python 标准库 `json` | 把 JSON 文本解析为 Python 值；[官方文档][Pjson] |
| `messages.append(...)` | 105、129 | Python `list` 方法 | 原地追加元素；[官方文档][Plist] |
| `input(...)` | 142 | Python 内置函数 | 显示提示并读取终端输入；[官方文档][Pinput] |
| `print(...)` | 110、125 | Python 内置函数 | 输出到终端；[官方文档][Pprint] |
| `run_bash(command)` | 定义 66、调用 127 | 作者自定义函数 | 包装命令执行与输出拼接；应读本项目第 66–80 行 |
| `agent_loop(messages)` | 定义 87、调用 151 | 作者自定义函数 | 组织模型与工具之间的循环；应读本项目第 87–135 行 |

`subprocess.run` 的几个参数也不是 SDK 参数：

| 参数 | 当前值 | 效果 |
|---|---|---|
| 第一个位置参数 | `command` | 需要执行的命令 |
| `shell` | `True` | 通过系统 shell 解释命令 |
| `capture_output` | `True` | 捕获 stdout 与 stderr |
| `text` | `True` | 使用文本形式读取输出 |
| `timeout` | `30` | 等待超时阈值，单位为秒；超时会抛出异常 |

虽然函数取名 `run_bash`，这里并没有显式选择 Bash。POSIX 系统中 `shell=True` 默认使用 `/bin/sh`。函数名字不能替代对实际实现的检查。当前代码也没有捕获超时异常。

`result` 与 `response` 尤其容易混淆：前者来自本机命令执行，后者来自模型请求。因此前者读 `.stdout`，后者读 `.choices`。

### 程序自己起的变量名速查

| 名字 | 首次来源 | 保存什么 |
|---|---|---|
| `API_KEY` | 第 14 行 | 环境变量中的密钥值 |
| `MODEL` | 第 15 行 | 环境变量中的模型名称 |
| `client` | 第 17 行 | SDK 客户端对象 |
| `SYSTEM` | 第 27 行 | 系统说明字符串 |
| `TOOLS` | 第 41 行 | 工具声明列表 |
| `command` | 第 66 行参数；第 118 行局部变量 | 在不同函数作用域中分别表示命令字符串、原始参数 JSON |
| `result` | 第 67 行 | 子进程结果对象 |
| `output` | 第 75 行；第 127 行 | 命令输出文本；两个函数中各有自己的局部变量 |
| `messages` | 第 144 行；作为第 87 行函数参数传入 | 对话历史列表 |
| `response` | 第 90 行 | SDK 解析后的模型响应 |
| `assistant_message` | 第 103 行 | 第一份候选回复中的消息 |
| `tool_call` | 第 114 行循环变量 | 当前正在处理的一次工具调用 |
| `arguments` | 第 121 行 | JSON 解析后的参数字典 |
| `bash_command` | 第 123 行 | 从参数字典取出的命令 |
| `query` | 第 142 行 | 用户在终端输入的任务 |

`if`、`for`、`while`、`return`、`def`、`import`、`not`、`*messages` 和 `f"...{变量}..."` 都是 Python 语法，不需要在 SDK 中寻找同名接口。

## 9. 遇到新名字时，怎样独立找到定义

以 `tool_call.function.arguments` 为例：

1. **在当前文件追变量来源。** `tool_call` 来自第 114 行循环；列表来自 `assistant_message.tool_calls`；消息来自第 103 行；响应来自第 90 行。
2. **确认返回对象的类型。** D2 的 Returns 写的是 `ChatCompletion`，然后沿 `choices → message → tool_calls → function → arguments` 查嵌套字段。
3. **看官方示例怎样使用。** D4 搜索 `json.loads`，能找到解析函数参数的上下文。
4. **官网折叠结构仍不清楚时，看本地安装版本。** 本手册下方提供了已核对的定义链接；它能回答“当前环境里的这个名字究竟写在哪里”。

编辑器如果支持 Python 的“转到定义”，可对 `OpenAI` 或 `.create` 使用该操作。需要选择本项目 `.venv` 中的解释器；解析不出类型时，动态补全可能不完整。补全是辅助线索，完整调用示例和返回类型仍是核对依据。

### 参数表中常见类型标注

| 写法 | 阅读方法 |
|---|---|
| `name: Type` | 名为 name 的参数或属性，其类型是 Type |
| `Iterable[T]` | 能逐个取出 T 类型元素的对象；列表通常可以满足 |
| `List[T]` / `list[T]` | 元素为 T 类型的列表 |
| `Union[A, B]` | A 或 B 类型 |
| `Optional[T]` | T 或 `None`；不等同于“函数调用时一定可省略” |
| `Literal["function"]` | 指定的字面值，这里就是字符串 `"function"` |
| `-> ChatCompletion` | 函数返回 ChatCompletion 类型 |
| `ChatCompletionMessageParam` | 可作为输入的消息类型集合；它不是需要照抄的消息内容 |

类型标注可类比“插口规格”，实际值才是“插进去的插头”。调用时写 `model=MODEL` 是传值；文档中写 `model: Union[...]` 是说明接收的值应符合什么类型。

## 10. 最短阅读路线：从程序入口走一遍

| 顺序 | 应读位置 | 这一步产生什么 |
|---|---|---|
| 1 | 4–20 行 | 导入 SDK，读取配置，创建 client |
| 2 | 27–59 行 | 定义规则 SYSTEM 和工具说明 TOOLS |
| 3 | 66–80 行 | 定义真正执行命令的 run_bash |
| 4 | 142–149 行 | 读取 query，建立初始 messages |
| 5 | 151 行 → 87 行 | 进入 agent_loop |
| 6 | 90–103 行 | 请求模型，取出 assistant_message |
| 7 | 105–111 行 | 记录助手消息；没有工具调用则打印并返回 |
| 8 | 114–127 行 | 逐个解析工具调用，执行本地函数 |
| 9 | 129–135 行 | 追加执行结果，再回到第 90 行 |

这份代码直接调用的 SDK 核心入口只有 **`OpenAI(...)` 和 `.chat.completions.create(...)`**。其余看起来突然出现的点号，主要是资源属性和返回对象的嵌套属性；它们的来源已经逐项列在第 3 节。

[code]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/code.py
[code4]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/code.py:4
[code17]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/code.py:17
[code41]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/code.py:41
[code90]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/code.py:90
[code103]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/code.py:103
[code109]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/code.py:109
[code114]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/code.py:114
[code129]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/code.py:129
[requirements]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/requirements.txt
[D0]: https://developers.openai.com/api/reference/python
[D1]: https://developers.openai.com/api/docs/libraries
[D2]: https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/create
[D3]: https://developers.openai.com/api/reference/python/resources/chat
[D4]: https://developers.openai.com/api/docs/guides/function-calling
[D5]: https://developers.openai.com/api/docs/guides/conversation-state
[sdkexport]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/.venv/lib/python3.14/site-packages/openai/__init__.py:12
[sdkinit]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/.venv/lib/python3.14/site-packages/openai/_client.py:162
[sdkchat]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/.venv/lib/python3.14/site-packages/openai/_client.py:368
[sdkcompletions]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/.venv/lib/python3.14/site-packages/openai/resources/chat/chat.py:21
[sdkcreate]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/.venv/lib/python3.14/site-packages/openai/resources/chat/completions/completions.py:252
[sdkrequest]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/.venv/lib/python3.14/site-packages/openai/resources/chat/completions/completions.py:1309
[sdkchoices]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/.venv/lib/python3.14/site-packages/openai/types/chat/chat_completion.py:200
[sdkmessagefield]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/.venv/lib/python3.14/site-packages/openai/types/chat/chat_completion.py:57
[sdkmessage]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/.venv/lib/python3.14/site-packages/openai/types/chat/chat_completion_message.py:57
[sdkfunctioncall]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/.venv/lib/python3.14/site-packages/openai/types/chat/chat_completion_message_function_tool_call.py:10
[sdktoolparam]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/.venv/lib/python3.14/site-packages/openai/types/chat/chat_completion_function_tool_param.py:12
[sdkfunctiondef]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/.venv/lib/python3.14/site-packages/openai/types/shared_params/function_definition.py:10
[sdktoolmessage]: /Users/chenzishu/Documents/Sophomore/ISR/Mini_agent/.venv/lib/python3.14/site-packages/openai/types/chat/chat_completion_tool_message_param.py:13
[Pdotenv]: https://bbc2.github.io/python-dotenv/
[Pos]: https://docs.python.org/3/library/os.html#os.getenv
[Psubprocess]: https://docs.python.org/3/library/subprocess.html#subprocess.run
[Pstdout]: https://docs.python.org/3/library/subprocess.html#subprocess.CompletedProcess.stdout
[Pstderr]: https://docs.python.org/3/library/subprocess.html#subprocess.CompletedProcess.stderr
[Pjson]: https://docs.python.org/3/library/json.html#json.loads
[Plist]: https://docs.python.org/3/tutorial/datastructures.html
[Pinput]: https://docs.python.org/3/library/functions.html#input
[Pprint]: https://docs.python.org/3/library/functions.html#print
