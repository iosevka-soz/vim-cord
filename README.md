# Vim-Cord

Quick and simple, single file Discord RPC integration for Neovim.

# Installation

[Pathogen](https://github.com/tpope/vim-pathogen)

`git clone https://github.com/iosevka-soz/vim-cord` into your installation's Bundle directory.

[Vim-Plug](https://github.com/junegunn/vim-plug)

Add:
    `Plug 'iosevka-soz/vim-nasm'`  And install all dependencies manuall

Or:
    `Plug 'iosevka-soz/vim-nasm', { 'do' : 'pip3 install --user pypresence pynvim nest-asyncio' }` To auto install all dependencies

**IMPORTANT**  After installing, you MUST run `:UpdateRemotePlugins`

## Dependencies

- Neovim compiled with Python support
- Python module pynvim:
    `pip3 install --user pynvim`
- Python module pypresence:
    `pip3 install --user pypresence`
- Python module nest-asyncio
    `pip3 install --user nest-asyncio`

## Usage

It should work out of the box with the default values without any configuration needed.

## Configuration and Customization

```vimscript
g:loaded_vim_cord
```
Set it to anything to disable vim-cord.

Vim-Cord will try to detect which editor you are using from your Vim environment,
you can override that by setting

```vimscript
g:vim_cord_editor_override
```
Possible values are:
- vi
- vim
- neovim
- gvim
- macvim

This is the app that will show on discord, for example if you select Vi, your RPC will be `"Playing Vi"`



```vimscript
g:vim_cord_app_id_override
```

Will set a catchall discord application ID for Vim-Cord to use, this supersedes `g:vim_cord_editor_override`



```vimscript
g:vim_cord_<EDITOR_NAME>_app_id 
```

This can be used to give a custom discord app id to each of the built-in supported editors, for example:



`let g:vim_cord_vim_app_id = 836288358629062416` will make Vim-cord use "836288358629062416" as the discord app ID

if it determines vim is the editor in use either by override or by detecting the environment.



```vimscript
g:vim_cord_update_delay
```

This is the delay in **seconds** between each automatic update, 
Vim-Cord will update when moving buffers buffers but also periodically.
Set it to -1 to disable periodic updating.



```vimscript
g:vim_cord_disable_image (Default: 0)
```

Set it to 1 if you don't want the images in your RPC, this means there will only be text info.



```vimscript
g:vim_cord_disable_small_image (Default: 0)
```

Set it to 1 if you wan't to disable only the small image in your RPC, which usually shows the editor icon
The large image with the language icon will sill show.



```vimscript
g:vim_cord_contract_bytes (Default: 1)
```

Set it to 0 if you don't want SI units to be used to show the filesize,
With contract_bytes enabled it would show: `8kiB` / `8kB`
And with contract_bytes disabled, it would show `8000B`



```vimscript
g:vim_cord_bytes_1000 (Default: 0)
```

Set whether to use 1000 or 1024 for the byte contraction, 
if set to 1 RPC will show kilobytes (kB), megabytes (MB), etc...
Otherwise if set to 0, kibibytes (kiB), mebibytes (MiB), etc... will be shown.



```vimscript
g:vim_cord_alert_on_fail (Default: 1)
```

If set to 1, Vim-Cord will display an error message if it fails to connect to discord (If discord is not open for example)
set to 0 to fail silently.



```vimscript
g:vim_cord_alert_on_success (Default: 1)
```

If set to 1, Vim-Cord will inform you when it connects, set to 0 to connect silently.

```vimscript
g:vim_cord_large_image_custom = { dict }
```

Use this to setup custom text on the large image for each filetype.
The keys should be the filtype as vim sees it and the values should be the custom text.
**WARNING: Values must be 2 characters or more.**


```vimscript
g:vim_cord_large_image_custom = { dict }
```

Set this to override the editor name showing up on the small image on discord.
**WARNING: Values must be 2 characters or more.**


```vimscript
g:vim_cord_timer_tracking_type (Default: 'buffer_remember')
```

This setting determines how Vim-Cord will display the timer on your RPC:

- `'session'` Means it'll keep a single timer for the whole vim session, e.g how long vim has been open for, moving buffers won't reset it.

- `'buffer'` Means Vim-Cord will reset the timer every time you move buffers, e.g how long you have been editing a buffer for.

- `'buffer_remember'` Works like `'buffer'` but Vim-Cord will remember how long a buffer was open when you left it if you come back to it.



## Commands
`:VimCordReconnect` Use it to force a reconnection retry at anytime, configuration is parsed again,
respects hard disable by setting `g:vim_cord_loaded`

`VimCordDisconnect` Will disconnect the RPC and disable the plugin, you can reconnect with `:VimCordReconnect`

## Troubleshooting

- No rpc!
Check that you have all the modules listed in [Dependencies](https://github.com/iosevka-soz/vim-nasm#dependencies).

Run `:UpdateRemotePlugins` if you're on Neovim 

Make sure you have Game Activity enabled on discord.

Make sure you are running Neovim with the same account you installed it. It will not work if you run neovim to edit a file as root only having it installed on user account for example.

## TODO

- Add screenshots to README.md

- Add support for Netrw, Nerdtree, help buffers, scratch buffers etc...

- Add more customization on the info displayed as text

- Disable plugin on "project"/"file"

- Connection timeout on nvim launch

- Connection retry on nvim launch
