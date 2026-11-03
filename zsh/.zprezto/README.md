# Stripped down Prezto

Forked from https://github.com/sorin-ionescu/prezto

Prezto will work with any recent release of Zsh, but the minimum required
version is **4.3.11**.

Set Zsh as your default shell:

    ```console
    chsh -s /bin/zsh
    ```

### Modules

01. Browse [_`modules`_][9] to see what is available.
02. Load the modules you need in _`${ZDOTDIR:-$HOME}/.zpreztorc`_ and then open
    a new Zsh terminal window or tab.

### Themes

01. For a list of themes, type `prompt -l`.
02. To preview a theme, type `prompt -p name`.
03. Load the theme you like in _`${ZDOTDIR:-$HOME}/.zpreztorc`_ and then
    open a new Zsh terminal window or tab.

    ![sorin theme][2]
    Note that the [_`git`_][11] module may be required for special symbols to
    appear, such as those on the right of the above image. Add `'git'` to the
    `pmodule` list (under `zstyle ':prezto:load' pmodule \` in your
    _`${ZDOTDIR:-$HOME}/.zpreztorc`_) to enable this module.

### External Modules

See `custom-modules/`

01. By default modules will be loaded from [_`/modules`_][9] and _`/contrib`_.
02. Additional module directories can be added to the
    `:prezto:load:pmodule-dirs` setting in _`${ZDOTDIR:-$HOME}/.zpreztorc`_.

    Note that module names need to be unique or they will cause an error when
    loading.

    ```sh
    zstyle ':prezto:load' pmodule-dirs $HOME/.zprezto-contrib
    ```
