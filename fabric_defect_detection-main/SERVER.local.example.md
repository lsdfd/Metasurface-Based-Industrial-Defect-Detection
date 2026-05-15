# SERVER.local.md example

这个文件是本地私有模板，不应提交真实密码。

可复制为：

```text
SERVER.local.md
```

并填写仅保存在本机的敏感信息：

```text
host: <HOST>
port: <PORT>
user: <USER>
password: <fill locally only>
remote_root: <REMOTE_PROJECT_ROOT>
```

正式同步时，这类文件应被 `.gitignore` 忽略。
