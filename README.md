# GitReporter

You can execute `gitreporter` by simply calling

```
gitreporter
```

to get an overview about the options.

The recommended way is to create a configuration file with
```
gitreporter -c CONFIG --create-config
```

where you insert all necessary parameters. Then you can call
```
gitreporter -c CONFIG
```

to analyse a git repository.

> Note: the option `comments-and-coding-standard` is only supported for C-like languages at the moment.
