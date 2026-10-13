# Commit 信息格式

本项目参考 [Conventional Commits](https://www.conventionalcommits.org/)，commit 信息统一用**英文**写。

## 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

只有第一行（标题）是必须的，`body` 和 `footer` 按需添加，三部分之间各空一行。

## 1. 标题行

```
feat(skills): add load_skill tool for progressive disclosure
```

| 部分 | 说明 |
|---|---|
| `type` | 改动类型，见下表 |
| `scope` | 可选，改动的模块：`agent`、`tools`、`skills`、`memory`、`config`、`prompts` |
| `subject` | 一句话说明做了什么 |

### type 取值

| type | 什么时候用 | 例子 |
|---|---|---|
| `feat` | 新功能 | 新增工具、新增 skill、新增记忆功能 |
| `fix` | 修复 bug | 工具参数解析错误 |
| `refactor` | 重构，功能不变 | 拆分文件、改目录结构 |
| `docs` | 只改文档 | README、本文档、注释 |
| `chore` | 杂项 | 依赖、`.gitignore`、配置文件 |
| `test` | 测试相关 | 新增或修改测试 |

### subject 规则

- 用**祈使句、动词原形**开头：`add`、`fix`、`remove`、`move`，不写 `added` 或 `adds`。
- 首字母小写，结尾不加句号。
- 控制在 **50 个字符以内**，写不下说明这个 commit 做的事太多了。

## 2. 正文（body）

说明**为什么改、改了什么**，不用解释代码怎么写（代码里看得到）。

- 每行不超过 72 个字符。
- 多项改动用 `-` 列表。

## 3. 页脚（footer）

可选，用于：

- 不兼容的改动：`BREAKING CHANGE: <说明旧用法怎么迁移>`
- 关联 issue：`Closes #12`

## 原则

1. **一个 commit 只做一件事。** 重构和新功能尽量分开提交，出问题时更容易回退。
2. **提交前看一眼 `git status`。** 不要提交 `.env`、`memory.md` 这类含密钥或个人信息的文件。
3. **标题要让人不看代码也知道改了什么。** 避免 `update`、`fix bug`、`changes` 这种空泛标题。

## 示例

```
fix(tools): stop read_file from escaping the working directory
```

```
feat(skills): add polite-email skill

Emails were sometimes blunt and had inconsistent sign-offs.
The skill enforces a polite structure and the fixed sign-off
"Best, Murray".
```

```
refactor!: split code.py into the mini_agent package

BREAKING CHANGE: `python code.py` no longer works.
Run `mini-agent` or `python -m mini_agent.main` instead.
```

标题里 type 后面加 `!`，表示这是一个不兼容的改动。
